# DABACO Dataset Toolkit

![DABACO Demo](docs/images/demo.gif)

This repository contains the official toolkit for accessing, evaluating, and benchmarking screen detection and pointing algorithms on the **DABACO Dataset** (*Dispositivo Apuntador de BAjo COste*).

> **Dataset Download**: The dataset is hosted on Zenodo: [10.5281/zenodo.22797836](https://doi.org/10.5281/zenodo.22797836) *(Note: This DOI is currently in draft state and may not resolve publicly yet).*

---

## Directory Structure

- `python/access/`: Dataloaders to easily iterate over camera sequences and annotations.
- `python/metrics/`: Standardized evaluation metrics (`Detection Rate`, `Corner Error (px/%)`, `IoU`, `Pointing Error (%)`) comparing algorithm predictions against ground truth.
- `python/algorithms/`: Screen detection algorithms and baseline models:
  - `baseline_classical.py`: Advanced classical computer vision pipeline (bilateral filtering, multi-scale Canny edge maps, adaptive thresholding, convexity & aspect ratio scoring).
  - `baseline_yolo.py`: Deep learning instance segmentation detector using YOLO.
  - `evaluate_algorithm.py`: Main evaluation script computing frame-by-frame and aggregate metrics with an interactive virtual HUD visualizer.
- `python/tools/`:
  - `compare_algorithms.py`: Standalone interactive HTML benchmark generator (with Dark/Light themes, official ULL corporate palette, and Plotly charts).
- `results/`: Directory where per-sequence evaluation JSON reports are saved.

> **Note on Frame Numbering**: In some sequences (e.g., `rpi4_ov5647_*`), the raw frame directories preserve original capture indices (e.g. `000182.jpg` to `000952.jpg`), while the `_inpainted` versions are renumbered starting from 0. The Python dataloader (`DabacoDataset`) automatically handles this misalignment by sorting sequentially, but be cautious if attempting to match frames manually by filename.

---

## Getting Started

### Prerequisites & Installation

- **Python Version**: Python `>= 3.9` (Reference environment: `3.14.7`, pinned in `.python-version` for `pyenv`/`uv`/`asdf`).

Clone the repository and set up a Python virtual environment:

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate

# Standard installation (compatible version ranges)
pip install -r requirements.txt

# Or exact reproducible freeze
pip install -r requirements-lock.txt
```

---

## Evaluating Algorithms

Run the evaluation script on an extracted dataset folder. You can evaluate all sequences or target a specific one with `--sequence`:

```bash
# Evaluate baseline_classical on a dataset directory
python algorithms/evaluate_algorithm.py /path/to/dataset --algorithm baseline_classical

# Evaluate baseline_yolo with live HUD visualization
python algorithms/evaluate_algorithm.py /path/to/dataset --algorithm baseline_yolo --visualize

# Evaluate a specific sequence
python algorithms/evaluate_algorithm.py /path/to/dataset --algorithm baseline_classical --sequence esp32_ov3660_scrA_v1_m1svga
```

### Evaluation Metrics

The toolkit calculates several metrics frame-by-frame and aggregates them per sequence:

- **Detection Rate**: Percentage of frames where the algorithm produced a valid screen quadrilateral detection.
- **Coverage**: Fraction of ground truth screen frames that were successfully detected by the algorithm.
- **False-Lock Rate**: Fraction of detections that locked onto an incorrect object (pointing error > 5%).
- **Time-to-Lock**: Average number of frames it takes the algorithm to acquire a lock after the screen enters the frame.
- **IoU (Intersection over Union)**: Geometric overlap between the predicted polygon and the ground truth. Higher is better (1.0 = perfect match).
- **Corner Error (px)**: Mean Euclidean distance in pixels between the 4 predicted corners and the ground truth corners.
- **Corner Error (%)**: Corner error normalized by the full image diagonal.
- **Pointing Error (px, 1920)**: The pointing error scaled to a standard Full HD monitor width (1920px) for human-readable physical intuition (e.g. "missed the target by 50px on a standard screen").
- **Pointing Error (%)**: The Euclidean distance between where the camera is looking relative to the predicted screen vs the ground truth screen. 0% is perfect, 100% means missing by a full screen width.
- **Inference Time (ms)**: Processing latency per frame.

### Ground Truth Status Labels

The dataset annotations (ground truth) classify each frame with a `status` tag indicating how the labeling was generated. You can filter by these statuses in the comparison dashboard to understand how algorithms perform under different conditions (e.g., fast motion where auto-detection fails).

- **`auto`**: Automatic direct detection using ArUco markers with subpixel accuracy. These are highly reliable anchor frames.
- **`tracked`**: Temporally tracked via bidirectional Lucas-Kanade optical flow. Usually occurs during motion blur when markers are not perfectly readable.
- **`interpolated`**: Linearly interpolated between anchors. Occurs in small gaps where neither detection nor tracking succeeded.
- **`manual`**: Human-reviewed or manually adjusted anchor.
- **`unlabeled`**: No label present (the screen is not visible, heavily occluded, or the frame was bypassed). Algorithms are not penalized if they also predict nothing, but predicting a screen here counts as a False-Lock.

### Interactive Visualization (HUD) Controls

![Interactive Visualization HUD](docs/images/visualization_hud.png)

When running with `--visualize`:
- **Green Bounding Box**: Ground truth screen corners.
- **Red Bounding Box**: Predicted screen corners.
- **Blue Reticle / Crosshair**: Camera optical center (frame center).
- **Virtual Screen Mini-HUD (Top-Left)**: Displays the pointing coordinate relative to the screen frame (Green dot: Ground truth, Red dot: Prediction).
- **Keyboard Shortcuts**:
  - `Space` / Any key: Step to the next frame.
  - `Q` / `q`: Exit visualization.

Evaluation results are automatically exported to `results/<algorithm_name>/<sequence_name>.json`.

---

## Benchmark & Comparison Dashboard

![Benchmark Dashboard](docs/images/benchmark_dashboard.png)

📊 **[Open Live Interactive Benchmark](https://domondo.github.io/dabaco-dataset-toolkit/)** *(via GitHub Pages)*  
*(Alternative direct mirror: [RawGithack Live Mirror](https://raw.githack.com/DoMondo/dabaco-dataset-toolkit/main/docs/index.html))*

To regenerate or compare newly evaluated algorithms (e.g. `baseline_classical` vs. `baseline_yolo`) locally across all sequences:

```bash
# Generates docs/index.html (GitHub Pages) by default
python tools/compare_algorithms.py --results_dir results
```

Open `docs/index.html` in your browser.

### Features of the Comparison Tool:
- **Interactive Metric Selection**: Filter by `Mean IoU`, `Corner Error (px)`, `Corner Error (%)`, `Pointing Error`, or `Inference Time (ms)`.
- **Global & Sequence Views**:
  - **Global Mode**: Compare sequence-level bars grouped by algorithm + global average overview cards.
  - **Sequence Mode**: Frame-by-frame bar chart with interactive range slider + sequence average overview cards.
- **Algorithm Filtering**: Real-time checkboxes to toggle algorithms in the comparison.
- **Corporate Styling**: Styled according to the **Universidad de La Laguna (ULL)** design system with automatic Dark / Light mode toggle.
