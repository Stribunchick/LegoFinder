import cv2
import numpy as np

class ColorMatcher:
    def __init__(self):
        self.reference = cv2.imread("./tests1/images/cube_red_real.png")
        self.ref_hsv = cv2.cvtColor(self.reference, cv2.COLOR_BGR2HSV)
        # print(self.reference)

    def find_color_matches(self, image):
        # image = cap.read()
        img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # 3. вычисляем средний цвет детали
        mean_color = np.mean(self.ref_hsv.reshape(-1, 3), axis=0)

        h, s, v = mean_color

        # 4. диапазон цвета (можно подбирать)
        lower = np.array([h-40, 80, 80])
        upper = np.array([h+40, 255, 255])

        # 5. маска
        mask = cv2.inRange(img_hsv, lower, upper)

        # 6. морфология (очистка шума)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # 7. поиск контуров
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


        return contours

if __name__ == "__main__":
    ...