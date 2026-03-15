import numpy as np
import cv2

class Comparator:
    conf_thres: float
    def __init__(self, folder):
        self.folder = folder
        self.desriptor = None
        self.sift  = cv2.ORB.create()
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        # self.matcher = cv2.FlannBasedMatcher(index_params, search_params)
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self.MIN_NUM_GOOD_MATCHES = 10
        self.conf_thres = 1.0

    # create files, images, descriptors globals
    def compare(self, query):
        kp, query_ds = self.sift.detectAndCompute(query, None)
        cv2.drawKeypoints(query, kp, query, (51, 163, 236), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        matches = self.matcher.knnMatch(query_ds, self.desriptor, k=2)
        
        good_matches = []
        for m, n in matches:
            if m.distance < self.conf_thres * n.distance:
                good_matches.append(m)
        
        num_good_matches = len(good_matches)
        # print(f"NUM KEYPOINTS: {len(kp)}")
        if num_good_matches >= self.MIN_NUM_GOOD_MATCHES:
            # if num_good_matches > greatest_num_good_matches:
            #     greatest_num_good_matches = num_good_matches
            print("GOOD")
            return True
        return False

    
    def set_descriptor(self, des):
        self.desriptor = des
                
    def set_conf_thres(self, val):
        self.conf_thres = val

if __name__ == "__main__":
    ...