import os

import numpy as np
import cv2

# def create_descriptors(folder):
#     feature_detector = cv2.SIFT.create()
#     files = []
#     for (dirpath, dirnames, filenames) in os.walk(folder):
#         files.extend(filenames)
#     for f in files:
#         create_descriptor(folder, f, feature_detector)

# def create_descriptor(folder, image_path, feature_detector):
#     if not image_path.endswith('png'):
#         print('skipping %s' % image_path)
#         return
#     print('reading %s' % image_path)
#     img = cv2.imread(os.path.join(folder, image_path),
#                      cv2.IMREAD_GRAYSCALE)
#     keypoints, descriptors = feature_detector.detectAndCompute(
#         img, None)
#     descriptor_file = image_path.replace('png', 'npy')
#     np.save(os.path.join(folder, descriptor_file), descriptors)

# folder = './images'
# create_descriptors(folder)

class DescriptorCreator:
    def __init__(self, folder) -> None:
        self.folder = folder
        self.feature_detector = cv2.SIFT.create()

    # def create_descriptors(self):
        
    #     files = []
    #     for (dirpath, dirnames, filenames) in os.walk(self.folder):
    #         files.extend(filenames)
    #     for f in files:
    #         create_descriptor(self.folder, f)

    def create_descriptor(self, frame, name):
        # if not image_path.endswith('png'):
        #     print('skipping %s' % image_path)
        #     return

        # print('reading %s' % image_path)
        # img = cv2.imread(os.path.join(folder, image_path),
        #                 cv2.IMREAD_GRAYSCALE)
        keypoints, descriptors = self.feature_detector.detectAndCompute(frame, None)
        descriptor_file = name.replace('png', 'npy')
        descriptor_file = f"{name}.npy"
        np.save(os.path.join(self.folder, descriptor_file), descriptors)