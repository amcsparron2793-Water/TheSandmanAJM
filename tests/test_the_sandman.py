import pytest
from unittest.mock import patch, MagicMock
from TheSandmanAJM.the_sandman import TheSandman


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def sandman(mock_logger):
    return TheSandman(sleep_time_seconds=10, logger=mock_logger)


def test_initialization_defaults():
    ts = TheSandman()
    assert ts.sleep_time == ts.__class__.DEFAULT_SLEEP_TIME_SECONDS
    assert ts.use_visual_sleep is ts.__class__.DEFAULT_USE_VISUAL_SLEEP
    assert ts.silent_sleep is ts.__class__.DEFAULT_SILENT_SLEEP


def test_initialization_custom():
    ts = TheSandman(sleep_time_seconds=30, use_visual_sleep=False, silent_sleep=True)
    assert ts.sleep_time == 30
    assert ts.use_visual_sleep is False
    assert ts.silent_sleep is True


def test_sleep_time_string_seconds(sandman):
    sandman.sleep_time_start = "2026-08-23 14:30"
    sandman.sleep_time_string = 45
    assert "sleeping for 45  second(s)" in sandman.sleep_time_string
    assert "(started at 2026-08-23 14:30)" in sandman.sleep_time_string


def test_sleep_time_string_minutes(sandman):
    sandman.sleep_time_start = "2026-08-23 14:30"
    sandman.sleep_time_string = 125
    assert "sleeping for 2  minute(s)" in sandman.sleep_time_string


def test_sleep_time_string_with_remaining(sandman):
    sandman.sleep_time_start = "2026-08-23 14:30"
    sandman._is_time_remaining = True
    sandman.sleep_time_string = 30
    assert "sleeping for 30 more second(s)" in sandman.sleep_time_string


def test_setup_sleep_in_rounds(sandman):
    kwargs = sandman._setup_sleep_in_rounds(extra="data")
    assert sandman.sleep_time_start is not None
    assert sandman._is_time_remaining is False
    assert kwargs['extra'] == "data"
    # Since use_visual_sleep is True by default, print_msg should be False
    assert kwargs['print_msg'] is False


@patch('TheSandmanAJM.the_sandman.sleep')
@patch('builtins.print')
def test_sleep_non_visual(mock_print, mock_sleep, sandman, mock_logger):
    sandman.use_visual_sleep = False
    sandman.silent_sleep = False
    mock_logger.hasHandlers.return_value = False

    sandman.sleep(5)
    mock_sleep.assert_called_once_with(5)
    # If logger is present and has handlers, it will log instead of print.
    # The sandman fixture uses mock_logger.
    mock_logger.info.assert_called()
    mock_print.assert_called()


@patch('TheSandmanAJM.the_sandman.TheSandman.visual_sleep')
def test_sleep_visual_calls_visual_sleep(mock_visual_sleep, sandman):
    sandman.use_visual_sleep = True
    sandman.sleep(5)
    mock_visual_sleep.assert_called_once_with(5)


@patch('TheSandmanAJM.the_sandman.tqdm')
@patch('TheSandmanAJM.the_sandman.sleep')
def test_visual_sleep(mock_sleep, mock_tqdm, sandman):
    # Mock tqdm to return a mock range
    mock_tqdm.return_value = range(5)
    sandman.visual_sleep(5)
    assert mock_sleep.call_count == 5
    mock_tqdm.assert_called_once()


@patch('TheSandmanAJM.the_sandman.TheSandman.sleep')
def test_sleep_in_rounds(mock_ts_sleep, sandman):
    sandman.sleep_time = 30
    sandman.sleep_in_rounds(rounds=3)
    assert mock_ts_sleep.call_count == 3
    # 30 // 3 = 10
    mock_ts_sleep.assert_called_with(10, print_msg=False)


@patch('TheSandmanAJM.the_sandman.tqdm')
@patch('TheSandmanAJM.the_sandman.TheSandman.sleep')
def test_visual_sleep_exception_fallback(mock_ts_sleep, mock_tqdm, sandman, mock_logger):
    mock_tqdm.side_effect = Exception("tqdm error")
    sandman.use_visual_sleep = True
    sandman.visual_sleep(5)
    assert sandman.use_visual_sleep is False
    mock_ts_sleep.assert_called_once_with(5)
    mock_logger.error.assert_called()
    assert sandman.use_visual_sleep is False


@patch('TheSandmanAJM.the_sandman.sleep')
def test_silent_sleep_still_logs(mock_sleep, mock_logger):
    # Test that silent_sleep does NOT affect logging if logger has handlers
    mock_logger.hasHandlers.return_value = True
    ts = TheSandman(sleep_time_seconds=10, logger=mock_logger, silent_sleep=True, use_visual_sleep=False)
    # The init log should have happened
    assert mock_logger.info.call_count >= 1

    ts.sleep(5)
    # The sleep log should also happen
    mock_logger.info.assert_called()


@patch('TheSandmanAJM.the_sandman.tqdm')
def test_visual_sleep_keyboard_interrupt(mock_tqdm, sandman):
    mock_tqdm.side_effect = KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):
        sandman.visual_sleep(5)


@patch('builtins.print')
@patch('TheSandmanAJM.the_sandman.sleep')
def test_basic_log_or_print_no_logger(mock_sleep, mock_print):
    # Test print when logger has no handlers
    ts = TheSandman(sleep_time_seconds=10, use_visual_sleep=False)
    # By default, logger might have handlers (e.g. if root logger is configured)
    # We want to force it to NOT use logger.
    ts.logger = MagicMock()
    ts.logger.hasHandlers.return_value = False

    ts.sleep(5, print_msg=True)
    mock_print.assert_called()


def test_sleep_in_rounds_single_round(sandman):
    with patch.object(TheSandman, 'sleep') as mock_sleep:
        sandman.sleep_time = 10
        sandman.sleep_in_rounds(rounds=1)
        mock_sleep.assert_called_once_with(10, print_msg=False)


@patch('builtins.print')
@patch('TheSandmanAJM.the_sandman.sleep')
def test_basic_log_or_print_with_usable_logger(mock_sleep, mock_print, mock_logger):
    # Test that logger is used if it has handlers
    ts = TheSandman(sleep_time_seconds=10, logger=mock_logger, use_visual_sleep=False)
    mock_logger.hasHandlers.return_value = True
    ts.sleep(5)
    mock_logger.info.assert_called()
    mock_print.assert_not_called()


@patch('TheSandmanAJM.the_sandman.tqdm')
@patch('TheSandmanAJM.the_sandman.sleep')
def test_visual_sleep_silent(mock_sleep, mock_tqdm, sandman):
    sandman.silent_sleep = True
    sandman.visual_sleep(5)
    mock_tqdm.assert_called_once()
    # Check that disable=True was passed to tqdm
    args, kwargs = mock_tqdm.call_args
    assert kwargs['disable'] is True
