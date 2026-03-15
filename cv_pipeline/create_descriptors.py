import os

import numpy as np
import cv2
# import matplotlib.pyplot as plt

class DescriptorCreator:
    def __init__(self, folder='data') -> None:
        self.folder = folder
        self.feature_detector = cv2.SIFT.create()

    def create_part_description(self, frame, name):
        mask = self.highlight_detail(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        _, descriptors = self.feature_detector.detectAndCompute(gray,mask)
        color_bounds = self.extract_part_cscheme(frame, mask)
        descriptor_file = name.replace('png', 'npy')
        descriptor_file = f"{name}.npz"
        np.savez(
            os.path.join(self.folder, descriptor_file), 
            descriptors=descriptors,
            color_bounds=color_bounds
        )
    
    def extract_part_cscheme(self, frame, mask):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        pixels = hsv[mask == 255]

        if len(pixels) == 0:
            return np.array([0, 0, 0]), np.array([0, 0, 0])
        
        lower = np.percentile(pixels, 5, axis=0)
        upper = np.percentile(pixels, 95, axis=0)

        margin = np.array([10, 30, 30])

        lower = np.maximum(lower - margin, [0, 0, 0])
        upper = np.minimum(upper + margin, [179, 255, 255])
        
        return lower.astype(np.uint8), upper.astype(np.uint8)
    
    def highlight_detail(self, frame):
        img = frame
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255,
                                    cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        # Remove noise.
        kernel = np.ones((3,3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel,
                                iterations=2)

        # Find the sure background region.
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # Find the sure foreground region.
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(
                dist_transform, 0.7 * dist_transform.max(), 255, 0)
        sure_fg = sure_fg.astype(np.uint8)

        # Find the unknown region.
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Label the foreground objects.
        _, markers = cv2.connectedComponents(sure_fg)

        # Add one to all labels so that sure background is not 0, but 1.
        markers += 1

        # Label the unknown region as 0.
        markers[unknown==255] = 0

        markers = cv2.watershed(img, markers)
        img[markers==-1] = [255, 0, 0]
        # plt.figure()
        # plt.imshow(img)
        # plt.show()
        cv2.imshow("test", img)
        mask = np.zeros(gray.shape, dtype=np.uint8)
        mask[markers > 1] = 255
        return mask