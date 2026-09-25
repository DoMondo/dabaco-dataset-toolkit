import os
import json
import glob
import cv2

class DabacoDataset:
    def __init__(self, dataset_dir, load_inpainted=False):
        """
        Initializes the DABACO dataset loader.
        
        Args:
            dataset_dir (str): Path to the extracted dataset directory for a camera.
                               It should contain the JSON files and the frame directories.
            load_inpainted (bool): If True, loads the frames from the _inpainted directories.
                                   Otherwise, loads the raw frames (mjpeg/jpg).
        """
        self.dataset_dir = dataset_dir
        self.load_inpainted = load_inpainted
        self.sequences = self._find_sequences()
        
    def _find_sequences(self):
        jsons = glob.glob(os.path.join(self.dataset_dir, "*.json"))
        sequences = []
        for j in jsons:
            base_name = os.path.basename(j).replace(".json", "")
            
            # Check if the video/frames dir exists
            frames_dir = os.path.join(self.dataset_dir, f"{base_name}_inpainted" if self.load_inpainted else base_name)
            
            if os.path.exists(frames_dir):
                sequences.append({
                    "name": base_name,
                    "json_path": j,
                    "frames_dir": frames_dir
                })
        return sorted(sequences, key=lambda x: x["name"])

    def __len__(self):
        return len(self.sequences)
        
    def get_sequence_names(self):
        return [s["name"] for s in self.sequences]

    def get_sequence(self, index_or_name):
        """
        Retrieves a sequence iterator and its ground truth.
        """
        if isinstance(index_or_name, int):
            seq = self.sequences[index_or_name]
        else:
            seq = next((s for s in self.sequences if s["name"] == index_or_name), None)
            if seq is None:
                raise ValueError(f"Sequence {index_or_name} not found.")
                
        # Load ground truth
        with open(seq["json_path"], "r") as f:
            ground_truth = json.load(f)
            
        # Try to load metadata if present in the raw sequence directory
        metadata = {}
        raw_frames_dir = seq["frames_dir"].replace("_inpainted", "")
        metadata_path = os.path.join(raw_frames_dir, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
        return SequenceIterator(seq["frames_dir"]), ground_truth, metadata


class SequenceIterator:
    def __init__(self, frames_dir):
        self.frames_dir = frames_dir
        
        # Determine if we are dealing with a directory of frames or an mjpeg file
        self.is_video_file = False
        self.cap = None
        self.frame_files = []
        
        video_path = os.path.join(frames_dir, "video.mjpeg")
        if os.path.exists(video_path):
            self.is_video_file = True
            self.cap = cv2.VideoCapture(video_path)
        else:
            self.frame_files = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")), 
                                      key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))
            self.current_idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.is_video_file:
            ret, frame = self.cap.read()
            if not ret:
                self.cap.release()
                raise StopIteration
            return frame
        else:
            if self.current_idx >= len(self.frame_files):
                raise StopIteration
            frame = cv2.imread(self.frame_files[self.current_idx])
            self.current_idx += 1
            return frame
