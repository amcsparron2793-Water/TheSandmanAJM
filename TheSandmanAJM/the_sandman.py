from datetime import datetime
from logging import getLogger, Logger
from time import sleep
from typing import Union

from tqdm import tqdm


class _TimerFormatting:
    MINUTES = 'minute(s)'
    SECONDS = 'second(s)'
    TIME_STRING_BASE = '{} {}'

    @classmethod
    def time_calculated_string(cls, time_seconds: Union[int, float]):
        time_calculated = time_seconds // 60 if time_seconds >= 60 else time_seconds
        suffix = cls.MINUTES if time_seconds >= 60 else cls.SECONDS
        return time_calculated, suffix

    @classmethod
    def format_time_string(cls, time_seconds: Union[int, float], format_args=()):
        time_calculated, suffix = cls.time_calculated_string(time_seconds)
        return (cls.TIME_STRING_BASE.format(time_calculated, *format_args) + suffix).strip()


class TheSandman(_TimerFormatting):
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
    TIME_STRING_BASE = 'Sleeping for {} {} '

    def __init__(self, sleep_time_seconds=None, **kwargs):
        self.sleep_time_start = None
        self.use_visual_sleep = kwargs.get('use_visual_sleep', self.__class__.DEFAULT_USE_VISUAL_SLEEP)
        self.silent_sleep = kwargs.get('silent_sleep', self.__class__.DEFAULT_SILENT_SLEEP)

        self.sleep_time: int = sleep_time_seconds or self.__class__.DEFAULT_SLEEP_TIME_SECONDS
        self._is_time_remaining = False
        self._sleep_time_string = None

        self.logger: Logger = kwargs.get('logger', getLogger(__name__))
        self.sleep_time_string = self.sleep_time
        self.logger.info(f'{self.__class__.__name__} initialized - {self.sleep_time_string} when called')

    @classmethod
    def format_time_string(cls, sleep_time_seconds: int, more: str = ''):
        return super().format_time_string(sleep_time_seconds, {more})

    def _needs_more_str_check(self) -> str:
        if self._is_time_remaining:
            more = 'more'
        else:
            more = ''
        return more

    def sleep_time_with_start_string(self, sleep_time_string):
        if self.sleep_time_start:
            str_parts = [sleep_time_string, f'(started at {self.sleep_time_start})']
            return ' '.join(str_parts)
        self.logger.debug(f"sleep_time_start is None, no need to add start time to string, returning: {sleep_time_string}")
        return sleep_time_string

    @property
    def sleep_time_string(self):
        """
        This property returns the string representation of the sleep time. The
        sleep time is represented as a string based on the underlying internal
        attribute.

        :return: A string representing the sleep time.
        :rtype: str
        """
        return self._sleep_time_string

    @sleep_time_string.setter
    def sleep_time_string(self, time_value_seconds: int):
        more = self._needs_more_str_check()
        sts = self.format_time_string(time_value_seconds, more)
        self._sleep_time_string = self.sleep_time_with_start_string(sts)

    def _setup_sleep_in_rounds(self, **kwargs):
        """
        Configures sleep behavior for the current operation round.

        This method initializes or adjusts sleep configuration parameters based on the
        current operational mode. It sets the start time, determines whether sleep
        notifications should be printed, and flags whether time remains for the current
        cycle. The returned dictionary of keyword arguments reflects these updated
        settings.

        :param kwargs: Keyword arguments to configure sleep parameters. The content of
            this dictionary is modified based on the current configuration and returned
            with updated values.
        :return: Updated keyword arguments reflecting sleep configuration adjustments.
        """
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
        """
        Executes a sleep process divided into multiple rounds. In each round, specific
        parameters from the `kwargs` are utilized to configure the sleep behavior. The
        process involves iterating through the specified number of rounds and invoking
        a helper function to handle each round.

        :param rounds: Number of rounds to execute the sleep process. Defaults to 2.
        :type rounds: int
        :param kwargs: Additional configuration parameters for the sleep behavior.
        :type kwargs: dict
        """
        kwargs = self._setup_sleep_in_rounds(**kwargs)

        for sleep_round in range(rounds):
            self._sleep_round(sleep_round, rounds, **kwargs)

    def _basic_log_or_print_sleep_time_string(self, **kwargs):
        print_msg = kwargs.get('print_msg', False)
        has_usable_logger = hasattr(self, 'logger') and self.logger.hasHandlers()

        print_by_default = (not self.silent_sleep
                            and not has_usable_logger
                            and not self.use_visual_sleep)

        if has_usable_logger:
            self.logger.info(self.sleep_time_string, **kwargs)
        if print_by_default or print_msg:
            print(self.sleep_time_string)

    def visual_sleep(self, sleep_time_seconds: int) -> None:
        """
        Pauses the execution of the program for the given number of seconds while providing
        a visual progress indicator using a progress bar.

        :param sleep_time_seconds: The number of seconds to pause execution.
        :type sleep_time_seconds: int
        :return: None
        :rtype: None

        :raises Exception: If an error occurs during execution, logs the error and disables
            the visual progress indicator before attempting a standard sleep operation.
        :raises KeyboardInterrupt: If the operation is interrupted by the user, propagates
            the exception to terminate execution.
        """
        try:
            for _ in tqdm(range(sleep_time_seconds),
                          desc=f"{self.sleep_time_string}",
                          unit="second",
                          disable=self.silent_sleep):
                sleep(1)
        # pylint: disable=broad-except
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
