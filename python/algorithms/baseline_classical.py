import cv2
import numpy as np
from .utils import order_points

class ClassicalScreenDetector:
    def __init__(self):
        """
        Baseline algorithm that uses classical computer vision (Canny + Contours)
        to detect the 4 corners of a screen/monitor.
        """
        pass
        
    def detect(self, frame):
        """
        Processes a single frame and returns the 4 corners of the detected screen.
        Returns:
            corners: list of 4 (x,y) tuples, or None if not found.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Dilate edges to close gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(dilated.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area, keep the largest ones
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
        
        for c in contours:
            # Approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            
            # If the approximated contour has 4 points, we assume it's the screen
            if len(approx) == 4:
                pts = approx.reshape(4, 2)
                rect = order_points(pts)
                return rect.tolist()
                
        return None
