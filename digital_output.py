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
file_handler = logging.FileHandler(os.path.join("logs", "digital_output.log"))
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def main():
    logger.debug(f"Program started")
    led = DigitalOutput(17)
    test_mode = 1
    time_of_last_test_change = perf_counter()
    while True:
        led.loop_output()
        if test_mode == 1:
            led.set_mode(DigitalOutput.MODE_ON)
        elif test_mode == 2:
            led.set_mode(DigitalOutput.MODE_BLINKING)
        else:
            led.set_mode(DigitalOutput.MODE_OFF)
        current_time = perf_counter()
        if current_time - time_of_last_test_change > 10.0:
            # change output mode after time passes
            test_mode += 1
            if test_mode > 2:
                test_mode = 0
            time_of_last_test_change = current_time
        time.sleep(0.01)


class DigitalOutput:
    MODE_OFF = 0
    MODE_ON = 1
    MODE_BLINKING = 2

    def __init__(self, pin):
        """
        :param pin: digital output number
        """
        self.mode = self.MODE_OFF
        self.output_state = False
        self.pin = pin
        self.setup_do()
        self.last_switch_time = 0.0
        self.blink_period_s = 1.0

    # must be called from main
    def loop_output(self):
        """
        Must be called from main in regular intervals to activate the output
        """
        if self.mode == self.MODE_OFF:
            self.set_output(False)
        elif self.mode == self.MODE_ON:
            self.set_output(True)
        elif self.mode == self.MODE_BLINKING:
            current_time = perf_counter()
            time_passed_since_last_change = current_time - self.last_switch_time
            if time_passed_since_last_change >= self.blink_period_s:
                if self.output_state:
                    self.set_output(False)
                else:
                    self.set_output(True)
                self.last_switch_time = current_time

    def set_blink_period(self, blink_period):
        """
        for blinking mode
        :param blink_period: how often to change the led state when blinking
        :return:
        """
        self.blink_period_s = blink_period

    def toggle_output(self):
        # for using outside of class
        if self.mode == self.MODE_ON or self.mode == self.MODE_BLINKING:
            self.set_mode(self.MODE_OFF)
        else:
            self.set_mode(self.MODE_ON)

    def set_mode(self, mode):
        # for using outside of class
        if self.MODE_OFF <= mode <= self.MODE_BLINKING:
            self.mode = mode
        else:
            logger.error("Invalid button mode set")

    def set_output(self, off_on):
        """
        Only call from within the  class
        :param off_on: determine if output should be on or off
        :return:
        """
        if off_on:
            # output should be off
            if not self.output_state:
                # switch output only if needed
                GPIO.output(self.pin, GPIO.HIGH)
                self.output_state = True
        else:
            # output should be off
            if self.output_state:
                # switch output only if needed
                GPIO.output(self.pin, GPIO.LOW)
                self.output_state = False

    def setup_do(self):
        # setup digital output
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)


if __name__ == '__main__':
    main()
