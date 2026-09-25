import numpy as np
import cv2

class DabacoMetrics:
    def __init__(self, image_width=1280, image_height=960):
        """
        Initializes the metrics calculator.
        Args:
            image_width (int): Used for IoU mask generation if needed.
            image_height (int): Used for IoU mask generation if needed.
        """
        self.image_width = image_width
        self.image_height = image_height

    def compute_detection_rate(self, ground_truth, predictions):
        """
        Computes the detection rate: the percentage of frames where 
        the algorithm successfully produced a prediction.
        """
        valid_gt_count = sum(1 for gt in ground_truth if gt is not None and len(gt) == 4)
        if valid_gt_count == 0:
            return 0.0
            
        detected_frames = sum(1 for gt, pred in zip(ground_truth, predictions) 
                              if gt is not None and len(gt) == 4 and pred is not None and len(pred) == 4)
        return detected_frames / valid_gt_count

    def _get_corner_errors(self, ground_truth, predictions):
        errors = []
        for gt, pred in zip(ground_truth, predictions):
            if gt is None or len(gt) != 4:
                continue
            if pred is None or len(pred) != 4:
                continue
                
            gt_pts = np.array(gt, dtype=np.float32)
            pred_pts = np.array(pred, dtype=np.float32)
            
            best_dist = float('inf')
            for reverse in (False, True):
                pts = pred_pts[::-1] if reverse else pred_pts
                for shift in range(4):
                    shifted_pts = np.roll(pts, shift, axis=0)
                    dists = np.linalg.norm(gt_pts - shifted_pts, axis=1)
                    mean_dist = np.mean(dists)
                    if mean_dist < best_dist:
                        best_dist = mean_dist
                        
            errors.append(best_dist)
        return errors

    def compute_corner_error(self, ground_truth, predictions):
        """
        Computes the mean Euclidean distance between predicted corners 
        and ground truth corners, returning both px and percentage of diagonal.
        """
        diagonal = np.sqrt(self.image_width**2 + self.image_height**2)
        errors = self._get_corner_errors(ground_truth, predictions)
            
        mean_px = np.mean(errors) if errors else 0.0
        mean_pct = (mean_px / diagonal) * 100 if diagonal > 0 else 0.0
        return mean_px, mean_pct

    def _get_ious(self, ground_truth, predictions):
        ious = []
        for gt, pred in zip(ground_truth, predictions):
            if gt is None or len(gt) != 4:
                continue
            if pred is None or len(pred) != 4:
                ious.append(0.0)
                continue
                
            gt_pts = np.array([gt], dtype=np.int32)
            pred_pts = np.array([pred], dtype=np.int32)
            
            # Draw masks
            gt_mask = np.zeros((self.image_height, self.image_width), dtype=np.uint8)
            pred_mask = np.zeros((self.image_height, self.image_width), dtype=np.uint8)
            
            cv2.fillPoly(gt_mask, gt_pts, 1)
            cv2.fillPoly(pred_mask, pred_pts, 1)
            
            intersection = np.logical_and(gt_mask, pred_mask).sum()
            union = np.logical_or(gt_mask, pred_mask).sum()
            
            iou = intersection / union if union > 0 else 0.0
            ious.append(iou)
            
        return ious

    def compute_iou(self, ground_truth, predictions):
        """
        Computes the Intersection over Union (IoU) of the quadrilateral 
        formed by the 4 corners, using OpenCV to calculate polygon areas.
        """
        ious = self._get_ious(ground_truth, predictions)
        return np.mean(ious) if ious else 0.0

    def compute_pointing_coordinate(self, corners):
        """
        Computes the relative coordinates of the camera center mapped onto the screen.
        Returns (u, v) where [0,0] is top-left and [1,1] is bottom-right, or None if invalid.
        """
        if corners is None or len(corners) != 4:
            return None
            
        cx, cy = self.image_width / 2.0, self.image_height / 2.0
        
        src_pts = np.array(corners, dtype=np.float32)
        dst_pts = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0]
        ], dtype=np.float32)
        
        try:
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            center_pt = np.array([[[cx, cy]]], dtype=np.float32)
            relative_pt = cv2.perspectiveTransform(center_pt, M)
            u, v = relative_pt[0][0]
            return float(u), float(v)
        except Exception:
            return None

    def _get_pointing_errors(self, ground_truth, predictions):
        errors = []
        for gt, pred in zip(ground_truth, predictions):
            if gt is None or len(gt) != 4:
                continue
                
            pt_gt = self.compute_pointing_coordinate(gt)
            pt_pred = self.compute_pointing_coordinate(pred) if pred is not None and len(pred) == 4 else None
            
            if pt_gt is None:
                continue
                
            if pt_pred is None:
                errors.append(1.0)
            else:
                err = np.linalg.norm(np.array(pt_gt) - np.array(pt_pred))
                errors.append(err)
        return errors

    def compute_pointing_error(self, ground_truth, predictions):
        """
        Computes the mean Euclidean distance in relative pointing coordinates 
        between the predicted screen and ground truth screen.
        """
        errors = self._get_pointing_errors(ground_truth, predictions)
        return np.mean(errors) if errors else 0.0
        
    def evaluate_all(self, ground_truth, predictions):
        """
        Computes and returns all metrics as a dictionary.
        """
        valid_gt_count = sum(1 for gt in ground_truth if gt is not None and len(gt) == 4)
        ce_px_list = self._get_corner_errors(ground_truth, predictions)
        iou_list = self._get_ious(ground_truth, predictions)
        pt_err_list = self._get_pointing_errors(ground_truth, predictions)
        
        det_rate = self.compute_detection_rate(ground_truth, predictions)
        diagonal = np.sqrt(self.image_width**2 + self.image_height**2)
        
        def format_stats(lst):
            if not lst:
                return {"mean": 0.0, "median": 0.0, "p95": 0.0}
            return {
                "mean": float(np.mean(lst)),
                "median": float(np.median(lst)),
                "p95": float(np.percentile(lst, 95))
            }
            
        ce_stats = format_stats(ce_px_list)
        iou_stats = format_stats(iou_list)
        pt_stats = format_stats(pt_err_list)
        
        ce_pct_stats = {k: (v / diagonal * 100) if diagonal > 0 else 0.0 for k, v in ce_stats.items()}
        pt_1920_stats = {k: v * 1920.0 for k, v in pt_stats.items()}
        
        # 3.1 False-Lock Rate
        # Fraction of made predictions where pointing error > 0.05
        false_locks = 0
        total_predictions = 0
        
        # 3.2 Time-to-Lock
        ttl_frames = -1
        
        for i, (gt, pred) in enumerate(zip(ground_truth, predictions)):
            if gt is None or len(gt) != 4:
                continue
                
            if pred is not None and len(pred) == 4:
                total_predictions += 1
                pt_gt = self.compute_pointing_coordinate(gt)
                pt_pred = self.compute_pointing_coordinate(pred)
                
                if pt_gt is not None and pt_pred is not None:
                    err = np.linalg.norm(np.array(pt_gt) - np.array(pt_pred))
                    if err > 0.05:
                        false_locks += 1
                    elif ttl_frames == -1:
                        ttl_frames = i  # First correct lock
                        
        false_lock_rate = false_locks / total_predictions if total_predictions > 0 else 0.0
        
        return {
            "Detection Rate": det_rate,
            "False-Lock Rate": false_lock_rate,
            "Time-to-Lock (frames)": float(ttl_frames),
            "Coverage": len(pt_err_list) / valid_gt_count if valid_gt_count > 0 else 0.0,
            "Mean Corner Error (px)": ce_stats['mean'],
            "Median Corner Error (px)": ce_stats['median'],
            "P95 Corner Error (px)": ce_stats['p95'],
            "Mean Corner Error (%)": ce_pct_stats['mean'],
            "Median Corner Error (%)": ce_pct_stats['median'],
            "P95 Corner Error (%)": ce_pct_stats['p95'],
            "Mean IoU": iou_stats['mean'],
            "Median IoU": iou_stats['median'],
            "P95 IoU": iou_stats['p95'],
            "Mean Pointing Error": pt_stats['mean'],
            "Median Pointing Error": pt_stats['median'],
            "P95 Pointing Error": pt_stats['p95'],
            "Mean Pointing Error (px, 1920)": pt_1920_stats['mean'],
            "Median Pointing Error (px, 1920)": pt_1920_stats['median'],
            "P95 Pointing Error (px, 1920)": pt_1920_stats['p95']
        }

