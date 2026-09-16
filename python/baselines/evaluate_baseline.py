import os
import sys

# Add toolkit to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from access.python.dabaco_dataset import DabacoDataset
from metrics.evaluate import DabacoMetrics
from baselines.screen_detector import ClassicalScreenDetector

def main():
    # Example path (adjust to your extracted dataset)
    # dataset_dir = "/path/to/extracted/dabaco_esp32_ov3660"
    dataset_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    try:
        dataset = DabacoDataset(dataset_dir, load_inpainted=True)
    except Exception as e:
        print(f"Could not load dataset at {dataset_dir}: {e}")
        return
        
    detector = ClassicalScreenDetector()
    
    for seq_name in dataset.get_sequence_names():
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
        for frame in seq_iter:
            corners = detector.detect(frame)
            predictions.append(corners)
            
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
