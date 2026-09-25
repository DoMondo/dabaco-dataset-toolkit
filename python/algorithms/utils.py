import numpy as np

def order_points(pts):
    """
    Orders 4 points: top-left, top-right, bottom-right, bottom-left.
    Robust against rotated bounding boxes by sorting based on angle from the centroid.
    """
    pts = np.array(pts, dtype="float32")
    centroid = np.mean(pts, axis=0)
    
    # Compute angles relative to centroid (y goes down in image coordinates)
    angles = np.arctan2(pts[:, 1] - centroid[1], pts[:, 0] - centroid[0])
    
    # Sort points by angle
    sorted_pts = pts[np.argsort(angles)]
    
    # Ensure the first point is the top-left by finding the point with minimum (x + y)
    sums = sorted_pts.sum(axis=1)
    tl_index = np.argmin(sums)
    
    # Cyclically shift the array so that top-left is first
    ordered_pts = np.roll(sorted_pts, -tl_index, axis=0)
    
    return ordered_pts
