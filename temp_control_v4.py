from gpiozero import CPUTemperature
import RPi.GPIO as GPIO
from threading import Timer
import time
from datetime import datetime
import logging
import os

# Setup logging
log_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.NOTSET)
# File logger
file_handler = logging.FileHandler(os.path.join("logs", "temperature_control.log"))
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)
logger.addHandler(file_handler)


def main():
    logger.info(f"Program started")
    try:
        temp_control = TempControl(fan_on_t=45.0, hyst=12.0, fan_on_t_night=60.0, hyst_night=24.0, fan_pin=21,
                                   temp_check_interval_s=5.0)
        temp_control.start_cooling()
        while True:
            # To catch the keyboard interrupt the main thread has to be kept running
            time.sleep(999)
    except KeyboardInterrupt:
        logger.info(f"Program stopped by keyboard interrupt")
        # print("Program stopped")
        temp_control.stop()
        GPIO.cleanup()


class TempControl:
    """
    Class for controlling raspberry pi fan depending on CPU temperature.
    """
    LOG_FILE_NAME = "temp_log.txt"
    LOG_FREQUENCY_EVERY_CHECK = 6  # temp check interval x this is how frequent the log is written4
    NIGHT_START_HOUR = 22
    NIGHT_END_HOUR = 8

    def __init__(self, fan_on_t: float, hyst: float, fan_on_t_night: float, hyst_night: float,
                 fan_pin: int, temp_check_interval_s: float):
        """
        :param fan_on_t: t° above which the fan will be turned on
        :param hyst: fan_on_t - hyst will be the temp at which fan turned off
        :param fan_on_t_night: seperate set of settings for night so the PI does not make sound so often
        :param hyst_night:
        :param fan_pin: digital output to which the fan is connected. DO NOT CONNECT DIRRECTLY - use a transistor
        or relay
        :param temp_check_interval_s: how often to chech CPU temperature
        """
        # temp levels for turning fan on or off
        self.fan_on_t = fan_on_t
        self.hyst = hyst
        # temp levels for turning fan on or off during night, quiet mode
        self.fan_on_t_night = fan_on_t_night
        self.hyst_night = hyst_night
        # current status of fan
        self.fan_on = False
        self.caluclate_off_t()
        # digital output for controlling of fan
        self.fan_pin = fan_pin
        self.temp_check_interval_s = temp_check_interval_s
        self.setup_pin()
        self.stop_flag = False
        # determines when temperatures should be logged in seperate file
        self.log_cntr = 0

    def start_cooling(self):
        # starts the repeated temperature check thread
        self.check_thread = Timer(self.temp_check_interval_s, self.check_t_repeated)
        self.check_thread.start()

    def setup_pin(self):
        # setup digital output
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.fan_pin, GPIO.OUT)

    def stop(self):
        # stop program
        self.stop_flag = True
        self.check_thread.cancel()

    def check_t_repeated(self):
        # method that calls itself repeatedly to check the CPU temperature and turn on off the fan
        cpu = CPUTemperature()
        cpu_t = cpu.temperature
        current_hour = datetime.now().hour
        # use different settings depending on whether it is night or not
        if self.NIGHT_START_HOUR <= current_hour or \
                self.NIGHT_END_HOUR >= current_hour:
            # night
            on_t = self.fan_on_t_night
            off_t = self.off_t_night
        else:
            # day
            on_t = self.fan_on_t
            off_t = self.off_t
        if cpu_t >= on_t:
            GPIO.output(self.fan_pin, GPIO.HIGH)
            self.fan_on = True
        elif cpu_t < off_t:
            self.fan_on = False
            GPIO.output(self.fan_pin, GPIO.LOW)
        if not self.stop_flag:
            self.check_thread = Timer(self.temp_check_interval_s, self.check_t_repeated)
            self.check_thread.start()
        self.log_temperature(cpu_t, self.fan_on)

    def set_hyst(self, new_hyst: float, new_hyst_night: float):
        """
        Change hysteresis settings
        :param new_hyst:
        :param new_hyst_night:
        :return:
        """
        self.hyst = new_hyst
        self.hyst_night = new_hyst_night
        self.caluclate_off_t()

    def set_on_t(self, new_on_t: float, new_on_t_night: float):
        """
        Change turn on setting settings
        :param new_on_t:
        :param new_on_t_night:
        :return:
        """
        self.fan_on_t = new_on_t
        self.fan_on_t_night = new_on_t_night
        self.caluclate_off_t()

    def caluclate_off_t(self):
        # calculate the temperatures at which the fan will be turned off
        self.off_t = self.fan_on_t - self.hyst
        self.off_t_night = self.fan_on_t_night - self.hyst_night

    def log_temperature(self, temp, fan_on_off):
        """
        Lof fan tempearature in a file
        :param temp: degrees to log
        :param fan_on_off: fan is on or off
        :return:
        """
        if (self.log_cntr % self.LOG_FREQUENCY_EVERY_CHECK) == 0:
            # log every N time
            cur_time = self.get_time_date_string()
            try:
                with open(self.LOG_FILE_NAME, "a+") as f:
                    f.write(f"{cur_time}, {temp}, {fan_on_off}\n")
            except IOError as e:
                logging.exception("IOError when logging temperature")
            except:  # handle other exceptions
                logging.exception("Other error when logging temperature")
        self.log_cntr += 1

    def get_time_date_string(self):
        """
        :return: current date and time as string like this : 2022_02_31_19_30_05
        """
        today = datetime.now()
        current_date = today.strftime("%Y_%m_%d")
        current_time = today.strftime("%H_%M_%S")
        string = f"{current_date}_{current_time}"
        return string


if __name__ == '__main__':
    main()
