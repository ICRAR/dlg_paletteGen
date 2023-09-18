import datetime
import importlib
import inspect
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pkgutil import iter_modules
from typing import Any, Union

import benedict
from blockdag import build_block_dag

from .classes import (
    BLOCKDAG_DATA_FIELDS,
    DOXYGEN_SETTINGS,
    DOXYGEN_SETTINGS_C,
    DOXYGEN_SETTINGS_PYTHON,
    VALUE_TYPES,
    Language,
    logger,
    typeFix,
)


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


next_key = -1


def get_next_key():
    """
    TODO: This needs to disappear!!
    """
    global next_key

    next_key -= 1

    return next_key + 1


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

    :returns: str, output_xml_filename
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
    palette.modelData.detailedDescription = module_doc.strip()
    palette.modelData.filePath = output_filename
    palette.modelData.repositoryUrl = git_repo
    palette.modelData.commitHash = version
    palette.modelData.signature = block_dag["signature"]  # type: ignore
    palette.modelData.lastModifiedDatetime = (
        datetime.datetime.now().timestamp()
    )

    palette.nodeDataArray = nodes

    # write palette to file
    with open(output_filename, "w") as outfile:
        json.dump(palette, outfile, indent=4)


def prepare_and_write_palette(
    nodes: list, output_filename: str, module_doc: str = ""
):
    """
    Prepare and write the palette in JSON format.

    :param nodes: the list of nodes
    :param output_filename: the filename of the output
    :param module_doc: module level docstring
    """
    # add signature for whole palette using BlockDAG
    vertices = {}
    GITREPO = os.environ.get("GIT_REPO")
    VERSION = os.environ.get("PROJECT_VERSION")

    for i in range(len(nodes)):
        vertices[i] = nodes[i]
    block_dag = build_block_dag(vertices, [], data_fields=BLOCKDAG_DATA_FIELDS)

    # write the output json file
    write_palette_json(
        output_filename,
        module_doc,
        nodes,
        GITREPO,
        VERSION,
        block_dag,
    )
    logger.debug("Wrote %s components to %s", len(nodes), output_filename)


def get_submodules(module):
    """
    Retrieve names of sub-modules using iter_modules.
    This will also return sub-packages. Third tuple
    item is a flag ispkg indicating that.

    :param: module, module object to be searched

    :returns: iterator[tuple]
    """
    if not inspect.ismodule(module):
        logger.warning(
            "Provided object %s is not a module: %s",
            module,
            type(module),
        )
        return iter([])
    submods = []
    if hasattr(module, "__all__"):
        for mod in module.__all__:
            submod = f"{module.__name__}.{mod}"
            logger.debug("Trying to import %s", submod)
            traverse = True if submod not in submods else False
            m = import_using_name(
                f"{module.__name__}.{mod}", traverse=traverse
            )
            if (
                inspect.ismodule(m)
                or inspect.isfunction(m)
                or inspect.ismethod(m)
                or inspect.isbuiltin(m)
            ):
                submods.append(f"{submod}")
        logger.info(
            "Found submodules of %s in __all__: %s", module.__name__, submods
        )
    elif hasattr(module, "__path__"):
        sub_modules = iter_modules(module.__path__)
        submods = [
            f"{module.__name__}.{x[1]}"
            for x in sub_modules
            if (x[1][0] != "_" and x[1][:4] != "test")
        ]  # get the names; ignore test modules
        logger.debug("sub-modules found: %s", submods)
    else:
        for m in inspect.getmembers(module, lambda x: inspect.ismodule(x)):
            if (
                inspect.ismodule(m[1])
                and m[1].__name__ not in sys.builtin_module_names
                # and hasattr(m[1], "__file__")
                and m[1].__name__.find(module.__name__) > -1
            ):
                logger.debug("Trying to import submodule: %s", m[1].__name__)
                submods.append(getattr(module, m[0]).__name__)
    return iter(submods)


def import_using_name(mod_name: str, traverse: bool = False):
    """
    Import a module using its name and try hard to go up the hierarchy if
    direct import is not possible. This only imports actual modules,
    not classes, functions, or types. In those cases it will return the
    lowest module in the hierarchy. As a final fallback it will return the
    highest level module.

    :param mod_name: The name of the module to be imported.
    :param traverse: Follow the tree even if module already loaded.
    """
    logger.debug("Importing %s", mod_name)
    parts = mod_name.split(".")
    exists = ".".join(parts[:-1]) in sys.modules if not traverse else False
    if parts[-1].startswith("_"):
        return None
    try:  # direct import first
        mod = importlib.import_module(mod_name)
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
                    logger.debug(
                        "Error when loading module %s: %s"
                        % (parts[0], str(e)),
                    )
                    raise ImportError
                for m in parts[1:]:
                    try:
                        logger.debug("Getting attribute %s", m)
                        # Make sure this is a module
                        if hasattr(mod, m):
                            mod_prev = mod_down if mod_down else mod
                            mod_down = getattr(mod, m)
                        else:
                            logger.debug(
                                "Problem getting attribute '%s' from '%s'",
                                m,
                                mod,
                            )
                            mod_prev = mod
                        if inspect.ismodule(mod_down):
                            mod = mod_down
                        elif (  # in other cases return the provious module.
                            inspect.isclass(mod_down)
                            or inspect.isfunction(mod_down)
                            or inspect.isbuiltin(mod_down)
                            or inspect.ismethod(mod_down)
                        ):
                            mod = mod_prev
                        else:  # just fallback to initial module
                            mod
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
                            )
                logger.debug("Loaded module: %s", mod_name)
            else:
                logger.debug(
                    "Recursive import failed! %s", parts[0] in sys.modules
                )
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
    options: list = [],
    readonly: bool = False,
    precious: bool = False,
    positional: bool = False,
):
    """
    Construct a dummy field
    """
    field = benedict.BeneDict()
    fieldValue = benedict.BeneDict()
    fieldValue.name = name
    fieldValue.value = value
    fieldValue.defaultValue = defaultValue
    fieldValue.description = description
    fieldValue.type = vtype
    fieldValue.parameterType = parameterType
    fieldValue.usage = usage
    fieldValue.readonly = readonly
    fieldValue.options = options
    fieldValue.precious = precious
    fieldValue.positional = positional
    field.__setattr__(name, fieldValue)
    return field


def populateFields(parameters: dict, dd) -> dict:
    """
    Populate a field from signature parameters.
    """
    fields = {}
    value = None

    for p, v in parameters.items():
        value = (
            v.default if not isinstance(v.default, inspect._empty) else "None"
        )
        field = initializeField(p)
        # if there is a type hint use that
        if v.annotation != inspect._empty:
            if isinstance(v.annotation, str):
                field[p].type = v.annotation
            elif (
                hasattr(v.annotation, "__name__")
                and v.annotation != inspect._empty
            ):
                field[p].type = (
                    v.annotation.__name__
                    if not v.annotation.__name__ == "Optional"
                    else "None"
                )
            else:
                field[p].type = "Object"
        else:  # no type hint
            try:
                if isinstance(v.default, (list, tuple)):
                    value = v.default  # type: ignore
                    field[p].type = VALUE_TYPES[type(v.default)]
                elif (
                    hasattr(v.default, "type") and v.default != inspect._empty
                ):
                    if isinstance(v.default, str):  # type: ignore
                        value = v.default  # type: ignore
                elif isinstance(
                    v.default,
                    (
                        int,
                        float,
                        bool,
                        complex,
                        str,
                        dict,
                    ),
                ):
                    if isinstance(v.default, float) and abs(
                        v.default
                    ) == float("inf"):
                        value = v.default.__repr__()  # type: ignore
                    else:
                        value = v.default  # type: ignore
                    field[p].type = type(v.default).__name__
                elif hasattr(v.default, "dtype"):
                    value = v.default.__repr__()
                    field[p].type = type(v.default).__name__
            except (ValueError, AttributeError):
                value = (
                    f"{type(v.default).__module__}"  # type: ignore
                    + f".{type(v.default).__name__}"  # type: ignore
                )

        if isinstance(value, type):
            value = None
        field[p].value = field[p].defaultValue = value
        param_desc = dd.params[p] if dd and p in dd.params else None
        field[p].description = dd.params[p]["desc"] if param_desc else ""
        field[p].parameterType = "ApplicationArgument"
        field[p].options = None
        field[p].positional = (
            True if v.kind == inspect.Parameter.POSITIONAL_ONLY else False
        )
        if not field[p].type:
            if param_desc and param_desc["type"]:
                field[p].type = dd.params[p]["type"]
            else:
                field[p].type = "Object"  # if we don't know what it is
        field[p].type = typeFix(field[p].type)
        if field[p].type == "Json" or field[p].type.startswith(
            "Object"
        ):  # we want to carry these as strings
            field[p].value = field[p].defaultValue = field[p].value.__repr__()
        fields.update(field)

    logger.debug("Parameters %s", fields)
    return fields


def constructNode(
    category: str = "PythonApp",
    key: int = -1,
    name: str = "example_function",
    description: str = "No description found",
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
    Node = benedict.BeneDict()
    Node.category = category
    Node.key = key
    Node.name = name
    Node.description = description
    Node.repositoryUrl = repositoryUrl
    Node.commitHash = commitHash
    Node.paletteDownloadUrl = paletteDownlaodUrl
    Node.dataHash = dataHash
    Node.fields = benedict.BeneDict()
    return Node


def populateDefaultFields(Node):
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
    gs[n].name = n
    gs[n].type = "Boolean"
    gs[n].value = "false"
    gs[n].default_value = "false"
    gs[n].description = "Is this node the start of a group?"
    Node.fields.update(gs)

    n = "execution_time"
    et = initializeField(n)
    et[n].name = n
    et[n].value = 2
    et[n].defaultValue = 2
    et[n].type = "Integer"
    et[
        n
    ].description = (
        "Estimate of execution time (in seconds) for this application."
    )
    et[n].parameterType = "ConstraintParameter"
    Node.fields.update(et)

    n = "num_cpus"
    ncpus = initializeField(n)
    ncpus[n].name = n
    ncpus[n].value = 1
    ncpus[n].default_value = 1
    ncpus[n].type = "Integer"
    ncpus[n].description = "Number of cores used."
    ncpus[n].parameterType = "ConstraintParameter"
    Node.fields.update(ncpus)

    n = "func_name"
    fn = initializeField(name=n)
    fn[n].name = n
    fn[n].value = "example.function"
    fn[n].defaultValue = "example.function"
    fn[n].type = "String"
    fn[n].description = "Complete import path of function"
    fn[n].readonly = True
    Node.fields.update(fn)

    n = "dropclass"
    dc = initializeField(n)
    dc[n].name = n
    dc[n].value = "dlg.apps.pyfunc.PyFuncApp"
    dc[n].defaultValue = "dlg.apps.pyfunc.PyFuncApp"
    dc[n].type = "String"
    dc[n].description = "The python class that implements this application"
    dc[n].readonly = True
    Node.fields.update(dc)

    n = "input_parser"
    inpp = initializeField(name=n)
    inpp[n].name = n
    inpp[n].description = "Input port parsing technique"
    inpp[n].value = "pickle"
    inpp[n].defaultValue = "pickle"
    inpp[n].type = "Select"
    inpp[n].options = ["pickle", "eval", "npy", "path", "dataurl"]
    Node.fields.update(inpp)

    n = "output_parser"
    outpp = initializeField(name=n)
    outpp[n].name = n
    outpp[n].description = "Output port parsing technique"
    outpp[n].value = "pickle"
    outpp[n].defaultValue = "pickle"
    outpp[n].type = "Select"
    outpp[n].options = ["pickle", "eval", "npy", "path", "dataurl"]
    Node.fields.update(outpp)

    return Node


def constructPalette():
    """
    Constructing the structure of a palette.
    """
    palette = benedict.BeneDict(
        {
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
            },
            "nodeDataArray": [],
            "linkDataArray": [],
        }
    )  # type: ignore
    return palette
