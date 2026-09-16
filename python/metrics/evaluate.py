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
        if len(ground_truth) == 0:
            return 0.0
            
        detected_frames = sum(1 for p in predictions if p is not None and len(p) == 4)
        return detected_frames / len(ground_truth)

    def compute_corner_error(self, ground_truth, predictions):
        """
        Computes the mean Euclidean distance between predicted corners 
        and ground truth corners, returning both px and percentage of diagonal.
        """
        diagonal = np.sqrt(self.image_width**2 + self.image_height**2)
        errors = []
        for gt, pred in zip(ground_truth, predictions):
            if pred is None or len(pred) != 4 or gt is None or len(gt) != 4:
                continue
                
            gt_pts = np.array(gt, dtype=np.float32)
            pred_pts = np.array(pred, dtype=np.float32)
            
            dists = np.linalg.norm(gt_pts - pred_pts, axis=1)
            errors.append(np.mean(dists))
            
        mean_px = np.mean(errors) if errors else 0.0
        mean_pct = (mean_px / diagonal) * 100 if diagonal > 0 else 0.0
        return mean_px, mean_pct

    def compute_iou(self, ground_truth, predictions):
        """
        Computes the Intersection over Union (IoU) of the quadrilateral 
        formed by the 4 corners, using OpenCV to calculate polygon areas.
        """
        ious = []
        for gt, pred in zip(ground_truth, predictions):
            if pred is None or len(pred) != 4 or gt is None or len(gt) != 4:
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
            
        return np.mean(ious) if ious else 0.0

    def compute_jitter(self, predictions):
        """
        Computes jitter (instability) as the average Euclidean distance 
        between predicted corners in consecutive frames, returning both px and %.
        """
        diagonal = np.sqrt(self.image_width**2 + self.image_height**2)
        jitters = []
        for i in range(1, len(predictions)):
            prev_pred = predictions[i-1]
            curr_pred = predictions[i]
            
            if prev_pred is None or curr_pred is None or len(prev_pred) != 4 or len(curr_pred) != 4:
                continue
                
            prev_pts = np.array(prev_pred, dtype=np.float32)
            curr_pts = np.array(curr_pred, dtype=np.float32)
            
            dists = np.linalg.norm(prev_pts - curr_pts, axis=1)
            jitters.append(np.mean(dists))
            
        mean_px = np.mean(jitters) if jitters else 0.0
        mean_pct = (mean_px / diagonal) * 100 if diagonal > 0 else 0.0
        return mean_px, mean_pct
        
    def evaluate_all(self, ground_truth, predictions):
        """
        Computes and returns all metrics as a dictionary.
        """
        ce_px, ce_pct = self.compute_corner_error(ground_truth, predictions)
        jit_px, jit_pct = self.compute_jitter(predictions)
        
        return {
            "Detection Rate": self.compute_detection_rate(ground_truth, predictions),
            "Mean Corner Error (px)": ce_px,
            "Mean Corner Error (%)": ce_pct,
            "Mean IoU": self.compute_iou(ground_truth, predictions),
            "Mean Jitter (px)": jit_px,
            "Mean Jitter (%)": jit_pct
        }
