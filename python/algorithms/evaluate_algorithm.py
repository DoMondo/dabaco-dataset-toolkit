import argparse
import cv2
import importlib
import inspect
import numpy as np
import os
import sys
import time
import json

# Add toolkit to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from access.dabaco_dataset import DabacoDataset
from metrics.evaluate import DabacoMetrics

class NpEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy data types."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def load_algorithm_detector(algorithm_name):
    """
    Dynamically loads the detector class from the specified module name.
    The algorithm_name matches the python file name in algorithms/ (e.g. 'baseline_yolo').
    """
    clean_name = algorithm_name[:-3] if algorithm_name.endswith('.py') else algorithm_name
    module_name = f"algorithms.{clean_name}"
    
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        raise ValueError(f"Could not import module '{module_name}': {e}")
        
    # Search for a detector class in the module that implements a 'detect' method
    detector_cls = None
    for _, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ == mod.__name__ and hasattr(cls, "detect"):
            detector_cls = cls
            break
            
    if detector_cls is None:
        raise ValueError(f"No detector class with a 'detect' method found in {module_name}")
        
    return detector_cls()

def main():
    parser = argparse.ArgumentParser(description="Evaluate screen detection algorithms on DaBaCo dataset")
    parser.add_argument("dataset_dir", nargs="?", default=".", help="Path to extracted dataset")
    parser.add_argument("--algorithm", "--detector", dest="algorithm", default="baseline_classical", 
                        help="Algorithm module to use, matching filename without .py (e.g. baseline_yolo, baseline_classical)")
    parser.add_argument("--visualize", action="store_true", help="Show comparison between ground truth and detection")
    parser.add_argument("--sequence", help="Name of a specific sequence to evaluate (e.g., esp32_ov3660_scrA_v1_m1svga)")
    args = parser.parse_args()
    
    dataset_dir = args.dataset_dir
    
    try:
        dataset = DabacoDataset(dataset_dir, load_inpainted=True)
    except Exception as e:
        print(f"Could not load dataset at {dataset_dir}: {e}")
        return
        
    detector = load_algorithm_detector(args.algorithm)
        
    sequences_to_evaluate = [args.sequence] if args.sequence else dataset.get_sequence_names()
    
    for seq_name in sequences_to_evaluate:
        if args.sequence and seq_name not in dataset.get_sequence_names():
            print(f"Sequence {seq_name} not found in dataset.")
            continue
            
        print(f"Evaluating sequence: {seq_name}")
        seq_iter, ground_truth = dataset.get_sequence(seq_name)
        
        # Create results directory for the algorithm
        results_dir = os.path.join("results", args.algorithm)
        os.makedirs(results_dir, exist_ok=True)
        
        predictions = []
        per_frame_results = []
        # Convert ground truth dict to list of corners aligned with frames
        # The ground truth JSON keys are string indices "0", "1", ...
        num_frames = ground_truth.get("total_frames", len(ground_truth.get("frames", {})))
        gt_list = [None] * num_frames
        
        for frame_idx, frame_data in ground_truth.get("frames", {}).items():
            gt_list[int(frame_idx)] = frame_data.get("corners")
            
        # Iterate over frames
        for frame_idx, frame in enumerate(seq_iter):
            fh, fw = frame.shape[:2]
            metrics = DabacoMetrics(image_width=fw, image_height=fh)
            
            t0 = time.time()
            corners = detector.detect(frame)
            t1 = time.time()
            inference_time = t1 - t0
            
            predictions.append(corners)
            
            # Compute and print per-frame metrics
            gt_corners = gt_list[frame_idx]
            pt_gt = metrics.compute_pointing_coordinate(gt_corners)
            pt_pred = metrics.compute_pointing_coordinate(corners)
            
            pt_gt_str = f"({pt_gt[0]:.3f}, {pt_gt[1]:.3f})" if pt_gt else "None"
            pt_pred_str = f"({pt_pred[0]:.3f}, {pt_pred[1]:.3f})" if pt_pred else "None"
            
            ce_px, ce_pct = metrics.compute_corner_error([gt_corners], [corners])
            iou = metrics.compute_iou([gt_corners], [corners])
            pt_err = metrics.compute_pointing_error([gt_corners], [corners])
            
            per_frame_results.append({
                "frame": frame_idx,
                "inference_time": inference_time,
                "corner_error_px": ce_px,
                "corner_error_pct": ce_pct,
                "iou": iou,
                "pointing_error": pt_err
            })
            
            print(f"Frame {frame_idx:04d}: Time: {inference_time*1000:.1f}ms | Pointing GT={pt_gt_str} | Pred={pt_pred_str} | CE: {ce_px:.1f}px ({ce_pct:.2f}%) | IoU: {iou:.3f} | PtErr: {pt_err:.3f}")
            
            if args.visualize:
                vis_frame = frame.copy()
                gt = gt_list[frame_idx]
                
                # Draw a blue crosshair/reticle at the center of the image frame
                center_x, center_y = int(fw / 2), int(fh / 2)
                cv2.drawMarker(vis_frame, (center_x, center_y), (255, 0, 0), cv2.MARKER_CROSS, 20, 2)
                cv2.circle(vis_frame, (center_x, center_y), 8, (255, 0, 0), 1)
                
                # Draw bounding polygons for ground truth and prediction
                if gt is not None:
                    pts = np.array(gt, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis_frame, [pts], True, (0, 255, 0), 2)
                        
                if corners is not None:
                    pts = np.array(corners, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis_frame, [pts], True, (0, 0, 255), 2)
                
                # Draw virtual screen in the top-left corner
                v_x, v_y = 15, 15
                v_w, v_h = 120, 75
                
                # Semi-transparent background for the virtual screen
                overlay = vis_frame.copy()
                cv2.rectangle(overlay, (v_x, v_y), (v_x + v_w, v_y + v_h), (30, 30, 30), -1)
                cv2.addWeighted(overlay, 0.7, vis_frame, 0.3, 0, vis_frame)
                cv2.rectangle(vis_frame, (v_x, v_y), (v_x + v_w, v_y + v_h), (220, 220, 220), 1)
                
                # Draw center crosshair on virtual screen
                cv2.drawMarker(vis_frame, (int(v_x + v_w / 2), int(v_y + v_h / 2)), (100, 100, 100), cv2.MARKER_CROSS, 8, 1)
                
                # Draw GT pointing position (Green dot)
                if pt_gt is not None:
                    gx = int(v_x + pt_gt[0] * v_w)
                    gy = int(v_y + pt_gt[1] * v_h)
                    if 0 <= gx < fw and 0 <= gy < fh:
                        cv2.circle(vis_frame, (gx, gy), 4, (0, 255, 0), -1)
                        cv2.circle(vis_frame, (gx, gy), 5, (0, 0, 0), 1)
                        
                # Draw Predicted pointing position (Red dot)
                if pt_pred is not None:
                    px = int(v_x + pt_pred[0] * v_w)
                    py = int(v_y + pt_pred[1] * v_h)
                    if 0 <= px < fw and 0 <= py < fh:
                        cv2.circle(vis_frame, (px, py), 4, (0, 0, 255), -1)
                        cv2.circle(vis_frame, (px, py), 5, (0, 0, 0), 1)
                
                cv2.imshow(f"Comparison - {args.algorithm} (GT: Green, Pred: Red)", vis_frame)
                # Wait indefinitely for a key press; terminate program immediately if 'q' or 'Q' is pressed
                key = cv2.waitKey(0) & 0xFF
                if key in (ord('q'), ord('Q')):
                    cv2.destroyAllWindows()
                    print("\nVisualization terminated by user.")
                    return
        
        if args.visualize:
            cv2.destroyAllWindows()
            
        # Truncate to the minimum length in case of mismatches
        min_len = min(len(gt_list), len(predictions))
        
        results = metrics.evaluate_all(gt_list[:min_len], predictions[:min_len])
        print(f"Results for {seq_name}:")
        for k, v in results.items():
            print(f"  {k}: {v:.4f}")
            
        # Save sequence results
        seq_results = {
            "sequence": seq_name,
            "algorithm": args.algorithm,
            "aggregated_metrics": results,
            "frame_metrics": per_frame_results
        }
        
        result_path = os.path.join(results_dir, f"{seq_name}.json")
        with open(result_path, "w") as f:
            json.dump(seq_results, f, indent=4, cls=NpEncoder)
        print(f"Results saved to {result_path}")

if __name__ == "__main__":
    main()
