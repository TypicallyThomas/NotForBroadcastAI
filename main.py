import globalVariable
import configparser
import cv2 as cv
from windowcapture import WindowCapture
from detection import Detection
from bot import AlexBot

# Read config file and set it to global variables
config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")
globalVariable.set_value('screenRes',
                         (config.getint('AlexBot', 'screenWidth'),
                          config.getint('AlexBot', 'screenHeight')))
globalVariable.set_value('windowRes',
                         (config.getint('AlexBot', 'windowWidth'),
                          config.getint('AlexBot', 'windowHeight')))
globalVariable.set_value('originRes',
                         (config.getint('AlexBot', 'originalWindowWidth'),
                          config.getint('AlexBot', 'originalWindowHeight')))
globalVariable.set_value('width_factor',
                         globalVariable.get_value('windowRes')[0] /
                         globalVariable.get_value('originRes')[0])
globalVariable.set_value('height_factor',
                         globalVariable.get_value('windowRes')[1] /
                         globalVariable.get_value('originRes')[1])
globalVariable.set_value('channel_threshold',
                         config.getint('AlexBot', 'channelThreshold'))
globalVariable.set_value('DEBUG',
                         config.getboolean('AlexBot', 'DEBUG'))

# Initialise WindowCapture
# TODO: This is not accurate. You'll need to right-click the window border, select move, press the up key once, and press enter.
x1 = int(globalVariable.get_value('screenRes')[0]/2 -
         globalVariable.get_value('windowRes')[0]/2)
x2 = int(globalVariable.get_value('screenRes')[0]/2 +
         globalVariable.get_value('windowRes')[0]/2)
y1 = int(globalVariable.get_value('screenRes')[1]/2 -
         globalVariable.get_value('windowRes')[1]/2)
y2 = int(globalVariable.get_value('screenRes')[1]/2 +
         globalVariable.get_value('windowRes')[1]/2)

wincap = WindowCapture(bbox=(x1, y1, x2, y2))  # bbox allows for cropping

# Debug
DEBUG = globalVariable.get_value('DEBUG')

# Initialise bot
bot = AlexBot()

# Initialise detection
detector = Detection()

# Threads
wincap.start()
bot.start()
detector.start()

while True:
    # Make sure there's a new screenshot ready
    if wincap.screenshot is None:
        continue

    # Update the detector
    detector.update_screenshot(wincap.screenshot)

    # Update the bot
    bot.update_adverts(detector.advert_time)
    bot.update_screenshot(wincap.screenshot)

    if DEBUG:
        cv.imshow("Debug", wincap.screenshot)

    key = cv.waitKey(1)
    if key == ord("q"):
        bot.stop()
        detector.stop()
        wincap.stop()
        cv.destroyAllWindows()
        break

if DEBUG:
    print("Done")
