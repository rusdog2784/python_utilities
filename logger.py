import os
import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_custom_logger(logger_name: str, log_file_directory: Path = None, backup_days: int = 7):
    """
    Creates a generic logger specific to my preferences. If a log file directory is
    provided, then a File Handler is added to the logger. Otherwise, this just
    creates a simple Stream Handler.
    :param logger_name: The name to give to the logger, which can be used to access
        the logger from anywhere.
    :param log_file_directory: (optional) A pathlib.Path object specifying the
        directory for where to create and keep the logger's log files. Logs are
        kept for 7 days and rotate at midnight using TimedRotatingFileHandler.
    :param backup_days: (optional) The number of days to keep log files. Default is 7 days.
    :return: A logging logger object.
    """
    # Create Formatter:
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')
    # Create Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    # Create Stream Handler:
    stream_handler = StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)
    # Create File Handler (if file_path is provided and exists):
    if log_file_directory and os.path.exists(log_file_directory):
        filename = logger_name if logger_name != "__main__" else f"custom-python-logfile-{datetime.utcnow().date()}"
        file_handler = TimedRotatingFileHandler(
            filename=Path(log_file_directory, f'{filename}.log'),
            when='midnight',
            backupCount=7
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    # Write to the logger to make sure things are working, then return the 
    return logger
