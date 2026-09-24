import cv2
import numpy as np
from .utils import order_points

class YoloScreenDetector:
    def __init__(self, model_name='yolov8s-seg.pt'):
        """
        Baseline algorithm that uses ultralytics YOLO Segmentation model
        to detect the screen/monitor (COCO classes: 62 for tv, 63 for laptop).
        Extracts the rotated bounding box from the precise segmentation mask,
        applying polygon approximation to smooth out mask artifacts.
        """
        from ultralytics import YOLO
        self.model = YOLO(model_name)
        self.classes = [62, 63]
        
    def detect(self, frame):
        """
        Processes a single frame and returns the 4 corners of the detected screen.
        """
        orig_h, orig_w = frame.shape[:2]
        
        # Resize image preserving aspect ratio
        target_size = 640
        scale = target_size / max(orig_h, orig_w)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        resized_frame = cv2.resize(frame, (new_w, new_h))
        
        # Pad image with OpenCV to multiples of 32 (adding bottom and right borders)
        pad_w = (32 - new_w % 32) % 32
        pad_h = (32 - new_h % 32) % 32
        padded_frame = cv2.copyMakeBorder(resized_frame, 0, pad_h, 0, pad_w, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        
        # imgsz expects (height, width)
        imgsz = (new_h + pad_h, new_w + pad_w)
        
        results = self.model.predict(
            padded_frame, 
            classes=self.classes, 
            verbose=False,
            imgsz=imgsz,
            retina_masks=True,
            conf=0.05
        )
        
        if len(results) == 0 or len(results[0].boxes) == 0:
            return None
            
        boxes = results[0].boxes
        
        best_idx = -1
        max_area = -1
        
        # Pick the detection with the largest bounding box area
        for i, box in enumerate(boxes):
            xmin, ymin, xmax, ymax = map(float, box.xyxy[0].tolist())
            area = (xmax - xmin) * (ymax - ymin)
            if area > max_area:
                max_area = area
                best_idx = i
                
        # If the model didn't return masks, fallback to the bounding box
        if results[0].masks is None or len(results[0].masks) == 0:
            box = boxes[best_idx]
            xmin, ymin, xmax, ymax = map(float, box.xyxy[0].tolist())
            rect = np.array([
                [xmin, ymin],
                [xmax, ymin],
                [xmax, ymax],
                [xmin, ymax]
            ], dtype=np.float32)
            # Revert scaling to map back to original coordinates
            rect = rect / scale
            return order_points(rect).tolist()
            
        # Get the mask polygon of the best detection
        best_mask = results[0].masks.xy[best_idx]
        
        if len(best_mask) < 3:
            return None
            
        # The mask might have stairstepping artifacts (perfectly vertical/horizontal tiny edges)
        # minAreaRect is an 'outer' bounding box, so it gets inflated by any tiny outlier pixel.
        # Instead, we iteratively increase epsilon in approxPolyDP to find the best 4-point polygon!
        mask_contour = np.array(best_mask, dtype=np.float32)
        peri = cv2.arcLength(mask_contour, True)
        
        # Search for a 4-point polygon (the screen corners)
        for eps_multiplier in np.linspace(0.01, 0.1, 50):
            epsilon = eps_multiplier * peri
            approx = cv2.approxPolyDP(mask_contour, epsilon, True)
            
            if len(approx) == 4:
                pts = approx.reshape(4, 2)
                # Revert scaling
                pts = pts / scale
                return order_points(pts).tolist()
                
        # Fallback if we couldn't find exactly 4 points:
        # Use a fixed epsilon and then minAreaRect
        epsilon = 0.02 * peri
        approx = cv2.approxPolyDP(mask_contour, epsilon, True)
        rect_contour = cv2.minAreaRect(approx)
        pts = cv2.boxPoints(rect_contour)
        
        # Revert scaling
        pts = np.array(pts, dtype=np.float32) / scale
        return order_points(pts).tolist()
