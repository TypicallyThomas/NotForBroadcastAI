import cv2 as cv
import numpy as np


class PixelsOfInterest:
    """ Provided original cropping position, these should be important pixels to track"""
    # Note: This depends on resolution of your screen and the resolution of the game
    # Which should be
    SCREEN_1_INDICATOR = (151, 232)
    SCREEN_2_INDICATOR = (329, 232)
    SCREEN_3_INDICATOR = (153, 371)
    SCREEN_4_INDICATOR = (327, 370)
    CENSOR_WAVEFORM = (429, 502)

    SCREEN_INDICATORS = [
        SCREEN_1_INDICATOR,
        SCREEN_2_INDICATOR,
        SCREEN_3_INDICATOR,
        SCREEN_4_INDICATOR
    ]


class Vision:

    # given a list of [x, y, w, h] rectangles returned by find(), convert those into a list of
    # [x, y] positions in the center of those rectangles where we can click on those found items
    @staticmethod
    def get_click_points(rectangles):
        points = []

        # Loop over all the rectangles
        for (x, y, w, h) in rectangles:
            # Determine the center position
            center_x = x + int(w/2)
            center_y = y + int(h/2)
            # Save the points
            points.append((center_x, center_y))

        return points

    # given a list of [x, y, w, h] rectangles and a canvas image to draw on, return an image with
    # all of those rectangles drawn
    @staticmethod
    def draw_rectangles(haystack_img, rectangles):
        # these colors are actually BGR
        line_color = (0, 255, 0)
        line_type = cv.LINE_4

        for (x, y, w, h) in rectangles:
            # determine the box positions
            top_left = (x, y)
            bottom_right = (x + w, y + h)
            # draw the box
            cv.rectangle(haystack_img, top_left, bottom_right, line_color, lineType=line_type)

        return haystack_img

    # given a list of [x, y] positions and a canvas image to draw on, return an image with all
    # of those click points drawn on as cross-hairs
    @staticmethod
    def draw_crosshairs(haystack_img, points):
        # these colors are actually BGR
        marker_color = (255, 0, 255)
        marker_type = cv.MARKER_CROSS

        for (center_x, center_y) in points:
            # draw the center point
            cv.drawMarker(haystack_img, (center_x, center_y), marker_color, marker_type)

        return haystack_img

    @staticmethod
    def centeroid(point_list):
        point_list = np.asarray(point_list, dtype=np.int32)
        length = point_list.shape[0]
        sum_x = np.sum(point_list[:, 0])
        sum_y = np.sum(point_list[:, 1])
        return [np.floor_divide(sum_x, length), np.floor_divide(sum_y, length)]
