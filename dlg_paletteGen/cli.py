"""This is the palette generator of the DALiuGE system.

It processes a file or a directory of source files and
produces a DALiuGE compatible palette file containing the
information required to use functions and components in graphs.
For more information please refer to the documentation
https://icrar.github.io/dlg_paletteGen/

"""
import argparse
import logging
import os
import sys
import tempfile

import pkg_resources

# isort: ignore
from dlg_paletteGen.base import (
    Language,
    logger,
    prepare_and_write_palette,
    process_compounddefs,
)
from dlg_paletteGen.support_functions import (
    DOXYGEN_SETTINGS,
    process_doxygen,
    process_xml,
)

NAME = "dlg_paletteGen"
VERSION = pkg_resources.require(NAME)[0].version


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
        description=__doc__ + f"\nVersion: {VERSION}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V",
        "--version",
        help="show tool version and exit",
        action="version",
        version=f"{NAME} version: {VERSION}",
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
        help="Parse non DAliuGE compliant functions and methods",
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
        DOXYGEN_SETTINGS.update({"RECURSIVE": "YES"})
        logger.info("Recursive flag ON")
    else:
        DOXYGEN_SETTINGS.update({"RECURSIVE": "NO"})
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
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputdir})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory.name})

    process_doxygen(language=language)
    output_xml_filename = process_xml()

    # get environment variables
    # gitrepo = os.environ.get("GIT_REPO")
    # version = os.environ.get("PROJECT_VERSION")

    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, outputfile)
    # cleanup the output directory
    output_directory.cleanup()
