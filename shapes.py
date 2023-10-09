from speed import SpeedCalculator
from qlearning import QLearning

import numpy as np
import pygame
import time
import cv2

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)


class DetectShape:
    def __init__(self):
        self.rectangle_positions = []
        self.triangle_position = None
        self.speed_calculator = SpeedCalculator()
        self.speed = 0

    def pygame_to_cvimage(self, surface):
        img_str = pygame.image.tostring(surface, "RGB")
        img = np.frombuffer(img_str, dtype=np.uint8).reshape(
            (HEIGHT, WIDTH, 3))
        return img

    def detect_shapes_in_image(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(
            edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        outline_img = np.zeros_like(image)

        for contour in contours:
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 3:
                cv2.drawContours(
                    outline_img, [contour], -1, (255, 255, 255), 2)

            elif len(approx) == 4:
                cv2.drawContours(outline_img, [contour], -1, (0, 0, 255), 2)

            else:
                cv2.drawContours(outline_img, [contour], -1, (0, 255, 0), 2)

        return outline_img

    def collision(self, image):
        current_time = time.time()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.triangle_position = None
        self.rectangle_positions = []

        for contour in contours:
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 3:
                triangle_vertices = [tuple(pt[0]) for pt in approx]
                self.triangle_position = triangle_vertices

            elif len(approx) == 4:
                x, y, w, h = cv2.boundingRect(contour)
                self.rectangle_positions.append(((x, y), (x + w, y), (x, y + h), (x + w, y + h)))

        if not self.triangle_position:
            return None

        x, y, w, h = cv2.boundingRect(contours[0])
        middle_position = (x + w // 2, y + h // 2)
        self.speed = self.speed_calculator.calculate_speed(middle_position, current_time)

        for rect_corners in self.rectangle_positions:
            top_left, top_right, bottom_left, bottom_right = rect_corners
            time_to_collision = (max(self.triangle_position, key=lambda t: t[1])[1] - top_left[1]) / self.speed

            projected_rect_top_left = (top_left[0], top_left[1] + self.speed * time_to_collision)
            projected_rect_top_right = (top_right[0], top_right[1] + self.speed * time_to_collision)

            triangle_x_positions = [vert[0] for vert in self.triangle_position]
            if max(triangle_x_positions) >= projected_rect_top_left[0] and min(triangle_x_positions) <= projected_rect_top_right[0]:
                return True

        return False

