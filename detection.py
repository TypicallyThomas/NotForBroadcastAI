import cv2 as cv
import numpy as np
from threading import Thread, Lock


class Facing:
    """ Enum for facing classification """
    DOWN = 0
    FORWARD = 1
    LEFT = 2
    RIGHT = 3


class Detection:
    # Threading properties
    _stopped = True
    _lock = None

    # Properties
    facing = None
    context = None
    screenshot = None
    advert_time = False
    tm_method = cv.TM_CCOEFF_NORMED
    tm_threshold = 0.990

    def __init__(self):
        self._lock = Lock()
        # Load zero needle
        self.zero_needle = cv.imread("./images/zeros.jpg", cv.IMREAD_GRAYSCALE)
        self.zero_needle_w, self.zero_needle_h = self.zero_needle.shape[::-1]

    def update_screenshot(self, screenshot):
        """ Update the screenshot the detection tasks need """
        self._lock.acquire()
        self.screenshot = screenshot
        self._lock.release()

    def start(self):
        self._stopped = False
        t = Thread(target=self.run)
        t.start()

    def stop(self):
        self._stopped = True

    def run(self):
        while not self._stopped:
            if self.screenshot is not None:
                # TODO: Classify context
                # TODO: Classify facing
                # Check if we need to cut to the ads
                self.adverts()

    def adverts(self):
        """ See if the timer is at zero, update the bot if so """
        if self.screenshot is not None:
            res = cv.matchTemplate(cv.cvtColor(self.screenshot, cv.COLOR_BGR2GRAY), self.zero_needle, self.tm_method)
            loc = np.where(res >= self.tm_threshold)
            if loc[0].shape == (1,):
                self._lock.acquire()
                self.advert_time = True
                self._lock.release()
            else:
                self._lock.acquire()
                self.advert_time = False
                self._lock.release()
