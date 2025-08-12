"""Package inspects Python modules and extracts complete descriptions of code."""

import logging
import sys


def silence_module_logger():
    """Silence loggers from imported modules."""
    n_enabled = len(list(logging.Logger.manager.loggerDict.keys()))
    for log_name, log_obj in logging.Logger.manager.loggerDict.items():
        log_obj = logging.getLogger(log_name)
        if (
            log_name != logger.name
            and hasattr(log_obj, "propagate")
            and log_obj.propagate
        ):
            logger.debug(f">>>>> disabling logger: {log_name}")
            log_obj.propagate = False
            n_enabled -= 1
    return n_enabled


class CustomFormatter(logging.Formatter):
    """Format the logging."""

    high = "\x1b[34;1m"
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    base_format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s "
        + "(%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: high + base_format + reset,
        logging.INFO: grey + base_format + reset,
        logging.WARNING: yellow + base_format + reset,
        logging.ERROR: red + base_format + reset,
        logging.CRITICAL: bold_red + base_format + reset,
    }

    def format(self, record):
        """Define the format."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%dT%H:%M:%S")
        return formatter.format(record)


# create console handler with a higher log level
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(CustomFormatter())

ch2 = logging.StreamHandler(sys.stderr)
ch2.setLevel(logging.ERROR)
ch2.setFormatter(CustomFormatter())

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(ch)
logger.addHandler(ch2)
logger.name = "dlg_paletteGen"
