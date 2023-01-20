import cv2 as cv
from windowcapture import WindowCapture
from detection import Detection
from bot import AlexBot

DEBUG = True

# Initialise WindowCapture
wincap = WindowCapture(bbox=(373, 221, 1546, 879))  # bbox allows for cropping

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
