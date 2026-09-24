import argparse
import cv2
import importlib
import inspect
import numpy as np
import os
import sys

# Add toolkit to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from access.dabaco_dataset import DabacoDataset
from metrics.evaluate import DabacoMetrics

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
        
        predictions = []
        # Convert ground truth dict to list of corners aligned with frames
        # The ground truth JSON keys are string indices "0", "1", ...
        num_frames = ground_truth.get("total_frames", len(ground_truth.get("frames", {})))
        gt_list = [None] * num_frames
        
        for frame_idx, frame_data in ground_truth.get("frames", {}).items():
            gt_list[int(frame_idx)] = frame_data.get("corners")
            
        # Iterate over frames
        for frame_idx, frame in enumerate(seq_iter):
            corners = detector.detect(frame)
            predictions.append(corners)
            
            if args.visualize:
                vis_frame = frame.copy()
                gt = gt_list[frame_idx]
                if gt is not None:
                    pts = np.array(gt, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis_frame, [pts], True, (0, 255, 0), 2)
                if corners is not None:
                    pts = np.array(corners, np.int32).reshape((-1, 1, 2))
                    cv2.polylines(vis_frame, [pts], True, (0, 0, 255), 2)
                
                cv2.imshow(f"Comparison - {args.algorithm} (GT: Green, Pred: Red)", vis_frame)
                    
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
        
        if args.visualize:
            cv2.destroyAllWindows()
            
        # Truncate to the minimum length in case of mismatches
        min_len = min(len(gt_list), len(predictions))
        
        w = ground_truth.get("src_width", 1280)
        h = ground_truth.get("src_height", 960)
        metrics = DabacoMetrics(image_width=w, image_height=h)
        
        results = metrics.evaluate_all(gt_list[:min_len], predictions[:min_len])
        print(f"Results for {seq_name}:")
        for k, v in results.items():
            print(f"  {k}: {v:.4f}")

if __name__ == "__main__":
    main()
