import time
from time import perf_counter
import random
from digital_output import DigitalOutput
from digital_input import ButtonDi
import logging
import os

# Setup logging
log_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)
# File logger
file_handler = logging.FileHandler(os.path.join("logs", "digital_output.log"))
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def main():
    logger.debug(f"Program started")
    cntrl = PiButtonLed()
    cntrl.main_loop()


class PiButtonLed:
    """
    Class for acting on digital input presses by blinking led
    """
    RANDOM_BLINK_TIMES = [0.1, 0.5, 1.0, 2.0]

    def __init__(self):
        self.btn = ButtonDi(4)
        self.led = DigitalOutput(17)

    def main_loop(self):
        while True:
            press_type = self.btn.loop_input()
            self.act_on_btn_press(press_type)
            self.led.loop_output()
            time.sleep(0.01)

    def act_on_btn_press(self, press_type):
        if press_type != ButtonDi.PRESS_TYPE_NONE:
            if press_type == ButtonDi.PRESS_TYPE_SHORT:
                print("Short press")
                self.led.toggle_output()
            elif press_type == ButtonDi.PRESS_TYPE_LONG:
                value_to_set = random.choice(self.RANDOM_BLINK_TIMES)
                self.led.set_blink_period(value_to_set)
                print("Long press")
            elif press_type == ButtonDi.PRESS_TYPE_DOUBLE:
                self.led.set_mode(DigitalOutput.MODE_BLINKING)
                print("Double press")


if __name__ == '__main__':
    main()
