import globalVariable
import cv2 as cv
import numpy as np
import pyautogui
import random
from time import time
from threading import Thread, Lock
from vision import PixelsOfInterest


class BotState:
    """" Enum to track current bot actions """
    INITIALISING = 0
    WATCHING = 1
    MOVING = 2


class Feeds:
    """"Keeping track of which camera is live with this enum"""
    # TODO: Work out how to check accuracy. Snugglehugs can mess with this enum
    CAMERA_1 = 0
    CAMERA_2 = 1
    CAMERA_3 = 2
    CAMERA_4 = 3


class IndicatorColors:
    """ These are used as weights to give incentive for better options """
    BLACK = -1
    RED = 0
    BLUE = 1
    GREEN = 2


class AlexBot:
    # Constants
    INITIALISING_SECONDS = 10
    MINIMAL_CUT_TIME = 1.2
    MAXIMUM_CUT_TIME = 8.0
    OPTIMAL_CUT_TIME = 3.5
    DEBUG = globalVariable.get_value('DEBUG')
    LOWER_RED = np.array([0, 120, 40])
    UPPER_RED = np.array([10, 255, 255])
    LOWER_BLUE = np.array([90, 120, 40])
    UPPER_BLUE = np.array([120, 255, 255])
    LOWER_GREEN = np.array([45, 120, 40])
    UPPER_GREEN = np.array([70, 255, 255])
    WIDTH_FACTOR = globalVariable.get_value('width_factor')
    HEIGHT_FACTOR = globalVariable.get_value('height_factor')

    # Threading properties
    _stopped = True
    _lock = None

    # Properties
    state = None
    init_timestamp = None
    last_cut = None
    screenshot = None
    screenshot_hsv = None
    targets = []
    current_screen = None
    screen_values = {}
    indicator_colors = {}

    # Translation
    INDICATOR_NAMES = {
        IndicatorColors.RED: "red",
        IndicatorColors.BLUE: "blue",
        IndicatorColors.GREEN: "green",
        IndicatorColors.BLACK: "black"
    }

    def __init__(self):
        self._lock = Lock()
        self.state = BotState.INITIALISING
        self.init_timestamp = time()
        self.last_cut = time()
        # Value to determine if an indicator is clearly one color or another
        self.CHANNEL_THRESHOLD = globalVariable.get_value('channel_threshold')
        self.time_limit = True
        self.advert_time = False

    # Threading methods
    def update_targets(self, targets):
        """" Essentially copied from Ben Johnson's code. Currently not used, may need to remove """
        self._lock.acquire()
        self.targets = targets
        self._lock.release()
        if self.DEBUG:
            print("Updated targets")

    def update_adverts(self, advert_time):
        """ Updates the self.advert_time bool when it's time to go to the ads """
        self._lock.acquire()
        self.advert_time = advert_time
        self._lock.release()
        if self.advert_time:
            self.check_adverts()

    def update_screenshot(self, screenshot):
        """ Updates the screenshot everytime the main loop is ready to update """
        self._lock.acquire()
        self.screenshot = screenshot
        self._lock.release()

    def start(self):
        self._stopped = False
        t = Thread(target=self.run)
        t.start()

    def stop(self):
        self._stopped = True

    # Main logic controller
    def run(self):
        while not self._stopped:
            # TODO: Add facing classification so we know which way we're facing. Some of these functions are no use
            #  if not facing forward
            if self.state == BotState.INITIALISING:
                # Don't do bot actions before initialising has completed
                if time() > (self.init_timestamp + self.INITIALISING_SECONDS):
                    self._lock.acquire()
                    self.state = BotState.WATCHING
                    self._lock.release()
            elif self.state == BotState.WATCHING:
                self.score_screens()
                self.censor()

                if self.current_screen and self.indicator_colors[self.current_screen] == IndicatorColors.BLACK:
                    pass
                elif (
                        # TODO: This is messy and needs a cleanup
                        not self.current_screen
                        # Check if we're currently red
                        or self.indicator_colors[self.current_screen] == IndicatorColors.RED
                        # Check if we're over maximum cut time and if there's a time limit
                        or self.get_cut_time() > self.MAXIMUM_CUT_TIME and self.time_limit
                        or self.get_cut_time() >= self.OPTIMAL_CUT_TIME
                        or (self.OPTIMAL_CUT_TIME > self.get_cut_time() > self.MAXIMUM_CUT_TIME
                            and random.randint(1, 3) == 1)
                        or (self.time_limit and random.uniform(self.OPTIMAL_CUT_TIME, self.MAXIMUM_CUT_TIME) >
                            self.get_cut_time())
                ):
                    possible_shots = [(shot, self.screen_values[shot]) for shot in self.screen_values
                                      if self.screen_values[shot] > 0]
                    if len(possible_shots) > 2:
                        # If there's more than 1 decent shot, we can assume there's a time limit on the level
                        self._lock.acquire()
                        self.time_limit = True
                        self._lock.release()
                        shot = max(possible_shots, key=lambda x: x[1])[0]  # Selects the highest scoring camera index
                    else:
                        # If there's only one shot, we don't want the bot to go cutting around for just anything
                        self._lock.acquire()
                        self.time_limit = False
                        self._lock.release()
                        if possible_shots:
                            shot = max(possible_shots, key=lambda x: x[1])[0]
                        else:
                            shot = self.current_screen
                    if (
                            # TODO: This is messy and needs cleanup
                            self.current_screen is None or (
                            self.current_screen is not None and (
                            self.indicator_colors[self.current_screen] == IndicatorColors.RED
                            or self.indicator_colors[self.current_screen] == IndicatorColors.BLACK)
                            or (self.indicator_colors[self.current_screen] == IndicatorColors.BLUE
                                and self.get_cut_time() >= self.MINIMAL_CUT_TIME))
                            or (self.get_cut_time() >= self.OPTIMAL_CUT_TIME and self.time_limit)
                            or (self.get_cut_time() > self.OPTIMAL_CUT_TIME
                                and self.screen_values[shot] > self.screen_values[self.current_screen])
                    ):
                        if shot != self.current_screen:
                            self.make_cut(shot)

    def detect_indicators(self):
        """ Use CV2 to detect the color of each indicator. Currently not working correctly """
        # TODO: Fix this function. It doesn't seem to work right
        colors = [
            (self.LOWER_RED, self.UPPER_RED, IndicatorColors.RED),
            (self.LOWER_GREEN, self.UPPER_GREEN, IndicatorColors.GREEN),
            (self.LOWER_BLUE, self.UPPER_BLUE, IndicatorColors.BLUE)
        ]
        for index, (x, y) in enumerate(PixelsOfInterest.SCREEN_INDICATORS):
            found = False
            for color in colors:
                pixel = cv.inRange(self.screenshot_hsv, color[0], color[1])[int(y*self.HEIGHT_FACTOR), int(x*self.WIDTH_FACTOR)]
                if pixel == 255:
                    self.indicator_colors[index] = color[2]
                    found = True
                    break
            if not found:
                self.indicator_colors[index] = IndicatorColors.BLACK

    def score_screens(self):
        """ Based on the weights in self.indicator_colors, assign a score to each camera """
        # TODO: This function feels messy. I think there's a better way to do this
        self.detect_indicators()
        for camera, weight in self.indicator_colors.items():
            if self._stopped:
                break
            score = self.MAXIMUM_CUT_TIME
            if self.current_screen != camera:
                score += self.get_cut_time()
            else:
                # Making sure the score doesn't drop below 0 in case the indicator is black
                score = max(score - self.get_cut_time(), 0.1)
            score *= weight
            self._lock.acquire()
            self.screen_values[camera] = score
            self._lock.release()

    def make_cut(self, shot_index):
        """ Make a cut by pressing the correct button and update knowledge base """
        if self.DEBUG:
            prev_dur = self.get_cut_time()
        camera_name = str(shot_index + 1)
        pyautogui.keyDown(camera_name)
        pyautogui.keyUp(camera_name)
        self._lock.acquire()
        self.current_screen = shot_index
        self.last_cut = time()
        self._lock.release()
        if self.DEBUG:
            # noinspection PyUnboundLocalVariable
            print(f"Cut to Camera {camera_name}\nShot duration: {prev_dur}"
                  f"\nScore:{self.screen_values[self.current_screen]}"
                  f"\nIndicator is {self.INDICATOR_NAMES[self.indicator_colors[self.current_screen]]}"
                  f"\nScores available: {self.screen_values}"
                  f"\nWeights: {self.indicator_colors}")
            print("-" * 30)

    def censor(self):
        """ If index pixel is red, press spacebar, otherwise, let go of it"""
        # This doesn't work for political censorship but there's no need to implement that
        mask = cv.inRange(self.screenshot_hsv, self.LOWER_RED, self.UPPER_RED)
        censor_pixel = mask[int(PixelsOfInterest.CENSOR_WAVEFORM[1] *
                            self.HEIGHT_FACTOR), int(PixelsOfInterest.CENSOR_WAVEFORM[0]*self.WIDTH_FACTOR)]
        if censor_pixel == 255:
            pyautogui.keyDown("space")
        else:
            pyautogui.keyUp("space")

    def get_cut_time(self):
        """ Returns the number of seconds since the last cut was made """
        return time() - self.last_cut

    def check_adverts(self):
        """ Cut to the ads when it's time to do so. No need to check which are loaded, just push all buttons """
        if self.advert_time:
            # Time for an advert
            for button in ["z", "x", "c"]:
                # Just pushing every button. Saves having to check which adverts are loaded
                if self._stopped:
                    break
                pyautogui.keyDown(button)
                pyautogui.keyUp(button)
