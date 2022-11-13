import RPi.GPIO as GPIO
import time
from time import perf_counter
import logging
import os

# Setup logging
log_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)
# File logger
file_handler = logging.FileHandler(os.path.join("logs", "digital_input.log"))
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def main():
    logger.debug(f"Program started")
    btn = ButtonDi(4)
    while True:
        press_type = btn.loop_input()
        if press_type != ButtonDi.PRESS_TYPE_NONE:
            if press_type == ButtonDi.PRESS_TYPE_SHORT:
                print("Short press")
            elif press_type == ButtonDi.PRESS_TYPE_LONG:
                print("Long press")
            elif press_type == ButtonDi.PRESS_TYPE_DOUBLE:
                print("Double press")
        time.sleep(0.01)


class ButtonDi:
    """
    Digital input class for Raspberry PI button
    Can differentiate between short press, long press and double press
    """
    SHORT_PRESS_TIME_S = 0.1
    DOUBLE_PRESS_PAUSE_TIME_MAX_S = 0.3
    LONG_PRESS_TIME_S = 1.0
    DEBOUNCE_TIME_S = 0.05
    PRESS_TYPE_NONE = 0
    PRESS_TYPE_SHORT = 1
    PRESS_TYPE_LONG = 2
    PRESS_TYPE_DOUBLE = 3

    def __init__(self, pin):
        """
        :param pin: digital input number on Pi
        """
        self.pin = pin
        self.setup_di()
        self.analysing_press = False
        self.time_of_current_state_change = 0.0
        self.time_of_previous_state_change = 0.0
        self.time_of_last_let_go = 0.0
        self.debouncing = False
        self.double_press_start = False
        self.old_btn_state = GPIO.input(self.pin)

    def loop_input(self):
        """
        Must be called from main in regular intervals to detect presses
        :return: press type - see constants
        """
        current_btn_state = GPIO.input(self.pin)
        press_type = self.PRESS_TYPE_NONE
        if not self.debouncing and current_btn_state != self.old_btn_state:
            time_of_current_state_change = perf_counter()
            self.debouncing = True
            if not current_btn_state:
                # btn released
                press_time = time_of_current_state_change - self.time_of_previous_state_change
                if not self.double_press_start and press_time >= self.LONG_PRESS_TIME_S:
                    logger.debug("LONG PRESS")
                    press_type = self.PRESS_TYPE_LONG
                elif self.double_press_start:
                    # first press of double press was executed before
                    logger.debug("DOUBLE PRESS")
                    press_type = self.PRESS_TYPE_DOUBLE
                    self.double_press_start = False
                else:
                    # Short press executed, now waiting if this will be a double press
                    self.analysing_press = True
                    self.time_of_last_let_go = time_of_current_state_change
            elif self.analysing_press:
                # btn pressed and a press was registered before as well
                self.double_press_start = True
                self.analysing_press = False
            # save old state and time
            self.old_btn_state = current_btn_state
            self.time_of_previous_state_change = time_of_current_state_change
        elif self.debouncing:
            current_time = perf_counter()
            time_passed_since_debounce_start = current_time - self.time_of_current_state_change
            if time_passed_since_debounce_start > self.DEBOUNCE_TIME_S:
                # end of debounce
                self.debouncing = False
        if self.analysing_press:
            # wait before considering a short press to allow the user to execute double press
            current_time = perf_counter()
            time_passed_since_let_go = current_time - self.time_of_last_let_go
            if time_passed_since_let_go > self.DOUBLE_PRESS_PAUSE_TIME_MAX_S:
                # the btn was not pressed again consider as short press
                press_type = self.PRESS_TYPE_SHORT
                logger.debug("SHORT PRESS")
                self.analysing_press = False
        return press_type

    def setup_di(self):
        # setup digital input
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


if __name__ == '__main__':
    main()
