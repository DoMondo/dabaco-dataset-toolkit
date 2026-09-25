# DaBaCo Dataset Schema

This document describes the structure of the JSON files distributed in the DaBaCo dataset.

## Coordinate System and Conventions
- **Origin**: Top-Left corner of the image (0, 0).
- **Canonical Corner Order**: `[Top-Left, Top-Right, Bottom-Right, Bottom-Left]`. All quadrilateral coordinates follow this clockwise order starting from the top-left corner.
- **Resolution**: Ground truth coordinates are defined in the source resolution (specified per sequence in metadata). In some cases, `src_width` and `src_height` refer to the original raw video size before crop or downscaling, while the frames directory contains resized/inpainted versions. The provided loader scripts automatically normalize coordinates using the frame dimensions.

## JSON File Structure

```json
{
  "sequence_name": "rpi4_ov5647_scrA_v1_m1fhd",
  "total_frames": 300,
  "frames": {
    "0": {
      "corners": [[10, 10], [100, 10], [100, 50], [10, 50]],
      "status": "tracked"
    },
    "1": {
      "corners": null,
      "status": "unlabeled"
    }
  }
}
```

### Missing Ground Truth (`status: "unlabeled"`)
Some frames may not contain valid ground truth (e.g. occlusion, blur where GT was impossible). These frames are marked with `"status": "unlabeled"` and `"corners": null`. They are **excluded** from evaluation calculations.

### Frame Status Types
The `status` field provides information about how the ground truth was obtained:
- `auto`: ArUco markers directly detected by the auto-annotator.
- `tracked`: Estimated via optical flow tracking (useful for maintaining GT during partial occlusion or fast motion blur).
- `manual`: Hand-annotated.
- `interpolated`: Interpolated between two confident detections.
- `unlabeled`: No valid ground truth available.
