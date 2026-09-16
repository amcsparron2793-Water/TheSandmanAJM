from datetime import datetime
from logging import getLogger, Logger
from time import sleep

from tqdm import tqdm


class TheSandman:
    """
        A utility class to facilitate and log time delays with custom sleep durations.

        Attributes:
            DEFAULT_SLEEP_TIME_SECONDS (int): Default sleep duration in seconds if not specified.
            sleep_time (int): Actual sleep time (in seconds) to be used by the instance.
            sleep_time_string (str): Human-readable string representing the current sleep duration.
            logger (Logger): Logging instance for logging messages related to sleep operations.

        Methods:
            sleep_time_string:
                Property getter and setter for updating the human-readable sleep time string.

            sleep_round():
                Splits the sleep duration into two equal parts. It logs and prints messages depicting the current sleep state, including the remaining time, and sleeps for the given durations.
    """
    # default 600 secs = 10 minutes
    DEFAULT_SLEEP_TIME_SECONDS = 600
    DEFAULT_USE_VISUAL_SLEEP = True
    DEFAULT_SILENT_SLEEP = False

    def __init__(self, sleep_time_seconds=None, **kwargs):
        self.sleep_time_start = None
        self.use_visual_sleep = kwargs.get('use_visual_sleep', self.__class__.DEFAULT_USE_VISUAL_SLEEP)
        self.silent_sleep = kwargs.get('silent_sleep', self.__class__.DEFAULT_SILENT_SLEEP)

        self.sleep_time: int = sleep_time_seconds or self.__class__.DEFAULT_SLEEP_TIME_SECONDS
        self._is_time_remaining = False
        self._sleep_time_string = None

        self.logger: Logger = kwargs.get('logger', getLogger(__name__))
        self.sleep_time_string = self.sleep_time
        self.logger.info(f'TheSandman initialized - sleep time set as {self.sleep_time_string}')

    @property
    def sleep_time_string(self):
        return self._sleep_time_string

    @sleep_time_string.setter
    def sleep_time_string(self, value: int):
        if self._is_time_remaining:
            more = 'more'
        else:
            more = ''
        if value >= 60:
            self._sleep_time_string = f'sleeping for {value // 60} {more} minute(s)'
        else:
            self._sleep_time_string = f'sleeping for {value} {more} second(s)'

        str_parts = [self._sleep_time_string, f'(started at {self.sleep_time_start})']
        self._sleep_time_string = ' '.join(str_parts)

    def _setup_sleep_in_rounds(self, **kwargs):
        self.sleep_time_start = datetime.now().strftime('%m/%d/%Y %H:%M')
        if self.use_visual_sleep or self.silent_sleep:
            kwargs['print_msg'] = False
        else:
            kwargs['print_msg'] = True
        self._is_time_remaining = False
        return kwargs

    def _sleep_round(self, curr_sleep_round: int, total_rounds: int, print_msg: bool, **kwargs):
        if curr_sleep_round == total_rounds - 1:
            self._is_time_remaining = True
        sleep_time_seconds = (self.sleep_time // total_rounds)
        self.sleep(sleep_time_seconds, print_msg=print_msg, **kwargs)

    def sleep_in_rounds(self, rounds=2, **kwargs):
        kwargs = self._setup_sleep_in_rounds(**kwargs)

        for sleep_round in range(rounds):
            self._sleep_round(sleep_round, rounds, **kwargs)

    def _basic_log_or_print_sleep_time_string(self, **kwargs):
        print_msg = kwargs.get('print_msg', False)
        has_usable_logger = hasattr(self, 'logger') and self.logger.hasHandlers()
        if has_usable_logger:
            self.logger.info(self.sleep_time_string, **kwargs)
        if (print_msg and not self.silent_sleep) and not has_usable_logger:
            print(self.sleep_time_string)

    def visual_sleep(self, sleep_time_seconds: int) -> None:
        try:
            for _ in tqdm(range(sleep_time_seconds),
                          desc=f"{self.sleep_time_string}",
                          unit="second"):
                sleep(1)
        except Exception as e:
            if e.__class__.__name__ != 'KeyboardInterrupt':
                self.logger.error(f"visual_sleep failed: {e}, turning off visual sleep and trying again...")
                self.use_visual_sleep = False
                self.sleep(sleep_time_seconds)
            else:
                raise

    def sleep(self, sleep_time_seconds: int, **kwargs):
        """
        :param sleep_time_seconds: The number of seconds the function should pause execution.
        :type sleep_time_seconds: int
        :return: None
        :rtype: None
        """

        self.sleep_time_string = self.sleep_time if not self._is_time_remaining else sleep_time_seconds
        self._basic_log_or_print_sleep_time_string(**kwargs)

        if self.use_visual_sleep:
            self.visual_sleep(sleep_time_seconds)
        else:
            sleep(sleep_time_seconds)


if __name__ == '__main__':
    ts = TheSandman(sleep_time_seconds=30)
    ts.sleep_in_rounds(rounds=3)
