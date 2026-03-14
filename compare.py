import os

import numpy as np
import cv2

# Read the query image.
# folder = './images'
# img_path = ''
# query = cv2.imread(os.path.join(folder, img_path),
#                    cv2.IMREAD_GRAYSCALE)
class Comparator:
    def __init__(self, folder):
        self.folder = folder
        
# create files, images, descriptors globals
    def compare(self, query):
        files = []
        images = []
        descriptors = []
        for (dirpath, dirnames, filenames) in os.walk(self.folder):
            files.extend(filenames)
            for f in files:
                if f.endswith('npy') and f != 'query.npy':
                    descriptors.append(f)
        # print(descriptors)

        # Create the SIFT detector.
        sift = cv2.SIFT.create()

        # Perform SIFT feature detection and description on the
        # query image.
        query_kp, query_ds = sift.detectAndCompute(query, None)

        # Define FLANN-based matching parameters.
        FLANN_INDEX_KDTREE = 1
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)

        # Create the FLANN matcher.
        flann = cv2.FlannBasedMatcher(index_params, search_params)

        # Define the minimum number of good matches for a suspect.
        MIN_NUM_GOOD_MATCHES = 10

        greatest_num_good_matches = 0
        prime_suspect = None

        # print('>> Initiating picture scan...')
        # print(descriptors)
        for d in descriptors:
            # print('--------- analyzing %s for matches ------------' % d)
            matches = flann.knnMatch(
                query_ds, np.load(os.path.join(self.folder, d)), k=2)
            good_matches = []
            for m, n in matches:
                if m.distance < 0.7 * n.distance:
                    good_matches.append(m)
            num_good_matches = len(good_matches)
            name = d.replace('.npy', '').upper()
            if num_good_matches >= MIN_NUM_GOOD_MATCHES:
                print('%s is a suspect! (%d matches)' % \
                    (name, num_good_matches))
                if num_good_matches > greatest_num_good_matches:
                    greatest_num_good_matches = num_good_matches
                    prime_suspect = name
            # else:
                print('%s is NOT a suspect. (%d matches)' % \
                    (name, num_good_matches))

        if prime_suspect is not None:
            print('Prime suspect is %s.' % prime_suspect)
        # else:
            # print('There is no suspect.')

# c = Comparator("./images")
# # img = cv2.pyrDown(cv2.imread("./images/red2x4_90.png", cv2.IMREAD_GRAYSCALE))

# img =cv2.imread("./images/red2x4_180.png", cv2.IMREAD_GRAYSCALE)
# c.compare(img)
if __name__ == "__main__":
    ...