import board
from adafruit_apds9960.apds9960 import APDS9960
import digitalio


class Gesture():
    def __init__(self):
        i2c = board.I2C()
        apds = APDS9960(i2c)
        apds.enable_gesture = True
        apds.enable_proximity = True
        while True:
            print(apds.proximity())
            self.gesture_controls(apds)

    def gesture_controls(self, apds):
        # print("12345")
        gesture = apds.gesture()
        while gesture == 0:
            gesture = apds.gesture()
        print('Saw gesture: {0}'.format(gesture))
        # if gesture == 1:
        #      print("up")
        # elif gesture == 2:
        #     print("down")
        # elif gesture == 3:
        #     print("left")
        # elif gesture == 4:
        #     print("right")

if __name__ == "__main__": 
    gesture = Gesture()  