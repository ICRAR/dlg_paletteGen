"""
dlg_paletteGen base module.

TODO: This whole tool needs re-factoring into separate class files
(compound, child, grandchild, grandgrandchild, node, param, pluggable parsers)
Should also be made separate sub-repo with proper installation and entry point.

"""
import csv
import json
import os
import xml.etree.ElementTree as ET
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

NAME = "dlg_paletteGen"

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

KNOWN_FIELD_TYPES = [
    "ComponentParameter",
    "ApplicationArgument",
    "InputPort",
    "OutputPort",
]

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

    :return dict: {
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


def check_required_fields_for_category(text: str, fields: list, category: str):
    """
    Check if fields have mandatory content and alert with <text> if not.

    :param text: str, the text to be used for the alert
    :param fields: list of field dicts to be checked
    :param category: str, category to be checked
    """
    if category in [
        "DynlibApp",
        "PythonApp",
        "Branch",
        "BashShellApp",
        "Mpi",
        "Docker",
    ]:
        alert_if_missing(text, fields, "execution_time")
        alert_if_missing(text, fields, "num_cpus")

    if category in [
        "DynlibApp",
        "PythonApp",
        "Branch",
        "BashShellApp",
        "Docker",
    ]:
        alert_if_missing(text, fields, "group_start")

    if category == "DynlibApp":
        alert_if_missing(text, fields, "libpath")

    if category in ["PythonApp", "Branch"]:
        alert_if_missing(text, fields, "appclass")

    if category in [
        "File",
        "Memory",
        "NGAS",
        "ParameterSet",
        "Plasma",
        "PlasmaFlight",
        "S3",
    ]:
        alert_if_missing(text, fields, "data_volume")

    if category in [
        "File",
        "Memory",
        "NGAS",
        "ParameterSet",
        "Plasma",
        "PlasmaFlight",
        "S3",
        "Mpi",
    ]:
        alert_if_missing(text, fields, "group_end")

    if category in ["BashShellApp", "Mpi", "Docker", "Singularity"]:
        alert_if_missing(text, fields, "input_redirection")
        alert_if_missing(text, fields, "output_redirection")
        alert_if_missing(text, fields, "command_line_arguments")
        alert_if_missing(text, fields, "paramValueSeparator")
        alert_if_missing(text, fields, "argumentPrefix")


def create_field(
    internal_name: str,
    external_name: str,
    value: str,
    value_type: str,
    field_type: str,
    access: str,
    options: str,
    precious: bool,
    positional: bool,
    description: str,
):
    """
    TODO: field should be a dataclass
    For now just create a dict using the values provided

    :param internal_name: str, the internal name of the parameter
    :param external_name: str, the visible name of the parameter
    :param value: str, the value of the parameter
    :param value_type: str, the type of the value
    :param field_type: str, the type of the field
    :param access: str, readwrite|readonly (default readonly)
    :param options: str, options
    :param precious: bool,
        should this parameter appear, even if empty or None
    :param positional: bool,
        is this a positional parameter
    :param description: str, the description used in the palette

    :returns field: dict
    """
    return {
        "text": external_name,
        "name": internal_name,
        "value": value,
        "defaultValue": value,
        "description": description,
        "type": value_type,
        "fieldType": field_type,
        "readonly": access == "readonly",
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
            message + " component missing " + internal_name + " cparam"
        )
        pass


def parse_value(message: str, value: str) -> tuple:
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

    # init attributes of the param
    external_name = ""
    default_value = ""
    value_type = "String"
    field_type = "cparam"
    access = "readwrite"
    options: list = []
    precious = False
    positional = False
    description = ""

    # assign attributes (if present)
    if len(parts) > 0:
        external_name = parts[0]
    if len(parts) > 1:
        default_value = parts[1]
    if len(parts) > 2:
        value_type = parts[2]
    if len(parts) > 3:
        field_type = parts[3]
    if len(parts) > 4:
        access = parts[4]
    else:
        logger.warning(
            message
            + " "
            + field_type
            + " ("
            + external_name
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
            message
            + " "
            + field_type
            + " ("
            + external_name
            + ") has no 'options', using default ([]) : "
            + value
        )
    if len(parts) > 6:
        precious = parts[6].lower() == "true"
    else:
        logger.warning(
            message
            + " "
            + field_type
            + " ("
            + external_name
            + ") has no 'precious' descriptor, using default (False) : "
            + value
        )
    if len(parts) > 7:
        positional = parts[7].lower() == "true"
    else:
        logger.warning(
            message
            + " "
            + field_type
            + " ("
            + external_name
            + ") has no 'positional', using default (False) : "
            + value
        )
    if len(parts) > 8:
        description = parts[8]

    return (
        external_name,
        default_value,
        value_type,
        field_type,
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
    inputPorts: list = []
    outputPorts: list = []
    inputLocalPorts: list = []
    outputLocalPorts: list = []
    fields: list = []
    applicationArgs: list = []

    # process the params
    for param in params:
        if not isinstance(param, dict):
            logger.error(
                "param %s has wrong type %s. Ignoring!", param, type(param)
            )
            continue
        key = param["key"]
        # direction = param["direction"]
        value = param["value"]

        if key == "category":
            category = value
        elif key == "construct":
            construct = value
        elif key == "tag" and not any(s in value for s in KNOWN_FIELD_TYPES):
            tag = value
        elif key == "text":
            text = value
        elif key == "description":
            comp_description = value
        else:
            internal_name = key
            (
                external_name,
                default_value,
                value_type,
                field_type,
                access,
                options,
                precious,
                positional,
                description,
            ) = parse_value(text, value)

            # check that type is in the list of known types
            if value_type not in KNOWN_PARAM_DATA_TYPES:
                # logger.warning(text + " " + field_type + " '" + name + "' has
                #  unknown type: " + type)
                pass

            # check that a param of type "Select" has some options specified,
            # and check that every param with some options specified is of type
            # "Select"
            if value_type == "Select" and len(options) == 0:
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + external_name
                    + "' is of type 'Select' but has no options specified: "
                    + str(options)
                )
            if len(options) > 0 and value_type != "Select":
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + external_name
                    + "' has at least one option specified but is not of type "
                    + "'Select': "
                    + value_type
                )

            # parse description
            if "\n" in value:
                logger.info(
                    text
                    + " description ("
                    + value
                    + ") contains a newline character, removing."
                )
                value = value.replace("\n", " ")

            # check that access is a known value
            if access != "readonly" and access != "readwrite":
                logger.warning(
                    text
                    + " "
                    + field_type
                    + " '"
                    + external_name
                    + "' has unknown 'access' descriptor: "
                    + access
                )

            # create a field from this data
            field = create_field(
                internal_name,
                external_name,
                default_value,
                value_type,
                field_type,
                access,
                options,
                precious,
                positional,
                description,
            )

            # add the field to the correct list in the component, based on
            # fieldType
            if field_type in KNOWN_FIELD_TYPES:
                fields.append(field)
            else:
                logger.warning(
                    text
                    + " '"
                    + external_name
                    + "' field_type is Unknown: "
                    + field_type
                )

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
            "drawOrderHint": 0,
            "key": get_next_key(),
            "text": text,
            "description": comp_description,
            "collapsed": False,
            "showPorts": False,
            "subject": None,
            "selected": False,
            "expanded": False,
            "inputApplicationName": "",
            "outputApplicationName": "",
            "inputApplicationType": "None",
            "outputApplicationType": "None",
            "inputPorts": inputPorts,
            "outputPorts": outputPorts,
            "inputLocalPorts": inputLocalPorts,
            "outputLocalPorts": outputLocalPorts,
            "inputAppFields": [],
            "outputAppFields": [],
            "fields": fields,
            "applicationArgs": applicationArgs,
            "repositoryUrl": GITREPO,
            "commitHash": VERSION,
            "paletteDownloadUrl": "",
            "dataHash": "",
        },
    )


def write_palette_json(
    outputfile: str, nodes: list, gitrepo: str, version: str, block_dag: list
):
    """
    Construct palette header and Write nodes to the output file

    :param outputfile: str, the name of the output file
    :param nodes: list of nodes
    :param gitrepo: str, the gitrepo URL
    :param version: str, version string to be used
    :param block_dag: list, the reproducibility information
    """
    for i in range(len(nodes)):
        nodes[i]["dataHash"] = block_dag[i]["data_hash"]
    palette = {
        "modelData": {
            "fileType": "palette",
            "repoService": "GitHub",
            "repoBranch": "master",
            "repo": "ICRAR/EAGLE_test_repo",
            "readonly": True,  # type: ignore
            "filePath": outputfile,
            "repositoryUrl": gitrepo,
            "commitHash": version,
            "downloadUrl": "",
            "signature": block_dag["signature"],  # type: ignore
        },
        "nodeDataArray": nodes,
        "linkDataArray": [],
    }  # type: ignore

    # write palette to file
    with open(outputfile, "w") as outfile:
        json.dump(palette, outfile, indent=4)


def process_compounddefs(
    output_xml_filename: str,
    allow_missing_eagle_start: bool = True,
    language: Language = Language.PYTHON,
) -> list:
    """
    Extract and process the compounddef elements.

    :param output_xml_filename: str, File name for the XML file produced by
        doxygen
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

            ns = params_to_nodes(params)
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

                ns = params_to_nodes(f["params"])

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
                "None EAGLE tagged component '%s' identified. "
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
        logger.info("Kown types are: %s", KNOWN_CONSTRUCT_TYPES)
        pass

    if node_type in ["Scatter", "MKN"]:
        add_fields = [
            {
                "text": "Scatter dimension",
                "name": "num_of_copies",
                "value": 4,
                "defaultValue": 4,
                "description": "Specifies the number of replications "
                "that will be generated of the scatter construct's "
                "contents.",
                "readonly": False,
                "type": "Integer",
                "precious": False,
                "options": [],
                "positional": False,
                "keyAttribute": False,
            }
        ]
    elif node_type == "Gather":
        add_fields = [
            {
                "text": "Gather power",
                "name": "num_of_inputs",
                "value": 4,
                "defaultValue": 4,
                "description": "Specifies the number of inputs "
                "that that the gather construct will merge. "
                "If it is less than the available number of "
                "inputs, the translator will automatically "
                "generate additional gathers.",
                "readonly": False,
                "type": "Integer",
                "precious": False,
                "options": [],
                "positional": False,
                "keyAttribute": False,
            }
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

    if node_type in ["Scatter", "Gather", "MKN"]:
        construct_node["inputAppFields"] = node["fields"]
        construct_node["inputAppArgs"] = node["applicationArgs"]
        construct_node["inputApplicationKey"] = node["key"]
        construct_node["inputApplicationName"] = node["text"]
        construct_node["inputApplicationType"] = node["category"]
        construct_node["inputApplicationDescription"] = node["description"]
        construct_node["inputLocalPorts"] = node["outputPorts"]
        construct_node["inputPorts"] = node["inputPorts"]
        construct_node["outputAppFields"] = []
        construct_node["outputAppArgs"] = []
        construct_node["outputApplicationKey"] = None
        construct_node["outputApplicationName"] = ""
        construct_node["outputApplicationType"] = "None"
        construct_node["outputApplicationDescription"] = ""
        construct_node["outputLocalPorts"] = []
        construct_node["outputPorts"] = []
    else:
        pass  # not sure what to do for branch

    return construct_node


def params_to_nodes(params: list) -> list:
    """
    Generate a list of nodes from the params found

    :param params: list, the parameters to be converted

    :returns list of node dictionaries
    """
    # logger.debug("params_to_nodes: %s", params)
    result = []
    tag = ""
    gitrepo = ""
    version = "0.1"

    # if no params were found, or only the name and description were found,
    # then don't bother creating a node
    if len(params) > 2:
        # create a node

        # check if gitrepo and version params were found and cache the values
        # TODO: This seems unneccessary remove?
        for param in params:
            logger.debug("param: %s", param)
            if not param:
                continue
            key, value = (param["key"], param["value"])
            if key == "gitrepo":
                gitrepo = value
            elif key == "version":
                version = value

        data, node = create_palette_node_from_params(params)

        # if the node tag matches the command line tag, or no tag was specified
        # on the command line, add the node to the list to output
        if data["tag"] == tag or tag == "":  # type: ignore
            logger.debug("Adding component: " + node["text"])
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
                construct_node["repositoryUrl"] = gitrepo
                construct_node["commitHash"] = version
                result.append(construct_node)

    return result


def prepare_and_write_palette(nodes: list, outputfile: str):
    """
    Prepare and write the palette in JSON format.

    :param nodes: the list of nodes
    :param outputfile: the name of the outputfile
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
        outputfile, nodes, GITREPO, VERSION, block_dag  # type: ignore
    )
    logger.info("Wrote " + str(len(nodes)) + " component(s)")
