"""
dlg_paletteGen base module.

TODO: This whole tool needs re-factoring into separate class files
(compound, child, grandchild, grandgrandchild, node, param, pluggable parsers)
Should also be made separate sub-repo with proper installation and entry point.

"""
import csv
import datetime
import inspect
import json
import os
import sys
import types
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Any, Union, _SpecialForm

from blockdag import build_block_dag

from dlg_paletteGen.classes import (
    Child,
    DetailedDescription,
    DummySig,
    Language,
    logger,
)

from .support_functions import (
    check_text_element,
    constructNode,
    constructPalette,
    get_next_key,
    get_submodules,
    import_using_name,
    populateDefaultFields,
    populateFields,
)

KNOWN_PARAM_DATA_TYPES = [
    "String",
    "Integer",
    "Float",
    "Object",
    "Boolean",
    "Select",
    "Password",
    "Json",
    "Python",
]
KNOWN_CONSTRUCT_TYPES = ["Scatter", "Gather"]

KNOWN_DATA_CATEGORIES = [
    "File",
    "Memory",
    "SharedMemory",
    "NGAS",
    "S3",
    "Plasma",
    "PlasmaFlight",
    "ParameterSet",
    "EnvironmentVariables",
]


class PGenEnum(str, Enum):
    @classmethod
    def has_key(cls, key):
        return key in cls._member_names_


class FieldType(PGenEnum):
    ComponentParameter = "ComponentParameter"
    ConstructParameter = "ConstructParameter"
    ApplicationArgument = "ApplicationArgument"


class FieldUsage(PGenEnum):
    NoPort = "NoPort"
    InputPort = "InputPort"
    OutputPort = "OutputPort"
    InputOutput = "InputOutput"


class FieldAccess(PGenEnum):
    readonly = "readonly"
    readwrite = "readwrite"


BLOCKDAG_DATA_FIELDS = [
    "inputPorts",
    "outputPorts",
    "applicationArgs",
    "category",
    "fields",
]


def find_field_by_name(fields, name):
    """
    Get a field from a list of field dictionaries.

    :param fields: list, list of field dictionaries
    :param name: str, field name to check for

    :returns field dict if found, else None
    """
    for field in fields:
        if field["name"] == name:
            return field
    return None


def check_required_fields_for_category(message: str, fields: list, catg: str):
    """
    Check if fields have mandatory content and alert with text if not.

    :param message: str, the text to be used for the alert
    :param fields: list of field dicts to be checked
    :param catg: str, category to be checked

    :returns None
    """
    if catg in [
        "DynlibApp",
        "PythonApp",
        "Branch",
        "BashShellApp",
        "Mpi",
        "Docker",
    ]:
        alert_if_missing(message, fields, "execution_time")
        alert_if_missing(message, fields, "num_cpus")

    if catg in [
        "DynlibApp",
        "PythonApp",
        "Branch",
        "BashShellApp",
        "Docker",
    ]:
        alert_if_missing(message, fields, "group_start")

    if catg == "DynlibApp":
        alert_if_missing(message, fields, "libpath")

    if catg in [
        "File",
        "Memory",
        "NGAS",
        "ParameterSet",
        "Plasma",
        "PlasmaFlight",
        "S3",
    ]:
        alert_if_missing(message, fields, "data_volume")

    if catg in [
        "File",
        "Memory",
        "NGAS",
        "ParameterSet",
        "Plasma",
        "PlasmaFlight",
        "S3",
        "Mpi",
    ]:
        alert_if_missing(message, fields, "group_end")

    if catg in ["BashShellApp", "Mpi", "Docker", "Singularity"]:
        alert_if_missing(message, fields, "input_redirection")
        alert_if_missing(message, fields, "output_redirection")
        alert_if_missing(message, fields, "command_line_arguments")
        alert_if_missing(message, fields, "paramValueSeparator")
        alert_if_missing(message, fields, "argumentPrefix")

    # all nodes
    alert_if_missing(message, fields, "dropclass")


def create_field(
    internal_name: str,
    value: str,
    value_type: str,
    field_type: FieldType,
    field_usage: FieldUsage,
    access: FieldAccess,
    options: list,
    precious: bool,
    positional: bool,
    description: str,
):
    """
    TODO: field should be a dataclass
    For now just create a dict using the values provided

    :param internal_name: str, the internal name of the parameter
    :param value: str, the value of the parameter
    :param value_type: str, the type of the value
    :param field_type: One of FieldType type
    :param field_usage: One from FieldUsage type
    :param access: FieldAccess type, ReadWrite|ReadOnly (default ReadOnly)
    :param options: list, list of options
    :param precious: bool,
        should this parameter appear, even if empty or None
    :param positional: bool,
        is this a positional parameter
    :param description: str, the description used in the palette

    :returns field: dict
    """
    return {
        "name": internal_name,
        "value": value,
        "defaultValue": value,
        "description": description,
        "type": value_type,
        "fieldType": field_type,
        "usage": field_usage,
        "readonly": access == FieldAccess.readonly,
        "options": options,
        "precious": precious,
        "positional": positional,
    }


def alert_if_missing(message: str, fields: list, internal_name: str):
    """
    Produce a warning message using `text` if a field with `internal_name`
    does not exist.

    :param message: str, message text to be used
    :param fields: list of dicts of field definitions
    :param internal_name: str, identifier name of field to check
    """
    if find_field_by_name(fields, internal_name) is None:
        logger.warning(
            message + " component missing " + internal_name + " field"
        )
        pass


def parse_value(component_name: str, field_name: str, value: str) -> tuple:
    """
    Parse the value from the EAGLE compatible string. These are csv strings
    delimited by '/'
    TODO: This parser should be pluggable

    :param message: str, message text to be used for messages.
    :param value: str, the csv string to be parsed

    :returns tuple of parsed values
    """
    parts = []
    reader = csv.reader([value], delimiter="/", quotechar='"')
    for row in reader:
        parts = row

    # check that row contains 9 parts
    if len(parts) < 9:
        logger.warning(
            component_name
            + " field definition contains too few parts. Ignoring! : "
            + value
        )
        return ()
    elif len(parts) > 9:
        logger.warning(
            component_name
            + " too many parts in field definition. Combining last. "
        )
        parts[8] = "/".join(parts[8:])

    # init attributes of the param
    default_value = ""
    value_type: str = "String"
    field_type: str = FieldType.ComponentParameter
    field_usage: str = FieldUsage.NoPort
    access: str = FieldAccess.readwrite
    options: list = []
    precious = False
    positional = False
    description = ""

    # assign attributes (if present)
    if len(parts) > 0:
        default_value = parts[0]
    if len(parts) > 1:
        value_type = parts[1]
    if len(parts) > 2:
        field_type = parts[2]
    if len(parts) > 3:
        field_usage = parts[3]
    if len(parts) > 4:
        access = parts[4]
    else:
        logger.warning(
            component_name
            + " "
            + field_type
            + " ("
            + field_name
            + ") has no 'access' descriptor, using default (readwrite) : "
            + value
        )
    if len(parts) > 5:
        if parts[5].strip() == "":
            options = []
        else:
            options = parts[5].strip().split(",")
    else:
        logger.warning(
            component_name
            + " "
            + field_type
            + " ("
            + field_name
            + ") has no 'options', using default ([]) : "
            + value
        )
    if len(parts) > 6:
        precious = parts[6].lower() == "true"
    else:
        logger.warning(
            component_name
            + " "
            + field_type
            + " ("
            + field_name
            + ") has no 'precious' descriptor, using default (False) : "
            + value
        )
    if len(parts) > 7:
        positional = parts[7].lower() == "true"
    else:
        logger.warning(
            component_name
            + " "
            + field_type
            + " ("
            + field_name
            + ") has no 'positional', using default (False) : "
            + value
        )
    if len(parts) > 8:
        description = parts[8]

    return (
        default_value,
        value_type,
        field_type,
        field_usage,
        access,
        options,
        precious,
        positional,
        description,
    )


# NOTE: color, x, y, width, height are not specified in palette node,
# they will be set by the EAGLE importer
def create_palette_node_from_params(params) -> tuple:
    """
    Construct the palette node entry from the parameter structure

    TODO: Should split this up into individual parts

    :param params: list of dicts of params

    :returns tuple of dicts

    TODO: This should return a node dataclass object
    """
    text = ""
    description = ""
    comp_description = ""
    category = ""
    tag = ""
    construct = ""
    # inputPorts: list = []
    # outputPorts: list = []
    # inputLocalPorts: list = []
    # outputLocalPorts: list = []
    fields: list = []
    # applicationArgs: list = []

    # process the params
    for key, value in params.items():
        # read data from param

        if key == "category":
            category = value
        elif key == "construct":
            construct = value
        elif key == "tag":
            tag = value
        elif key == "text":
            text = value
        elif key == "description":
            comp_description = value
        else:
            internal_name = key

            # check if value can be correctly parsed
            field_data = parse_value(text, internal_name, value)
            if field_data in [None, ()]:
                continue

            (
                default_value,
                value_type,
                field_type,
                field_usage,
                access,
                options,
                precious,
                positional,
                description,
            ) = field_data

            # check that a param of type "Select" has some options specified,
            # and check that every param with some options specified is of type
            # "Select"
            if value_type == "Select" and len(options) == 0:
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + internal_name
                    + "' is of type 'Select' but has no options specified: "
                    + str(options)
                )
            if len(options) > 0 and value_type != "Select":
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + internal_name
                    + "' option specified but is not of type 'Select': "
                    + value_type
                )

            # parse description
            if "\n" in value:
                logger.info(
                    text
                    + " "
                    + field_type
                    + " '"
                    + internal_name
                    + "' description ("
                    + value
                    + ") contains a newline character, removing."
                )
                value = value.replace("\n", " ")

            # check that type is a known value
            if not FieldType.has_key(field_type):
                logger.warning(
                    text
                    + " '"
                    + internal_name
                    + "' field_type is Unknown: "
                    + field_type
                )

            # check that usage is a known value
            if not FieldUsage.has_key(field_usage):
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + internal_name
                    + "' has unknown 'usage' descriptor: "
                    + field_usage
                )

            # check that access is a known value
            if not FieldAccess.has_key(access.lower()):
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + internal_name
                    + "' has unknown 'access' descriptor: "
                    + access
                )

            # create a field from this data
            field = create_field(
                internal_name,
                default_value,
                value_type,
                field_type,
                field_usage,
                access,
                options,
                precious,
                positional,
                description,
            )

            # add the field to the fields list
            fields.append(field)

    # check for presence of extra fields that must be included for each
    # category
    check_required_fields_for_category(text, fields, category)

    # create and return the node
    GITREPO = os.environ.get("GIT_REPO")
    VERSION = os.environ.get("PROJECT_VERSION")
    return (
        {"tag": tag, "construct": construct},
        {
            "category": category,
            "key": get_next_key(),
            "text": text,
            "description": comp_description,
            "fields": fields,
            "repositoryUrl": GITREPO,
            "commitHash": VERSION,
            "paletteDownloadUrl": "",
            "dataHash": "",
        },
    )


def write_palette_json(
    output_filename: str,
    nodes: list,
    git_repo: str,
    version: str,
    block_dag: list,
):
    """
    Construct palette header and Write nodes to the output file

    :param output_filename: str, the name of the output file
    :param nodes: list of nodes
    :param git_repo: str, the git repository URL
    :param version: str, version string to be used
    :param block_dag: list, the reproducibility information
    """
    for i in range(len(nodes)):
        nodes[i]["dataHash"] = block_dag[i]["data_hash"]
    palette = constructPalette()
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


def process_compounddefs(
    output_xml_filename: str,
    tag: str,
    allow_missing_eagle_start: bool = True,
    language: Language = Language.PYTHON,
) -> list:
    """
    Extract and process the compounddef elements.

    :param output_xml_filename: str, File name for the XML file produced by
        doxygen
    :param tag: Tag, return only those components matching this tag
    :param allow_missing_eagle_start: bool, Treat non-daliuge tagged classes
        and functions
    :param language: Language, can be [2] for Python, 1 for C or 0 for Unknown

    :returns nodes
    """
    # load and parse the input xml file
    tree = ET.parse(output_xml_filename)

    xml_root = tree.getroot()
    # init nodes array
    nodes = []
    compounds = xml_root.findall("./compounddef")
    for compounddef in compounds:
        # are we processing an EAGLE component?
        eagle_tags = compounddef.findall(
            "./detaileddescription/para/simplesect/title"
        )
        is_eagle_node = False
        if (
            len(eagle_tags) == 2
            and eagle_tags[0].text == "EAGLE_START"
            and eagle_tags[1].text == "EAGLE_END"
        ):
            is_eagle_node = True
        compoundname = check_text_element(compounddef, "./compoundname")
        kind = compounddef.attrib["kind"]
        if kind not in ["class", "namespace"]:
            # we'll ignore this compound
            continue

        if is_eagle_node:
            params = process_compounddef_eagle(compounddef)

            ns = params_to_nodes(params, tag)
            nodes.extend(ns)

        if not is_eagle_node and allow_missing_eagle_start:  # not eagle node
            logger.info("Handling compound: %s", compoundname)
            # ET.tostring(compounddef, encoding="unicode"),
            # )
            functions = process_compounddef_default(compounddef, language)
            functions = functions[0] if len(functions) > 0 else functions
            logger.debug("Number of functions in compound: %d", len(functions))
            for f in functions:
                f_name = f["params"]["text"]
                logger.debug("Function names: %s", f_name)
                if f_name == [".Unknown"]:
                    continue

                ns = params_to_nodes(f["params"], "")

                for n in ns:
                    alreadyPresent = False
                    for node in nodes:
                        if node["text"] == n["text"]:
                            alreadyPresent = True

                    # print("component " + n["text"] + " alreadyPresent " +
                    # str(alreadyPresent))

                    if alreadyPresent:
                        # TODO: Originally this was suppressed, but in reality
                        # multiple functions with the same name are possible
                        logger.warning(
                            "Function has multiple entires: %s", n["text"]
                        )
                    if n["description"] == "" and f["description"] != "":
                        n["description"] = f["description"]
                    nodes.append(n)
        if not is_eagle_node and not allow_missing_eagle_start:
            logger.warning(
                "Non-EAGLE tagged component '%s' identified. "
                + "Not parsing it due to setting. "
                + "Consider using the -s flag.",
                compoundname,
            )
    return nodes


def process_compounddef_default(
    compounddef: ET.Element, language: Language
) -> list:
    """
    Process a compound definition

    :param compounddef: list of children of compounddef
    :param language: Language, can be [2] for Python, 1 for C or 0 for Unknown
    """
    result: list = []

    ctags = [c.tag for c in compounddef]
    tags = ctags.copy()
    logger.debug("Child elements found: %s", tags)

    # initialize the compound object
    tchild = compounddef[ctags.index("compoundname")]
    compound = Child(tchild, language)
    tags.pop(tags.index("compoundname"))

    # get the compound's detailed description
    # NOTE: This may contain all param information, e.g. for classes
    # and has to be merged with the descriptions found in sectiondef elements
    if tags.count("detaileddescription") > 0:
        tchild = compounddef[ctags.index("detaileddescription")]
        cdescrObj = Child(tchild, language, parent=compound)
        tags.pop(tags.index("detaileddescription"))
    compound.description = cdescrObj.description
    compound.format = cdescrObj.format

    # Handle all the other child elements
    for t in enumerate(ctags):
        if t[1] in tags:
            child = compounddef[t[0]]
            logger.debug(
                "Handling child: %s; using parent: %s", t, compound.type
            )
            childO = Child(child, language, parent=cdescrObj)
            if childO.members not in [None, []]:
                result.append(childO.members)
            else:
                continue
    return result


def process_compounddef_eagle(compounddef: Union[ET.Element, Any]) -> dict:
    """
    Interpret a compound definition element.

    :param compounddef: dict, the compounddef dictionary derived from the
                        respective element

    :returns dictionary

    TODO: This should be split up and make use of XPath expressions
    """
    result: dict = {}

    # get child of compounddef called "briefdescription"
    briefdescription = None
    for child in compounddef:
        if child.tag == "briefdescription":
            briefdescription = child
            break

    if briefdescription is not None:
        if len(briefdescription) > 0:
            if briefdescription[0].text is None:
                logger.warning("No brief description text")
                result["text"] = ""
            else:
                result["text"] = briefdescription[0].text.strip(" .")

    # get child of compounddef called "detaileddescription"
    detaileddescription = compounddef.find("./detaileddescription")

    # check that detailed description was found
    if detaileddescription is not None:
        # We know already that this is an EGALE node

        para = detaileddescription.findall("./para")  # get para elements
        description = check_text_element(para[0], ".")
        para = para[-1]
        if description is not None:
            result.update({"description": description.strip()})

    # check that we found the correct para
    if para is None:
        return result

    # find parameterlist child of para
    parameterlist = para.find("./parameterlist")  # type: ignore

    # check that we found a parameterlist
    if parameterlist is None:
        return result

    # read the parameters from the parameter list
    # TODO: refactor this as well
    for parameteritem in parameterlist:
        for pichild in parameteritem:
            if pichild.tag == "parameternamelist":
                key = pichild[0].text.strip()
            elif pichild.tag == "parameterdescription":
                if key == "gitrepo" and isinstance(pichild[0], list):
                    if pichild[0][0] is None or pichild[0][0].text is None:
                        logger.warning("No gitrepo text")
                        value = ""
                    else:
                        value = pichild[0][0].text.strip()
                else:
                    if pichild[0].text is None:
                        logger.warning("No key text (key: %s)", key)
                        value = ""
                    else:
                        value = pichild[0].text.strip()

        result.update({key: value})
    return result


def create_construct_node(node_type: str, node: dict) -> dict:
    """
    Create the special node for constructs.

    :param node_type: str, the type of the construct node to be created
    :param node: dict, node description (TODO: should be a node object)

    :returns dict of the construct node
    """
    # check that type is in the list of known types
    if node_type not in KNOWN_CONSTRUCT_TYPES:
        logger.warning(
            " construct for node'"
            + node["text"]
            + "' has unknown type: "
            + node_type
        )
        logger.info("Known types are: %s", KNOWN_CONSTRUCT_TYPES)
        pass

    if node_type == "Scatter":
        add_fields = [
            create_field(
                "num_of_copies",
                "4",
                "Integer",
                FieldType.ConstructParameter,
                FieldUsage.NoPort,
                FieldAccess.readwrite,
                [],
                False,
                False,
                "Specifies the number of replications "
                "that will be generated of the scatter construct's "
                "contents.",
            ),
            create_field(
                "dropclass",
                "dlg.apps.constructs.ScatterDrop",
                "String",
                FieldType.ComponentParameter,
                FieldUsage.NoPort,
                FieldAccess.readwrite,
                [],
                False,
                False,
                "Drop class",
            ),
        ]
    elif node_type == "MKN":
        add_fields = [
            create_field(
                "num_of_copies",
                "4",
                "Integer",
                FieldType.ConstructParameter,
                FieldUsage.NoPort,
                FieldAccess.readwrite,
                [],
                False,
                False,
                "Specifies the number of replications "
                "that will be generated of the scatter construct's "
                "contents.",
            ),
            create_field(
                "dropclass",
                "dlg.apps.constructs.MKNDrop",
                "String",
                FieldType.ComponentParameter,
                FieldUsage.NoPort,
                FieldAccess.readwrite,
                [],
                False,
                False,
                "Drop class",
            ),
        ]
    elif node_type == "Gather":
        add_fields = [
            create_field(
                "num_of_inputs",
                "4",
                "Integer",
                FieldType.ConstructParameter,
                FieldUsage.NoPort,
                FieldAccess.readwrite,
                [],
                False,
                False,
                "Specifies the number of inputs "
                "that that the gather construct will merge. "
                "If it is less than the available number of "
                "inputs, the translator will automatically "
                "generate additional gathers.",
            ),
            create_field(
                "dlg.apps.constructs.GatherDrop",
                "",
                "String",
                FieldType.ComponentParameter,
                FieldUsage.NoPort,
                FieldAccess.readwrite,
                [],
                False,
                False,
                "Drop class",
            ),
        ]
    else:
        add_fields = []  # don't add anything at this point.
    GITREPO = os.environ.get("GIT_REPO")
    VERSION = os.environ.get("PROJECT_VERSION")

    construct_node = {
        "category": node_type,
        "description": "A default "
        + node_type
        + " construct for the "
        + node["text"]
        + " component.",
        "fields": add_fields,
        "applicationArgs": [],
        "repositoryUrl": GITREPO,
        "commitHash": VERSION,
        "paletteDownloadUrl": "",
        "dataHash": "",
        "key": get_next_key(),
        "text": node_type + "/" + node["text"],
    }

    return construct_node


def params_to_nodes(params: dict, tag: str) -> list:
    """
    Generate a list of nodes from the params found

    :param params: list, the parameters to be converted

    :returns list of node dictionaries
    """
    # logger.debug("params_to_nodes: %s", params)
    result = []
    git_repo = ""
    version = "0.1"

    # if no params were found, or only the name and description were found,
    # then don't bother creating a node
    if len(params) > 2:
        # create a node

        # check if git_repo and version params were found and cache the values
        # TODO: This seems unnecessary remove?
        git_repo = params["gitrepo"] if "girepo" in params else ""
        version = params["version"] if "version" in params else ""

        data, node = create_palette_node_from_params(params)

        # if the node tag matches the command line tag, or no tag was specified
        # on the command line, add the node to the list to output
        if data["tag"] == tag or tag == "":  # type: ignore
            logger.info(
                "Adding component: "
                + node["text"]
                + " with "
                + str(len(node["fields"]))
                + " fields."
            )
            result.append(node)

            # if a construct is found, add to nodes
            if data["construct"] != "":
                logger.info(
                    "Adding component: "
                    + data["construct"]
                    + "/"
                    + node["text"]
                )
                construct_node = create_construct_node(data["construct"], node)
                construct_node["repositoryUrl"] = git_repo
                construct_node["commitHash"] = version
                result.append(construct_node)

    return result


def prepare_and_write_palette(nodes: list, output_filename: str):
    """
    Prepare and write the palette in JSON format.

    :param nodes: the list of nodes
    :param output_filename: the filename of the output
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
        output_filename, nodes, GITREPO, VERSION, block_dag  # type: ignore
    )
    logger.info("Wrote " + str(len(nodes)) + " component(s)")


def get_members(mod: types.ModuleType, parent=None, member=None):
    """
    Get members of a module
    """
    if not mod:
        return {}
    name = parent if parent else mod.__name__
    logger.debug(f">>>>>>>>> Analysing members for module: {name}")
    content = inspect.getmembers(
        mod,
        lambda x: inspect.isfunction(x)
        or inspect.isclass(x)
        or inspect.isbuiltin(x),
    )
    count = 0
    # logger.debug("Members of %s: %s", name, [c for c, m in content])
    members = {}
    for c, m in content:
        if not member or (member and c == member):
            if c[0] == "_" and c not in ["__init__", "__call__"]:
                # TODO: Deal with __init__
                # NOTE: PyBind11 classes can have multiple constructors
                continue
            m = getattr(mod, c)
            if not callable(m) or isinstance(m, _SpecialForm):
                # logger.warning("Member %s is not callable", m)
                # # TODO: not sure what to do with these. Usually they
                # # are class parameters.
                continue
            else:
                node = constructNode()
                count += 1
                name = (
                    f"{parent}.{m.__name__}"
                    if hasattr(m, "__name__")
                    else f"{mod.__name__}.Unknown"
                )
                logger.info("Inspecting %s: %s", type(m).__name__, m.__name__)

                dd = None
                if m.__doc__ and len(m.__doc__) > 0:
                    logger.info(
                        f"Process documentation of {type(m).__name__} {name}"
                    )
                    dd = DetailedDescription(m.__doc__)
                    logger.debug(f"Full description: {dd.description}")
                    node.description = dd.brief_descr.strip()
                    node.text = name
                    if len(dd.params) > 0:
                        logger.debug("Desc. parameters: %s", dd.params)
                elif hasattr(m, "__name__"):
                    logger.warning("Member '%s' has no description!", name)
                else:
                    logger.warning(
                        "Entity '%s' has neither descr. nor __name__", m
                    )

                if type(m).__name__ in [
                    "pybind11_type",
                    "builtin_function_or_method",
                ]:
                    logger.info(
                        "!!! PyBind11 or builtin: Creting dummy signature !!!"
                    )
                    sig = DummySig(m)
                else:
                    try:
                        # this will fail for e.g. pybind11 modules
                        sig = inspect.signature(m)  # type: ignore
                    except ValueError:
                        logger.warning(
                            "Unable to get signature of %s: ", m.__name__
                        )
                        continue
                # fill custom ApplicationArguments first
            fields = populateFields(sig.parameters, dd)
            for _, field in fields.items():
                node.fields.update(field)

            # now populate with default fields.
            node = populateDefaultFields(node)
            node.fields["func_name"]["value"] = name
            if hasattr(sig, "ret"):
                logger.debug("Return type: %s", sig.ret)
            logger.debug(
                ">>> member update with: %s", {name: node.dump_json_str()}
            )
            members.update({name: node})

            if hasattr(m, "__members__"):
                # this takes care of enum types, but needs some
                # serious thinking for DALiuGE. Note that enums
                # from PyBind11 have a generic type, but still
                # the __members__ dict.
                logger.info("\nMembers:")
                logger.info(m.__members__)
                # pass
            break
    logger.info("Analysed %d members in module %s", count, name)
    return members


def module_hook(
    mod_name: str, modules: dict = {}, recursive: bool = True
) -> "dict":
    """
    This is the starting point of a function dissecting the
    docs for an imported module.

    TODO: Generate palette from description and params.
    TODO: At some point this might be the main entry point for
    the whole parsing, but means that the module has to be installed.

    :param mod_name: str, the name of the module to be treated
    :param recursive: bool, treat sub-modules [True]

    :returns: dict of modules processed
    """
    member = None
    if mod_name not in sys.builtin_module_names:
        try:
            mod = import_using_name(mod_name)
            if mod_name != mod.__name__:
                member = mod_name.split(".")[-1]
                mod_name = mod.__name__
            modules.update(
                {mod_name: get_members(mod, parent=mod_name, member=member)}
            )
            # mod_count += 1
            if not member and recursive and mod:
                sub_modules = get_submodules(mod)
                # if len(sub_modules) > 0:
                logger.info("Iterating over sub_modules of %s", mod_name)
                for sub_mod in sub_modules:
                    logger.info("Treating sub-module: %s", sub_mod)
                    modules = module_hook(sub_mod, modules=modules)
            # member_count = sum([len(m) for m in modules.values()])
        except ImportError:
            logger.error("Module %s can't be loaded!", mod_name)
    return modules
