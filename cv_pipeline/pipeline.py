import cv2
# from sift_test import TemplateMatcher
from .color_masking import ColorMatcher
from .compare import Comparator
import os
import numpy as np
class Pipeline:
    def __init__(self, folder):
          self.folder = folder
          self.cmatcher = ColorMatcher()
          self.comparator = Comparator(folder)
          self.det_name = ''

    def process(self, frame):
        img = frame // 6 * 6 + 6 // 2
        contours = self.cmatcher.find_color_matches(frame)
        if not contours:
            return frame
        for cnt in contours:
            if cv2.contourArea(cnt) > 500:
                x,y,w,h = cv2.boundingRect(cnt)
                roi = frame[y:y+h, x:x+w]
                
                temp_img = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                match = self.comparator.compare(temp_img)
                if match:
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                    print("[SIFT] MATCH")
                print("[COLOR] MATCH")
        return frame

    def update_template(self, det_name):
        des, cb = self._load_part_info(det_name)
        if des is None and cb is None:
            return
        self.det_name = det_name
        self.cmatcher.set_reference(cb)
        self.comparator.set_descriptor(des)
    
    def _load_part_info(self, det_name):
        if not det_name:
            return None, None
        path = f"{self.folder}/{det_name}"
        
        print(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Файл не найден: {path}")
        data = np.load(path, allow_pickle=True)
        # print(data)
        descriptors = data["descriptors"]
        color_bounds = data["color_bounds"]

        return descriptors, color_bounds