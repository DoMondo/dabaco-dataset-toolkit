# DABACO Dataset Toolkit

![DABACO Demo](demo.gif)

This repository contains the official code for accessing and evaluating the DABACO Dataset (Dispositivo Apuntador de BAjo COste).

> **Dataset Download**: The dataset is hosted on Zenodo: [10.5281/zenodo.22797836](https://doi.org/10.5281/zenodo.22797836)

## Directory Structure

- `python/access/`: Dataloaders for Python to easily iterate over the dataset and its ground truth.
- `python/metrics/`: Standardized evaluation metrics (`Detection Rate`, `Pixel Error`, `IoU`, `Jitter`) to compare algorithm predictions against the ground truth.
- `python/algorithms/`: Reference algorithms (like classical screen contour detection and YOLO instance segmentation) and evaluation scripts.

## Getting Started

To begin working with the dataset, the easiest way is to run the provided baseline script. It demonstrates how to initialize the dataset, iterate over the video frames, and calculate the evaluation metrics using the ground truth.

### Python

Navigate to the `python` directory, create a virtual environment, and install the required dependencies:

```bash
cd python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the algorithm evaluation on an extracted dataset folder. You can choose any detector module in `algorithms/` (e.g. `baseline_classical` or `baseline_yolo`), and optionally use `--visualize` to see the live comparison between the ground truth and the prediction:

```bash
python algorithms/evaluate_algorithm.py /path/to/extracted/dabaco_esp32_ov3660 --algorithm baseline_yolo --visualize
```

