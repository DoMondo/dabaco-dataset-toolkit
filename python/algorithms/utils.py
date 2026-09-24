import numpy as np

def order_points(pts):
    """
    Orders 4 points: top-left, top-right, bottom-right, bottom-left.
    Robust against rotated bounding boxes and ties.
    """
    pts = np.array(pts, dtype="float32")
    # Sort points based on x-coordinates
    xSorted = pts[np.argsort(pts[:, 0]), :]
    
    # Left-most and right-most points
    leftMost = xSorted[:2, :]
    rightMost = xSorted[2:, :]
    
    # Sort left-most by y-coordinate to get top-left and bottom-left
    leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
    (tl, bl) = leftMost
    
    # Sort right-most by y-coordinate to get top-right and bottom-right
    rightMost = rightMost[np.argsort(rightMost[:, 1]), :]
    (tr, br) = rightMost
    
    return np.array([tl, tr, br, bl], dtype="float32")
