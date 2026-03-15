import cv2
import numpy as np

class ColorMatcher:
    def __init__(self):
        # self.reference = cv2.imread("./tests1/images/red2x4.png")
        # self.ref_hsv = cv2.cvtColor(self.reference, cv2.COLOR_BGR2HSV)
        self.range_color: np.ndarray | None = None

    def find_color_matches(self, image):
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        mask_comb = np.zeros(image.shape[:2], dtype=np.uint8)
        # print(self.range_color.shape)
        if self.range_color is None:
            return None
        lower = self.range_color[0]
        upper = self.range_color[1]
        mask = cv2.inRange(img_hsv, np.array(lower), np.array(upper))
        mask_comb |= mask
        
        contours, _ = cv2.findContours(mask_comb, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = 250
        contour_filter = [c for c in contours if cv2.contourArea(c) > min_area]

        return contour_filter
    
    def set_reference(self, color_bounds):
        self.range_color = color_bounds

if __name__ == "__main__":
    ...
    