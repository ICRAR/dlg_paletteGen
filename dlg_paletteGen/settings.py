"""Set global values."""

import inspect
import logging
import sys
from enum import Enum

import numpy


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

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# logger = logging.getLogger()
logger.addHandler(ch)
logger.addHandler(ch2)


# these are our supported base types
VALUE_TYPES = {
    str: "String",
    int: "Integer",
    float: "Float",
    bool: "Boolean",
    list: "List",
    dict: "Dict",
}

SVALUE_TYPES = {k.__name__: v for k, v in VALUE_TYPES.items() if hasattr(k, "__name__")}

CVALUE_TYPES = {
    "array_like": "numpy.array",
    "arraylike": "numpy.array",
    numpy.ndarray.__name__: "numpy.array",
    numpy._globals._NoValueType.__name__: "Object",  # type: ignore
    inspect._empty: "None",
    "type": "Object",
    "any": "Object",
    "NoneType": "None",
    "builtins.NoneType": "None",
}

BLOCKDAG_DATA_FIELDS = [
    "inputPorts",
    "outputPorts",
    "applicationArgs",
    "category",
    "fields",
]


class Language(Enum):
    """Set Language defaults."""

    UNKNOWN = 0
    C = 1
    PYTHON = 2


DOXYGEN_SETTINGS = {
    "OPTIMIZE_OUTPUT_JAVA": "YES",
    "AUTOLINK_SUPPORT": "NO",
    "IDL_PROPERTY_SUPPORT": "NO",
    "EXCLUDE_PATTERNS": "*/web/*, CMakeLists.txt",
    "VERBATIM_HEADERS": "NO",
    "GENERATE_HTML": "NO",
    "GENERATE_LATEX": "NO",
    "GENERATE_XML": "YES",
    "XML_PROGRAMLISTING": "NO",
    "ENABLE_PREPROCESSING": "NO",
    "CLASS_DIAGRAMS": "NO",
}

# extra doxygen setting for C repositories
DOXYGEN_SETTINGS_C = {
    "FILE_PATTERNS": "*.h, *.hpp",
}

DOXYGEN_SETTINGS_PYTHON = {
    "FILE_PATTERNS": "*.py",
}
