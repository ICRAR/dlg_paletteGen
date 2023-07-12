"""
dlg_paletteGen base module.

TODO: This whole tool needs re-factoring into separate class files
(compound, child, grandchild, grandgrandchild, node, param, pluggable parsers)
Should also be made separate sub-repo with proper installation and entry point.

"""
import csv
import datetime
import json
import os
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Any, Union

from blockdag import build_block_dag

from dlg_paletteGen.classes import Child
from dlg_paletteGen.support_functions import (
    Language,
    check_text_element,
    create_uuid,
    get_next_key,
    logger,
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


def create_port(
    component_name,
    internal_name,
    external_name,
    direction,
    event,
    value_type,
    description,
) -> dict:
    """
    Create the dict data structure used to describe a port
    TODO: This should be a dataclass

    :param component_name: str, the name of the component
    :param internal_name: str, the identifier name for the component
    :param external_name: str, the display name of the component
    :param direction: str, ['input'|'output']
    :param event: str, if event this string contains event name
    :param value_type: str, type of the port (not limited to standard data
                       types)
    :param description: str, short description of the port

    :returns dict: {
                    'Id':uuid,
                    'IdText': internal_name,
                    'text': external_name,
                    'event': event,
                    'type': value_type,
                    'description': description
                    }
    """
    seed = {
        "component_name": component_name,
        "internal_name": internal_name,
        "external_name": external_name,
        "direction": direction,
        "event": event,
        "type": value_type,
        "description": description,
    }

    port_uuid = create_uuid(str(seed))

    return {
        "Id": str(port_uuid),
        "IdText": internal_name,
        "text": external_name,
        "event": event,
        "type": value_type,
        "description": description,
    }


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
    :param field_type: FieldType, the type of the field
    :param field_usage: FieldUsage, type usage of the field
    :param access: FieldAccess, ReadWrite|ReadOnly (default ReadOnly)
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
    for param in params:
        # abort if param is not a dictionary
        if not isinstance(param, dict):
            logger.error(
                "param %s has wrong type %s. Ignoring!", param, type(param)
            )
            continue

        # read data from param
        key = param["key"]
        value = param["value"]

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
    palette = {
        "modelData": {
            "filePath": output_filename,
            "fileType": "palette",
            "shortDescription": "",
            "detailedDescription": "",
            "repoService": "GitHub",
            "repoBranch": "master",
            "repo": "ICRAR/EAGLE_test_repo",
            "eagleVersion": "",
            "eagleCommitHash": "",
            "schemaVersion": "AppRef",
            "readonly": True,  # type: ignore
            "repositoryUrl": git_repo,
            "commitHash": version,
            "downloadUrl": "",
            "signature": block_dag["signature"],  # type: ignore
            "lastModifiedName": "",
            "lastModifiedEmail": "",
            "lastModifiedDatetime": datetime.datetime.now().timestamp() * 1000,
        },
        "nodeDataArray": nodes,
        "linkDataArray": [],
    }  # type: ignore

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
                f_name = [
                    k["value"] for k in f["params"] if k["key"] == "text"
                ]
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
    result = []

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


def process_compounddef_eagle(compounddef: Union[ET.Element, Any]) -> list:
    """
    Interpret a compound definition element.

    :param compounddef: dict, the compounddef dictionary derived from the
                        respective element

    :returns list of dictionaries

    TODO: This should be split up and make use of XPath expressions
    """
    result = []

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
                result.append({"key": "text", "direction": None, "value": ""})
            else:
                result.append(
                    {
                        "key": "text",
                        "direction": None,
                        "value": briefdescription[0].text.strip(" ."),
                    }
                )

    # get child of compounddef called "detaileddescription"
    detaileddescription = compounddef.find("./detaileddescription")

    # check that detailed description was found
    if detaileddescription is not None:
        # We know already that this is an EGALE node

        para = detaileddescription.findall("./para")  # get para elements
        description = check_text_element(para[0], ".")
        para = para[-1]
        if description is not None:
            result.append(
                {
                    "key": "description",
                    "direction": None,
                    "value": description.strip(),
                }
            )

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
        key = None
        direction = None
        value = None
        for pichild in parameteritem:
            if pichild.tag == "parameternamelist":
                key = pichild[0].text.strip()
                direction = pichild[0].attrib.get("direction", "").strip()
            elif pichild.tag == "parameterdescription":
                if key == "gitrepo" and isinstance(pichild[0], list):
                    # the gitrepo is a URL, so is contained within a <ulink>
                    # element,
                    # therefore we need to use pichild[0][0] here to look one
                    # level deeper
                    # in the hierarchy
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

        result.append({"key": key, "direction": direction, "value": value})
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
                "dropclass",
                "dlg.apps.constructs.GatherDrop",
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


def params_to_nodes(params: list, tag: str) -> list:
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
        for param in params:
            logger.debug("param: %s", param)
            if not param:
                continue
            key, value = (param["key"], param["value"])
            if key == "gitrepo":
                git_repo = value
            elif key == "version":
                version = value

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
