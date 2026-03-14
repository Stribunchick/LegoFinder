import cv2
# from sift_test import TemplateMatcher
from colour_masking import ColorMatcher
from compare import Comparator

class Pipeline:
    def __init__(self):
          self.cmatcher = ColorMatcher()
          self.comparator = Comparator("./tests1/images")

    def process(self, frame):
        # print("PROCESSING")
        contours = self.cmatcher.find_color_matches(frame)
        # print(contours)
        for cnt in contours:
            if cv2.contourArea(cnt) > 500:
                x,y,w,h = cv2.boundingRect(cnt)
                roi = frame[y:y+h, x:x+w]
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                temp_img = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV) # Чтобы использовать -> перевести в HSV
                self.comparator.compare(temp_img)
        return frame