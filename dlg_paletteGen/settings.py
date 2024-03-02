"""
Various settings and global values.
"""

import ast
import logging
import re
import sys
import typing
from enum import Enum
from typing import Any, Union

import numpy


class CustomFormatter(logging.Formatter):
    """
    Formatter for logging.
    """

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
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%dT%H:%M:%S")
        return formatter.format(record)


# create console handler with a higher log level
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

logger = logging.getLogger(__name__)
logger.addHandler(ch)


def cleanString(input_text: str) -> str:
    """
    Remove ANSI escape strings from input"

    :param input_text: string to clean

    :returns: str, cleaned string
    """
    # ansi_escape = re.compile(r'[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]')
    ansi_escape = re.compile(r"\[[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", input_text)


def convert_type_str(input_type: str = "") -> str:
    """
    Convert the string provided into a supported type string

    :param value_type: str, type string to be converted

    :returns: str, supported type string
    """
    if input_type in SVALUE_TYPES.values():
        return input_type
    value_type = (
        SVALUE_TYPES[input_type] if input_type in SVALUE_TYPES else f"{input_type}"
    )
    return value_type


def guess_type_from_default(default_value: typing.Any = "", raw=False):
    """
    Try to guess the parameter type from a default_value provided.

    The value can be of any type by itself, including a JSON string
    containing a complex data structure.

    :param default_value: any, the default_value
    :param raw: bool, return raw type object, rather than string

    :returns: str, the type of the value as a supported string
    """
    vt = None  # type: Union[str, Any]
    try:
        # we'll try to interpret what the type of the default_value is
        # using ast
        l: dict = {}
        try:
            eval(
                compile(
                    ast.parse(f"t = {default_value}"),
                    filename="",
                    mode="exec",
                ),
                l,
            )
            vtype = type(l["t"])
            if not isinstance(vtype, type):
                vt = l["t"]
            else:
                vt = vtype
        except (NameError, SyntaxError):
            vt = "String"
    except:  # noqa: E722
        return "Object"
    if not raw:
        return VALUE_TYPES[vt] if vt in VALUE_TYPES else "Object"

    return vt if vt in VALUE_TYPES else typing.Any


def typeFix(value_type: Union[Any, None] = "", default_value: Any = None) -> str:
    """
    Trying to fix or guess the type of a parameter. If a value_type is
    provided, this will be used to determine the type.

    :param value_type: any, convert type to one of our strings
    :param default_value: any, this will be used to determine the
                          type if value_type is not specified.

    :returns: str, the converted type as a supported string
    """
    if not value_type and default_value:
        try:  # first check for standard types
            value_type = type(default_value).__name__
        except TypeError:
            return str(guess_type_from_default(default_value))
    if isinstance(value_type, str) and value_type in SVALUE_TYPES.values():
        return str(value_type)  # make lint happy and cast to string
    if isinstance(value_type, str) and value_type in SVALUE_TYPES:
        return SVALUE_TYPES[value_type]
    if value_type in VALUE_TYPES:
        return VALUE_TYPES[value_type]
    return "UNSPECIFIED"


# these are our supported base types
VALUE_TYPES = {
    str: "String",
    int: "Integer",
    float: "Float",
    bool: "Boolean",
    list: "Json",
    dict: "dict",
    tuple: "Json",
    numpy.ndarray: "numpy.array",
    type: "Object",
    any: "Object",
}

SVALUE_TYPES = {k.__name__: v for k, v in VALUE_TYPES.items() if hasattr(k, "__name__")}
SVALUE_TYPES.update(
    {
        "Object.Object": "Object",
        "typing.Any": "Any",
        "NoneType": "UNSPECIFIED",
        "builtins.NoneType": "UNSPECIFIED",
    }
)

BLOCKDAG_DATA_FIELDS = [
    "inputPorts",
    "outputPorts",
    "applicationArgs",
    "category",
    "fields",
]


class Language(Enum):
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
