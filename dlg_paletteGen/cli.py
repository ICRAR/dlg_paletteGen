"""This is the palette generator of the DALiuGE system.

It processes a file or a directory of source files and
produces a DALiuGE compatible palette file containing the
information required to use functions and components in graphs.
For more information please refer to the documentation
https://daliuge.readthedocs.io/en/latest/development/app_development/eagle_app_integration.html#automatic-eagle-palette-generation

"""
import argparse
import logging
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from blockdag import build_block_dag

# isort: ignore
from dlg_paletteGen.base import (
    BLOCKDAG_DATA_FIELDS,
    DOXYGEN_SETTINGS,
    DOXYGEN_SETTINGS_C,
    DOXYGEN_SETTINGS_PYTHON,
    Language,
    logger,
    modify_doxygen_options,
    params_to_nodes,
    process_compounddef_default,
    process_compounddef_eagle,
    write_palette_json,
)


def get_args():
    """
    Deal with the command line arguments

    :returns (
                args.idir:str,
                args.tag:str,
                args.ofile:str,
                args.parse_all:bool,
                args.module:str,
                language)
    """
    # inputdir, tag, outputfile, allow_missing_eagle_start, module_path,
    # language
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("idir", help="input directory path or file name")
    parser.add_argument("ofile", help="output file name")
    parser.add_argument(
        "-m", "--module", help="Module load path name", default=""
    )
    parser.add_argument(
        "-t", "--tag", help="filter components with matching tag", default=""
    )
    parser.add_argument(
        "-c",
        help="C mode, if not set Python will be used",
        action="store_true",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="Traverse sub-directories",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--parse_all",
        help="Try to parse non DAliuGE compliant functions and methods",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase output verbosity",
        action="store_true",
    )
    if len(sys.argv) == 1:
        print(
            "\x1b[31;20mInsufficient number of arguments provided!!!\n\x1b[0m"
        )
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    logger.setLevel(logging.INFO)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    logger.debug("DEBUG logging switched on")
    if args.recursive:
        DOXYGEN_SETTINGS.append(("RECURSIVE", "YES"))
        logger.info("Recursive flag ON")
    else:
        DOXYGEN_SETTINGS.append(("RECURSIVE", "NO"))
        logger.info("Recursive flag OFF")
    language = Language.C if args.c else Language.PYTHON
    return (
        args.idir,
        args.tag,
        args.ofile,
        args.parse_all,
        args.module,
        language,
    )


def check_environment_variables() -> bool:
    """
    Check environment variables and set them if not defined.

    :returns True
    """
    required_environment_variables = [
        "PROJECT_NAME",
        "PROJECT_VERSION",
        "GIT_REPO",
    ]

    for variable in required_environment_variables:
        value = os.environ.get(variable)

        if value is None:
            if variable == "PROJECT_NAME":
                os.environ["PROJECT_NAME"] = os.path.basename(
                    os.path.abspath(".")
                )
            elif variable == "PROJECT_VERSION":
                os.environ["PROJECT_VERSION"] = "0.1"
            elif variable == "GIT_REPO":
                os.environ["GIT_REPO"] = os.environ["PROJECT_NAME"]

    return True


def main():  # pragma: no cover
    """
    The main function executes on commands:
    `python -m dlg_paletteGen` and `$ dlg_paletteGen `.
    """
    # read environment variables
    if not check_environment_variables():
        sys.exit(1)
    (
        inputdir,
        tag,
        outputfile,
        allow_missing_eagle_start,
        module_path,
        language,
    ) = get_args()
    logger.info("PROJECT_NAME:" + os.environ.get("PROJECT_NAME"))
    logger.info("PROJECT_VERSION:" + os.environ.get("PROJECT_VERSION"))
    logger.info("GIT_REPO:" + os.environ.get("GIT_REPO"))

    logger.info("Input Directory:" + inputdir)
    logger.info("Tag:" + tag)
    logger.info("Output File:" + outputfile)
    logger.info("Allow missing EAGLE_START:" + str(allow_missing_eagle_start))
    logger.info("Module Path:" + module_path)

    # create a temp directory for the output of doxygen
    output_directory = tempfile.TemporaryDirectory()

    # add extra doxygen setting for input and output locations
    DOXYGEN_SETTINGS.append(("PROJECT_NAME", os.environ.get("PROJECT_NAME")))
    DOXYGEN_SETTINGS.append(("INPUT", inputdir))
    DOXYGEN_SETTINGS.append(("OUTPUT_DIRECTORY", output_directory.name))

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

    # run xsltproc
    output_xml_filename = output_directory.name + "/xml/doxygen.xml"

    with open(output_xml_filename, "w") as outfile:
        subprocess.call(
            [
                "xsltproc",
                output_directory.name + "/xml/combine.xslt",
                output_directory.name + "/xml/index.xml",
            ],
            stdout=outfile,
            stderr=subprocess.DEVNULL,
        )

    # debug - copy output xml to local dir
    os.system("cp " + output_xml_filename + " output.xml")
    logger.info("Wrote doxygen XML to output.xml")

    # get environment variables
    gitrepo = os.environ.get("GIT_REPO")
    version = os.environ.get("PROJECT_VERSION")

    # init nodes array
    nodes = []

    # load the input xml file
    tree = ET.parse(output_xml_filename)
    xml_root = tree.getroot()

    for compounddef in xml_root:

        # debug - we need to determine this correctly
        is_eagle_node = False

        if is_eagle_node or not allow_missing_eagle_start:
            params = process_compounddef_eagle(compounddef)

            ns = params_to_nodes(params)
            nodes.extend(ns)

        else:  # not eagle node
            logger.info("Handling compound: %s", compounddef)
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

    # add signature for whole palette using BlockDAG
    vertices = {}
    for i in range(len(nodes)):
        vertices[i] = nodes[i]
    block_dag = build_block_dag(vertices, [], data_fields=BLOCKDAG_DATA_FIELDS)

    # write the output json file
    write_palette_json(outputfile, nodes, gitrepo, version, block_dag)
    logger.info("Wrote " + str(len(nodes)) + " component(s)")

    # cleanup the output directory
    output_directory.cleanup()
