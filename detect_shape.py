import numpy as np
import pygame
import cv2

WIDTH, HEIGHT = 800, 600
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)


class DetectShape:
    def pygame_to_cvimage(surface):
        img_str = pygame.image.tostring(surface, "RGB")
        img = np.frombuffer(img_str, dtype=np.uint8).reshape((HEIGHT, WIDTH, 3))
        return img

    def detect_shapes_in_image(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        outline_img = np.zeros_like(image)

        for contour in contours:
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 3:
                cv2.drawContours(outline_img, [contour], -1, (255, 255, 255), 2)
            
            elif len(approx) == 4:
                cv2.drawContours(outline_img, [contour], -1, (0, 0, 255), 2)
            
            else:
                cv2.drawContours(outline_img, [contour], -1, (0, 255, 0), 2)
                
        return outline_img


    def colision(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        outline_img = np.zeros_like(image)

        for contour in contours:
            epsilon = 0.04 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 3:
                # Triangle - Outline in white
                cv2.drawContours(outline_img, [contour], -1, (255, 255, 255), 2)
            
            elif len(approx) == 4:
                # Rectangle - Outline in red
                cv2.drawContours(outline_img, [contour], -1, (0, 0, 255), 2)
            
            else:
                # Circle - Outline in lime
                cv2.drawContours(outline_img, [contour], -1, (0, 255, 0), 2)
                
        return outline_img