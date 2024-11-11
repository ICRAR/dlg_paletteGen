# pylint: disable=invalid-name
# pylint: disable=bare-except
# pylint: disable=eval-used
# pylint: disable=global-statement
# pylint: disable=too-many-arguments
# pylint: disable=too-many-branches
# pylint: disable=too-many-statements
# pylint: disable=protected-access
# pylint: disable=dangerous-default-value
"""
Support functions
"""

import ast
import datetime
import importlib
import inspect
import json
import os
import re
import subprocess
import sys
import tempfile
import typing
import xml.etree.ElementTree as ET
from pkgutil import iter_modules
from typing import Any, Union

import numpy
from blockdag import build_block_dag

from .settings import (
    BLOCKDAG_DATA_FIELDS,
    CVALUE_TYPES,
    DOXYGEN_SETTINGS,
    DOXYGEN_SETTINGS_C,
    DOXYGEN_SETTINGS_PYTHON,
    SVALUE_TYPES,
    VALUE_TYPES,
    Language,
    logger,
)


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
            vt = str
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
    path_ind = 0
    if not value_type and default_value:
        try:  # first check for standard types
            value_type = type(default_value).__name__
        except TypeError:
            guess_type = str(guess_type_from_default(default_value))
        path_ind = 1
    elif isinstance(value_type, str) and value_type in SVALUE_TYPES.values():
        guess_type = str(value_type)  # make lint happy and cast to string
        path_ind = 2
    elif isinstance(value_type, str) and value_type in SVALUE_TYPES:
        guess_type = SVALUE_TYPES[value_type]
        path_ind = 3
    elif value_type in VALUE_TYPES:
        guess_type = VALUE_TYPES[value_type]
        path_ind = 4
    elif not isinstance(value_type, str):
        mod = value_type.__module__ if hasattr(value_type, "__module__") else ""
        guess_type = f"{mod}.{value_type.__name__}"  # type: ignore[union-attr]
        path_ind = 5
    elif isinstance(value_type, str) and value_type in CVALUE_TYPES:
        guess_type = CVALUE_TYPES[value_type]
        path_ind = 6
    elif isinstance(value_type, str) and value_type in CVALUE_TYPES.values():
        guess_type = str(value_type)  # make lint happy and cast to string
        path_ind = 7
    elif import_using_name(value_type, traverse=True, err_log=False):
        guess_type = str(value_type)
        path_ind = 8
    else:
        guess_type = "UNIDENTIFIED"
        path_ind = 9
    logger.debug(
        "Parameter type guessed from %s: %s, %d", value_type, guess_type, path_ind
    )
    return guess_type


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
    with open(doxygen_filename, "r", encoding="utf-8") as dfile:
        contents = dfile.readlines()

    with open(doxygen_filename, "w", encoding="utf-8") as dfile:
        for line in contents:
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


def get_next_id() -> str:
    """
    Use tempfile.mktmp now
    """
    return tempfile.mktemp(prefix="", dir="")


def get_mod_name(mod) -> str:
    """
    Helper function to get a name from a module in
    all cases.
    """
    if not mod:
        return ""
    if hasattr(mod, "__name__"):
        return mod.__name__
    if hasattr(mod, "__class__"):
        return getattr(mod, "__class__").__name__
    for n, m in globals().items():
        if m == mod:
            return n
    return ""


def process_doxygen(language: Language = Language.PYTHON):
    """
    Run doxygen on the provided directory/file.

    :param language: Language, can be [2] for Python, 1 for C or 0 for Unknown
    """
    # create a temp file to contain the Doxyfile
    # create a temp file to contain the Doxyfile
    with tempfile.NamedTemporaryFile() as doxygen_file:
        doxygen_filename = doxygen_file.name

    # create a default Doxyfile
    subprocess.call(
        ["doxygen", "-g", doxygen_filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    logger.info("Wrote doxygen configuration file (Doxyfile) to %s", doxygen_filename)

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

    :returns: str, output_xml_filename
    """
    # run xsltproc
    outdir = DOXYGEN_SETTINGS["OUTPUT_DIRECTORY"]
    output_xml_filename = outdir + "/xml/doxygen.xml"

    with open(output_xml_filename, "w", encoding="utf-8") as outfile:
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
    os.system("cp " + output_xml_filename + " output.xml")
    logger.info("Wrote doxygen XML to output.xml")
    return output_xml_filename


def write_palette_json(
    output_filename: str,
    module_doc: Union[str, None],
    nodes: list,
    git_repo: Union[str, None],
    version: Union[str, None],
    block_dag: list,
):
    """
    Construct palette header and Write nodes to the output file

    :param output_filename: str, the name of the output file
    :param module_doc: module level docstring
    :param nodes: list of nodes
    :param git_repo: str, the git repository URL
    :param version: str, version string to be used
    :param block_dag: list, the reproducibility information
    """
    if not module_doc:
        module_doc = ""
    for i in range(len(nodes)):
        nodes[i]["dataHash"] = block_dag[i]["data_hash"]
    palette = constructPalette()
    palette["modelData"]["detailedDescription"] = module_doc.strip()
    palette["modelData"]["filePath"] = output_filename
    palette["modelData"]["repositoryUrl"] = git_repo
    palette["modelData"]["commitHash"] = version
    palette["modelData"]["signature"] = block_dag["signature"]  # type: ignore
    palette["modelData"]["lastModifiedDatetime"] = datetime.datetime.now().timestamp()
    palette["modelData"]["numLGNodes"] = len(nodes)

    palette["nodeDataArray"] = nodes

    # write palette to file
    # logger.debug(">>> palette: %s", palette)
    with open(output_filename, "w", encoding="utf-8") as outfile:
        try:
            json.dump(palette, outfile, indent=4)
            return palette
        except TypeError:
            logger.error("Problem serializing palette! Bailing out!!")
            return palette


def get_field_by_name(name: str, node, value_key: str = "") -> dict:
    """
    Get field dictionary from node providing a name.

    :param name: the name of the field to retrieve
    :param node: the node data structure
    :value_key: the key of the attribute of the field to return

    :returns the field dictionary or empty dict
    """
    try:
        field = [f for f in node["fields"] if f["name"] == name][0]
        if value_key and value_key in field:
            return field[value_key]
        return field
    except (IndexError, TypeError):
        return {}


def prepare_and_write_palette(nodes: list, output_filename: str, module_doc: str = ""):
    """
    Prepare and write the palette in JSON format.

    :param nodes: the list of nodes
    :param output_filename: the filename of the output
    :param module_doc: module level docstring
    """
    # add signature for whole palette using BlockDAG
    vertices = {}
    v_ind = -1
    GITREPO = os.environ.get("GIT_REPO")
    VERSION = os.environ.get("PROJECT_VERSION")

    funcs = []
    f_nodes = []
    for i in range(len(nodes)):
        func_name = get_field_by_name("func_name", nodes[i], value_key="value")
        if func_name and func_name not in funcs:
            # mod_name = func_name.split(".", 1)[0]
            # if mod_name not in bi.keys():
            funcs.append(func_name)
            f_nodes.append(nodes[i])
            v_ind += 1
            vertices[v_ind] = nodes[i]
            logger.debug("Added function %s: %s", func_name, v_ind)
        elif func_name and func_name in funcs:
            logger.debug("Removing duplicate function: %s", func_name)
        elif not func_name:
            v_ind += 1
            f_nodes.append(nodes[i])
            vertices[v_ind] = nodes[i]
    block_dag = build_block_dag(vertices, [], data_fields=BLOCKDAG_DATA_FIELDS)

    # write the output json file
    palette = write_palette_json(
        output_filename,
        module_doc,
        f_nodes,
        GITREPO,
        VERSION,
        block_dag,
    )
    logger.debug("Wrote %s components to %s", len(nodes), output_filename)
    return palette


def get_submodules(module):
    """
    Retrieve names of sub-modules using iter_modules.
    This will also return sub-packages. Third tuple
    item is a flag ispkg indicating that.

    :param: module, module object to be searched

    :returns: iterator[tuple]
    """
    submods = []
    module_vars = {}  # store module level variables
    module_name = get_mod_name(module)
    if hasattr(module, "__all__"):
        for mod in module.__all__:
            try:
                type_mod = getattr(module, mod)
            except AttributeError:
                logger.warning(
                    "Attribute %s defined in %s.__all__, but not found.", mod, module
                )
                continue
            if isinstance(
                type_mod, (str, int, float, bytes, bytearray, bool, dict, list, tuple)
            ):
                # just store module level variables for now
                value = getattr(module, mod)
                field = initializeField(
                    name=mod,
                    value=value,
                    defaultValue=value,
                    vtype=typeFix(type(value)),
                    parameterType="ApplicationArgument",
                    readonly=True,
                )
                module_vars[mod] = field
                continue
            submod = f"{module_name}.{mod}"
            logger.debug("Trying to import %s", submod)
            traverse = submod not in submods
            m = import_using_name(f"{module_name}.{mod}", traverse=traverse)
            if (
                not get_mod_name(m)
                == get_mod_name(module)  # prevent loading module itself
                # and inspect.ismodule(m)
                # or inspect.isfunction(m)
                # or inspect.ismethod(m)
                # or inspect.isbuiltin(m)
            ):
                logger.debug(">>> submodule %s of type: %s", submod, type(m))
                submods.append(f"{submod}")
        logger.debug("Found submodules of %s in __all__: %s", module_name, submods)
    elif hasattr(module, "__path__"):
        sub_modules = iter_modules(module.__path__)
        submods = [
            f"{module_name}.{x[1]}"
            for x in sub_modules
            if (x[1][0] != "_" and x[1][:4] != "test")
        ]  # get the names; ignore test modules
        logger.debug("sub-modules found: %s", submods)
    else:
        for m in inspect.getmembers(module, lambda x: inspect.ismodule(x)):
            if (
                inspect.ismodule(m[1])
                and get_mod_name(m[1]) not in sys.builtin_module_names
                # and hasattr(m[1], "__file__")
                and get_mod_name(m[1]).find(module_name) > -1
            ):
                logger.debug("Trying to import submodule: %s", get_mod_name(m[1]))
                submods.append(get_mod_name(getattr(module, m[0])))
    return iter(submods), iter(module_vars)


def import_using_name(mod_name: str, traverse: bool = False, err_log=True):
    """
    Import a module using its name and try hard to go up the hierarchy if
    direct import is not possible. This only imports actual modules,
    not classes, functions, or types. In those cases it will return the
    lowest module in the hierarchy. As a final fallback it will return the
    highest level module.

    :param mod_name: The name of the module to be imported.
    :param traverse: Follow the tree even if module already loaded.
    :param err_log: Log import error
    """
    logger.debug("Importing %s", mod_name)
    if not re.match("^[_A-Z,a-z]", mod_name):
        return None
    parts = mod_name.split(".")
    exists = ".".join(parts[:-1]) in sys.modules if not traverse else False
    if parts[-1].startswith("_"):
        return None
    try:  # direct import first
        mod = importlib.import_module(mod_name)
    except ValueError:
        logger.error("Unable to import module: %s", mod_name)
        mod = None
    except ModuleNotFoundError:
        mod_down = None
        if len(parts) >= 1:
            if parts[-1] in ["__init__", "__class__"]:
                parts = parts[:-1]
            logger.debug("Recursive import: %s", parts)
            # import top-level first
            if parts[0] and not exists:
                try:
                    mod = importlib.import_module(parts[0])
                except ImportError as e:
                    if err_log:
                        logger.error(
                            "Error when loading module %s: %s %s",
                            parts[0],
                            str(e),
                            mod_name,
                        )
                    return None
                for m in parts[1:]:
                    try:
                        logger.debug("Getting attribute %s", m)
                        # Make sure this is a module
                        if hasattr(mod, m):
                            mod_down = getattr(mod, m)
                        else:
                            logger.debug(
                                "Problem getting attribute '%s' from '%s'",
                                m,
                                mod,
                            )
                        mod = mod_down
                    except AttributeError:
                        try:
                            logger.debug(
                                "Trying to load backwards: %s",
                                ".".join(parts[:-1]),
                            )
                            mod = importlib.import_module(".".join(parts[:-1]))
                            break
                        except Exception as e:
                            raise ValueError(
                                "Problem importing module %s, %s" % (mod, e)
                            ) from e
                logger.debug("Loaded module: %s", mod_name)
            else:
                logger.debug("Recursive import failed! %s", parts[0] in sys.modules)
                return None
    return mod


def initializeField(
    name: str = "dummy",
    value: Any = "dummy",
    defaultValue: Any = "dummy",
    description: str = "no description found",
    vtype: Union[str, None] = None,
    parameterType: str = "ComponentParameter",
    usage: str = "NoPort",
    options: list = [],  # noeq: E501
    readonly: bool = False,
    precious: bool = False,
    positional: bool = False,
):
    """
    Construct a dummy field
    """
    field = {}  # type: ignore
    fieldValue = {}
    fieldValue["name"] = name
    fieldValue["value"] = value
    fieldValue["defaultValue"] = defaultValue
    fieldValue["description"] = description
    fieldValue["type"] = vtype  # type:ignore
    fieldValue["parameterType"] = parameterType
    fieldValue["usage"] = usage
    fieldValue["readonly"] = readonly  # type:ignore
    fieldValue["options"] = options  # type:ignore
    fieldValue["precious"] = precious  # type:ignore
    fieldValue["positional"] = positional  # type:ignore
    field.__setitem__(name, fieldValue)
    return field


def get_value_type_from_default(default):
    """
    Extract value and type from default value
    """
    param_desc = {
        "value": None,
        "desc": "",
        "type": "Object",
    }  # temporarily holds results
    # get value and type
    value = ptype = (
        f"{type(default).__module__}"  # type: ignore
        + f".{type(default).__name__}"  # type: ignore
    )
    if default is inspect._empty or ptype == "builtins.NoneType":
        value = None
        ptype = CVALUE_TYPES["NoneType"]
    else:  # there is a default value
        try:
            ptype = type(default)
            if ptype in VALUE_TYPES:
                if isinstance(default, float) and abs(default) == float("inf"):
                    value = default.__repr__()  # type: ignore
                else:
                    value = default
            elif hasattr(default, "dtype"):
                try:
                    value = default.__repr__()
                except TypeError as e:
                    if e.__repr__().find("numpy.bool_") > -1:
                        value = "bool"
        except (ValueError, AttributeError):
            value = ptype = (
                f"{type(default).__module__}"  # type: ignore
                + f".{type(default).__name__}"  # type: ignore
            )

        # final checks of the value
        if isinstance(value, type):
            value = None
        try:
            json.dumps(value)
        except TypeError:
            # this is a complex type
            logger.debug("Object not JSON serializable: %s", value)
            ptype = value = type(value).__name__
        if not isinstance(value, (str, bool)) and (
            ptype in ["Json"]
        ):  # we want to carry these as strings
            value = value.__name__()
    if repr(default) == "nan" and numpy.isnan(default):
        value = None
    param_desc["value"] = value
    param_desc["type"] = typeFix(ptype)
    return param_desc


def populateFields(parameters: dict, dd) -> dict:
    """
    Populate a field from signature parameters and mixin
    documentation if available.
    """
    fields = {}
    descr_miss = []

    new_param = inspect.Parameter(
        "base_name", inspect._ParameterKind.POSITIONAL_OR_KEYWORD
    )
    items = list(parameters.items()) + [(new_param.name, new_param)]
    for p, v in items:
        field = initializeField(p)

        param_desc = get_value_type_from_default(v.default)
        # now merge with description from docstring, if available
        if dd:
            if p in dd.params and p != "self":
                param_desc["desc"] = dd.params[p]["desc"]
            elif p != "self":
                descr_miss.append(p)
            elif p == "self":
                param_desc["desc"] = f"Reference to {dd.name} object"

        # populate the field itself
        field[p]["value"] = field[p]["defaultValue"] = param_desc["value"]

        # deal with the type
        if (
            v.annotation  # type from inspect is first choice.
            and v.annotation not in [None, inspect._empty]
            and (hasattr(v.annotation, "__name__") or hasattr(v.annotation, "__repr__"))
        ):
            if (
                hasattr(v.annotation, "__name__")
                and hasattr(v.annotation, "__module__")
                and v.annotation.__module__ != "builtins"
            ):
                field[p]["type"] = f"{v.annotation.__module__}.{v.annotation.__name__}"
            elif hasattr(v.annotation, "__name__"):
                field[p]["type"] = typeFix(f"{v.annotation.__name__}")
            else:
                field[p]["type"] = v.annotation.__repr__()
            logger.debug("Parameter type from annotation: %s", field[p]["type"])
        # else we use the type from default value
        elif field[p]["name"] == "args":
            field[p]["type"] = "list"
        elif field[p]["name"] == "kwargs":
            field[p]["type"] = "dict"
        elif param_desc["type"] and param_desc["type"] != "None":
            field[p]["type"] = param_desc["type"]
        elif dd and p in dd.params and dd.params[p]["type"]:
            # type from docstring
            field[p]["type"] = typeFix(dd.params[p]["type"])
        else:
            field[p]["type"] = CVALUE_TYPES["NoneType"]

        if (
            field[p]["type"] not in SVALUE_TYPES.values()
            and field[p]["name"] != "base_name"
        ):
            # complex types can't be specified on a simple form field
            # thus we assume they are provided through a port.
            # Like this we can support any type.
            field[p]["usage"] = "InputPort"
            field[p]["value"] = None
        field[p]["description"] = param_desc["desc"]
        if p in ["self", "class"]:
            field[p]["parameterType"] = "ComponentParameter"
        else:
            field[p]["parameterType"] = "ApplicationArgument"
        field[p]["options"] = None
        field[p]["positional"] = v.kind == inspect.Parameter.POSITIONAL_ONLY
        logger.debug("Final type of parameter %s: %s", p, field[p]["type"])
        if isinstance(field[p]["value"], numpy.ndarray):
            try:
                field[p]["value"] = field[p]["defaultValue"] = field[p]["value"].tolist()
            except NotImplementedError:
                field[p]["value"] = []
        if repr(field[p]["value"]) == "nan" and numpy.isnan(field[p]["value"]):
            field[p]["value"] = None
        fields.update(field)

    fields["base_name"]["parameterType"] = "ComponentParameter"
    fields["base_name"]["type"] = "String"
    fields["base_name"]["readonly"] = True
    fields["base_name"]["description"] = "The base class for this member function"
    return fields


def constructNode(
    category: str = "PythonApp",
    name: str = "example_function",
    description: str = "",
    repositoryUrl: str = "dlg_paletteGen.generated",
    commitHash: str = "0.1",
    paletteDownlaodUrl: str = "",
    dataHash: str = "",
):
    """
    Construct a palette node using default parameters if not
    specified otherwise. For some reason sub-classing benedict
    did not work here, thus we use a function instead.
    """
    Node = {}
    Node["category"] = category
    Node["id"] = get_next_id()
    Node["name"] = name
    Node["description"] = description
    Node["repositoryUrl"] = repositoryUrl
    Node["commitHash"] = commitHash
    Node["paletteDownloadUrl"] = paletteDownlaodUrl
    Node["dataHash"] = dataHash
    Node["fields"] = {}  # type:ignore
    return Node


def populateDefaultFields(Node):  # pylint: disable=invalid-name
    """
    Populate a palette node with the default
    field definitions. This is separate from the
    construction of the node itself to allow the
    ApplicationArgs to be listed first.

    :param Node: a LG node from constructNode
    """
    # default field definitions
    n = "group_start"
    gs = initializeField(n)
    gs[n]["name"] = n
    gs[n]["type"] = "Boolean"
    gs[n]["value"] = "false"
    gs[n]["default_value"] = "false"
    gs[n]["description"] = "Is this node the start of a group?"
    Node["fields"].update(gs)

    n = "execution_time"
    et = initializeField(n)
    et[n]["name"] = n
    et[n]["value"] = 2
    et[n]["defaultValue"] = 2
    et[n]["type"] = "Integer"
    et[n]["description"] = "Estimate of execution time (in seconds) for this application."
    et[n]["parameterType"] = "ConstraintParameter"
    Node["fields"].update(et)

    n = "num_cpus"
    ncpus = initializeField(n)
    ncpus[n]["name"] = n
    ncpus[n]["value"] = 1
    ncpus[n]["default_value"] = 1
    ncpus[n]["type"] = "Integer"
    ncpus[n]["description"] = "Number of cores used."
    ncpus[n]["parameterType"] = "ConstraintParameter"
    Node["fields"].update(ncpus)

    n = "func_name"
    fn = initializeField(name=n)
    fn[n]["name"] = n
    fn[n]["value"] = "example.function"
    fn[n]["defaultValue"] = "example.function"
    fn[n]["type"] = "String"
    fn[n]["description"] = "Complete import path of function"
    fn[n]["readonly"] = True
    Node["fields"].update(fn)

    n = "dropclass"
    dc = initializeField(n)
    dc[n]["name"] = n
    dc[n]["value"] = "dlg.apps.pyfunc.PyFuncApp"
    dc[n]["defaultValue"] = "dlg.apps.pyfunc.PyFuncApp"
    dc[n]["type"] = "String"
    dc[n]["description"] = "The python class that implements this application"
    dc[n]["readonly"] = True
    Node["fields"].update(dc)

    n = "input_parser"
    inpp = initializeField(name=n)
    inpp[n]["name"] = n
    inpp[n]["description"] = "Input port parsing technique"
    inpp[n]["value"] = "pickle"
    inpp[n]["defaultValue"] = "pickle"
    inpp[n]["type"] = "Select"
    inpp[n]["options"] = ["pickle", "eval", "npy", "path", "dataurl"]
    Node["fields"].update(inpp)

    n = "output_parser"
    outpp = initializeField(name=n)
    outpp[n]["name"] = n
    outpp[n]["description"] = "Output port parsing technique"
    outpp[n]["value"] = "pickle"
    outpp[n]["defaultValue"] = "pickle"
    outpp[n]["type"] = "Select"
    outpp[n]["options"] = ["pickle", "eval", "npy", "path", "dataurl"]
    Node["fields"].update(outpp)

    return Node


def constructPalette():
    """
    Constructing the structure of a palette.
    """
    palette = {
        "modelData": {
            "filePath": "",
            "fileType": "palette",
            "shortDescription": "",
            "detailedDescription": "",
            "repoService": "GitHub",
            "repoBranch": "master",
            "repo": "ICRAR/EAGLE_test_repo",
            "eagleVersion": "",
            "eagleCommitHash": "",
            "schemaVersion": "AppRef",
            "readonly": True,
            "repositoryUrl": "",
            "commitHash": "",
            "downloadUrl": "",
            "signature": "",
            "lastModifiedName": "wici",
            "lastModifiedEmail": "",
            "lastModifiedDatetime": datetime.datetime.now().timestamp(),
            "numLGNodes": 0,
        },
        "nodeDataArray": [],
        "linkDataArray": [],
    }
    return palette
