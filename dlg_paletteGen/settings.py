"""Set global values."""

from enum import Enum

import numpy

from . import logger, silence_module_logger

logger.debug("Number of enabled loggers: %d", silence_module_logger())

# these are our supported base types
VALUE_TYPES = {
    str: "String",
    int: "Integer",
    float: "Float",
    bool: "Boolean",
    list: "List",
    dict: "Dict",
    numpy.array: "numpy.array",
    numpy.ndarray: "numpy.array",
}

SVALUE_TYPES = {k.__name__: v for k, v in VALUE_TYPES.items() if hasattr(k, "__name__")}

CVALUE_TYPES = {
    "array_like": "numpy.array",
    "arraylike": "numpy.array",
    numpy.ndarray.__name__: "numpy.array",
    numpy._globals._NoValueType.__name__: "Object",  # type: ignore
    "inspect._empty": "None",
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
