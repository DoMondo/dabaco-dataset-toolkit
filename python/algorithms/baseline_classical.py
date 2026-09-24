import cv2
import numpy as np
from .utils import order_points

class ClassicalScreenDetector:
    def __init__(self):
        """
        Baseline algorithm using classical computer vision to detect the 4 corners
        of a screen or monitor.
        """
        pass
        
    def _evaluate_quad(self, pts, frame_w, frame_h, is_hull_approx=True):
        """
        Evaluates a candidate 4-point polygon and returns (is_valid, score).
        """
        pts = pts.astype("float32")
        ordered = order_points(pts)
        (tl, tr, br, bl) = ordered
        
        # Segment vectors
        v_top = tr - tl
        v_bot = br - bl
        v_left = bl - tl
        v_right = br - tr
        
        w_top = np.linalg.norm(v_top)
        w_bot = np.linalg.norm(v_bot)
        h_left = np.linalg.norm(v_left)
        h_right = np.linalg.norm(v_right)
        
        avg_w = (w_top + w_bot) / 2.0
        avg_h = (h_left + h_right) / 2.0
        
        if avg_w < 30 or avg_h < 30:
            return False, 0
            
        area = cv2.contourArea(ordered.astype(np.int32))
        frame_area = float(frame_w * frame_h)
        area_ratio = area / frame_area
        
        # Screen should occupy a realistic fraction of the frame (5% to 92%)
        if area_ratio < 0.05 or area_ratio > 0.92:
            return False, 0
            
        # Parallelism check: opposite sides
        w_ratio = min(w_top, w_bot) / max(w_top, w_bot)
        h_ratio = min(h_left, h_right) / max(h_left, h_right)
        if w_ratio < 0.65 or h_ratio < 0.65:
            return False, 0
            
        # Aspect ratio check
        aspect_ratio = avg_w / avg_h
        if aspect_ratio < 0.6 or aspect_ratio > 2.6:
            return False, 0
            
        # Check angle orthogonality using dot products
        cos_top_left = abs(np.dot(v_top, v_left) / (w_top * h_left + 1e-6))
        cos_top_right = abs(np.dot(v_top, v_right) / (w_top * h_right + 1e-6))
        cos_bot_left = abs(np.dot(v_bot, v_left) / (w_bot * h_left + 1e-6))
        cos_bot_right = abs(np.dot(v_bot, v_right) / (w_bot * h_right + 1e-6))
        
        max_cos = max(cos_top_left, cos_top_right, cos_bot_left, cos_bot_right)
        # Cosine of near-90-degree angle is near 0. Reject if angle deviates significantly (> 35 deg)
        if max_cos > 0.58:  # cos(55 deg) ~ 0.57
            return False, 0
            
        ortho_score = 1.0 - max_cos
        
        # Natural screen aspect ratios (16:9 ~ 1.77, 16:10 ~ 1.6, 4:3 ~ 1.33)
        aspect_dev = min(abs(aspect_ratio - 1.77), abs(aspect_ratio - 1.6), abs(aspect_ratio - 1.33))
        aspect_score = max(0.2, 1.0 - (aspect_dev / 1.5))
        
        # Exact polygon approximations get a higher bonus than minAreaRect fallbacks
        poly_bonus = 1.5 if is_hull_approx else 0.8
        
        score = area * (w_ratio * h_ratio) * ortho_score * aspect_score * poly_bonus
        return True, score

    def detect(self, frame):
        """
        Processes a single frame and returns the 4 corners of the detected screen.
        Returns:
            corners: list of 4 (x,y) tuples, or None if not found.
        """
        h, w = frame.shape[:2]
        frame_area = float(h * w)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Bilateral filter to smooth texture while keeping sharp bezel boundaries
        blurred = cv2.bilateralFilter(gray, 7, 45, 45)
        
        median_val = np.median(blurred)
        
        # Multiple binary representations to capture both high-contrast bezels and lit panels
        binary_maps = []
        
        # 1. Multi-scale Canny edges
        for low_factor, high_factor in [(0.4, 1.1), (0.66, 1.33), (0.8, 1.6)]:
            c_low = int(max(10, low_factor * median_val))
            c_high = int(min(250, high_factor * median_val))
            e = cv2.Canny(blurred, c_low, c_high)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            binary_maps.append(cv2.morphologyEx(e, cv2.MORPH_CLOSE, kernel, iterations=2))
            
        # 2. Adaptive Thresholding
        thresh1 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 3)
        thresh2 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 5)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        binary_maps.append(cv2.morphologyEx(thresh1, cv2.MORPH_CLOSE, kernel, iterations=2))
        binary_maps.append(cv2.morphologyEx(thresh2, cv2.MORPH_CLOSE, kernel, iterations=2))
        
        candidates = []
        
        for bin_map in binary_maps:
            contours, _ = cv2.findContours(bin_map, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # Select large contours
            large_contours = [c for c in contours if cv2.contourArea(c) > 0.04 * frame_area]
            large_contours = sorted(large_contours, key=cv2.contourArea, reverse=True)[:10]
            
            for c in large_contours:
                hull = cv2.convexHull(c)
                peri = cv2.arcLength(hull, True)
                
                # Try multi-epsilon polygon approximations
                found_approx = False
                for eps in [0.015, 0.02, 0.025, 0.03, 0.04, 0.05]:
                    approx = cv2.approxPolyDP(hull, eps * peri, True)
                    if len(approx) == 4 and cv2.isContourConvex(approx):
                        pts = approx.reshape(4, 2)
                        is_valid, score = self._evaluate_quad(pts, w, h, is_hull_approx=True)
                        if is_valid:
                            candidates.append((score, pts))
                            found_approx = True
                            break
                            
                # Fallback to rotated bounding box if no clean 4-point polygon was found
                if not found_approx:
                    rect = cv2.minAreaRect(hull)
                    box = cv2.boxPoints(rect)
                    is_valid, score = self._evaluate_quad(box, w, h, is_hull_approx=False)
                    if is_valid:
                        candidates.append((score, box))
                        
        if candidates:
            # Sort by highest score
            candidates = sorted(candidates, key=lambda x: x[0], reverse=True)
            best_pts = candidates[0][1]
            ordered = order_points(best_pts)
            return ordered.tolist()
            
        return None
