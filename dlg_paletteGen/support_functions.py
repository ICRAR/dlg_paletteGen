import ast
import logging
import os
import random
import re
import subprocess
import sys
import tempfile
import types
import uuid
import xml.etree.ElementTree as ET
from enum import Enum

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


class CustomFormatter(logging.Formatter):
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

next_key = -1

VALUE_TYPES = {
    str: "String",
    int: "Integer",
    float: "Float",
    bool: "Boolean",
    list: "Json",
    dict: "Json",
    tuple: "Json",
}


class Language(Enum):
    UNKNOWN = 0
    C = 1
    PYTHON = 2


def cleanString(input_text: str) -> str:
    """
    Remove ANSI escape strings from input"

    :param input_text: string to clean

    :returns: str, cleaned string
    """
    # ansi_escape = re.compile(r'[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]')
    ansi_escape = re.compile(r"\[[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", input_text)


def typeFix(value_type: str, default_value: str = "") -> str:
    """
    Trying to fix or guess the type of a parameter

    :param value_type: str, convert type string to something known

    :returns output_type: str, the converted type
    """
    typerex = r"[\(\[](bool|boolean|int|float|string|str)[\]\)]"
    re_type = re.findall(typerex, value_type)
    # fix some types
    if re_type:
        re_type = re_type[0]
        if re_type in ["bool", "boolean"]:
            value_type = "Boolean"
            if default_value == "":
                default_value = "False"
        if re_type == "int":
            value_type = "Integer"
            if default_value == "":
                default_value = "0"
        if re_type == "float":
            value_type = "Float"
            if default_value == "":
                default_value = "0"
        if re_type in ["string", "str", "*", "**"]:
            value_type = "String"
    elif default_value != "":
        value_type = default_value

    # try to guess the type based on the default value
    # TODO: try to parse default_value as JSON to detect JSON types

    if (
        not re_type
        and default_value != ""
        and default_value is not None
        and default_value != "None"
    ):
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
                vt = type(l["t"])
                if not isinstance(l["t"], type):
                    default_value = l["t"]
                else:
                    vt = str
            except NameError:
                vt = str
            except SyntaxError:
                vt = str

            value_type = VALUE_TYPES[vt] if vt in VALUE_TYPES else "String"
            val = None
            if value_type == "String":
                # if it is String we need to do a few more tests
                try:
                    val = int(default_value)  # type: ignore
                    value_type = "Integer"
                    # print("Use Integer")
                except TypeError:
                    if isinstance(default_value, types.BuiltinFunctionType):
                        value_type = "String"
                except ValueError:
                    try:
                        val = float(  # noqa: F841
                            default_value  # type: ignore
                        )
                        value_type = "Float"
                    except ValueError:
                        if default_value and (
                            default_value.lower() == "true"
                            or default_value.lower() == "false"
                        ):
                            value_type = "Boolean"
                            default_value = default_value.lower()
                        else:
                            value_type = "String"
        except NameError or TypeError:  # type: ignore
            raise
    # we only want stuff in parentheses
    v_type = re.split(r"[\[\]\(\)]", value_type)
    value_type = v_type[1] if len(v_type) > 1 else v_type[0]
    return value_type


def check_text_element(xml_element: ET.Element, sub_element: str):
    """
    Check a xml_element for the first occurance of sub_elements and return
    the joined text content of them.
    """
    text = ""
    sub = xml_element.find(sub_element)
    try:
        text += sub.text  # type: ignore
    except (AttributeError, TypeError):
        text = "Unknown"
    return text


def modify_doxygen_options(doxygen_filename: str, options: dict):
    """
    Updates default doxygen config for this task

    :param doxygen_filename: str, the file name of the config file
    :param options: dict, dictionary of the options to be modified
    """
    with open(doxygen_filename, "r") as dfile:
        contents = dfile.readlines()

    with open(doxygen_filename, "w") as dfile:
        for index, line in enumerate(contents):
            if line[0] == "#":
                continue
            if len(line) <= 1:
                continue

            parts = line.split("=")
            first_part = parts[0].strip()
            written = False

            for key, value in options.items():
                if first_part == key:
                    dfile.write(key + " = " + str(value) + "\n")
                    written = True
                    break

            if not written:
                dfile.write(line)


def get_next_key():
    """
    TODO: This needs to disappear!!
    """
    global next_key

    next_key -= 1

    return next_key + 1


def create_uuid(seed):
    """
    Simple helper function to create a UUID

    :param seed: [int| str| bytes| bytearray], seed value, if not provided
                 timestamp is used

    :returns uuid
    """
    rnd = random.Random()
    rnd.seed(seed)

    new_uuid = uuid.UUID(int=rnd.getrandbits(128), version=4)
    return new_uuid


def process_doxygen(language: Language = Language.PYTHON):
    """
    Run doxygen on the provided directory/file.

    :param language: Language, can be [2] for Python, 1 for C or 0 for Unknown
    """
    # create a temp file to contain the Doxyfile
    doxygen_file = tempfile.NamedTemporaryFile()
    doxygen_filename = doxygen_file.name
    doxygen_file.close()

    # create a default Doxyfile
    subprocess.call(
        ["doxygen", "-g", doxygen_filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info(
        "Wrote doxygen configuration file (Doxyfile) to " + doxygen_filename
    )

    # modify options in the Doxyfile
    modify_doxygen_options(doxygen_filename, DOXYGEN_SETTINGS)

    if language == Language.C:
        modify_doxygen_options(doxygen_filename, DOXYGEN_SETTINGS_C)
    elif language == Language.PYTHON:
        modify_doxygen_options(doxygen_filename, DOXYGEN_SETTINGS_PYTHON)

    # run doxygen
    # os.system("doxygen " + doxygen_filename)
    subprocess.call(
        ["doxygen", doxygen_filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def process_xml() -> str:
    """
    Run xsltproc on the output produced by doxygen.

    :returns output_xml_filename: str
    """
    # run xsltproc
    outdir = DOXYGEN_SETTINGS["OUTPUT_DIRECTORY"]
    output_xml_filename = outdir + "/xml/doxygen.xml"

    with open(output_xml_filename, "w") as outfile:
        subprocess.call(
            [
                "xsltproc",
                outdir + "/xml/combine.xslt",
                outdir + "/xml/index.xml",
            ],
            stdout=outfile,
            stderr=subprocess.DEVNULL,
        )

    # debug - copy output xml to local dir
    # TODO: do this only if DEBUG is enabled
    os.system("cp " + output_xml_filename + " output.xml")
    logger.info("Wrote doxygen XML to output.xml")
    return output_xml_filename
