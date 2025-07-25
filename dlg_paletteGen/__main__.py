# pylint: disable=consider-using-with
"""
This is the palette generator of the DALiuGE system.

It produces a DALiuGE compatible palette file containing the
information required to use functions and components in graphs.

It operates in two main modes:

1) module mode: when providing a module name using the -m flag.
   In this mode dlg_paletteGen tries to import the module and
   then uses introspection to identify classes, methods and functions
   and their arguments along with the documentation, if available
   in-line. It also tries to infer the types of arguments.

2) source code mode: this is used when the -m flag does not exist.
   It is using the first positional parameter as an input file or
   directory name and uses doxygen to extract the documentation as
   XML. It then parses the XML to derive the same information as
   when called with a module name.
   Special flags:  # noqa: RST301
      The -t flag allows to filter DALiuGE specific components.
      The -s flag allows to



For more information please refer to the documentation
https://icrar.github.io/dlg_paletteGen/

"""

import argparse
import logging
import os
import sys
import tempfile

from dlg_paletteGen.module_base import palettes_from_module
from dlg_paletteGen.settings import DOXYGEN_SETTINGS, Language
from dlg_paletteGen.source_base import process_compounddefs
from dlg_paletteGen.support_functions import (
    NAME,
    VERSION,
    prepare_and_write_palette,
    process_doxygen,
    process_xml,
)

from . import logger


def get_args(args=None):
    # def get_args():
    """
    Deal with the command line arguments.

    :returns: (
                args.idir:str,
                args.tag:str,
                args.ofile:str,
                args.parse_all:bool,
                args.module:str,
                args.recursive:bool,
                args.split:bool,
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
        "-m",
        "--module",
        help="Module load path name (if set idir is ignored)",
        default="",
    )
    parser.add_argument(
        "-t",
        "--tag",
        help="filter components with matching tag (only applicable in source mode)",
        default="",
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
        "-S",
        "--split",
        help="Split into sub-module palettes "
        + "(ofile is ignored, only applicable in module mode)",
        action="store_true",
        default=False,
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
        help="DEBUG level logging",
        action="store_true",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        help="Only critical logging",
        action="store_true",
    )
    if not args:
        if len(sys.argv) == 1:
            print("\x1b[31;20mInsufficient number of arguments provided!!!\n\x1b[0m")
            parser.print_help(sys.stderr)
            sys.exit(1)
        args = parser.parse_args()
    logger.setLevel(logging.INFO)
    if args.quiet:
        logger.setLevel(logging.CRITICAL)
    elif args.verbose:
        logger.setLevel(logging.DEBUG)
    logger.debug("DEBUG logging switched on")
    if args.module:
        args.idir = "."  # ignore whatever is provided as idir
        args.parse_all = True  # in module mode parse everything
    if args.module and not args.split and args.ofile == ".":
        args.ofile = f"{args.module.replace('.','_')}.palette"
    if args.recursive:
        DOXYGEN_SETTINGS.update({"RECURSIVE": "YES"})
        logger.info("Recursive flag ON")
    else:
        DOXYGEN_SETTINGS.update({"RECURSIVE": "NO"})
        logger.info("Recursive flag OFF")
    language = Language.C if args.c else Language.PYTHON
    if args.split:
        logger.info("Split flag ON")
    else:
        args.split = False
    return (
        args.idir,
        args.tag,
        args.ofile,
        args.parse_all,
        args.module,
        args.recursive,
        args.split,
        language,
    )


def check_environment_variables() -> bool:
    """
    Check environment variables and set them if not defined.

    :returns: True
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
                os.environ["PROJECT_NAME"] = os.path.basename(os.path.abspath("."))
            elif variable == "PROJECT_VERSION":
                os.environ["PROJECT_VERSION"] = "0.1"
            elif variable == "GIT_REPO":
                os.environ["GIT_REPO"] = os.environ["PROJECT_NAME"]

    return True


def main():  # pragma: no cover
    """
    Execute the commands.

    `python -m dlg_paletteGen` and `$ dlg_paletteGen`.
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
        recursive,
        split,
        language,
    ) = get_args()
    logger.info("PROJECT_NAME: %s", os.environ.get("PROJECT_NAME"))
    logger.info("PROJECT_VERSION: %s", os.environ.get("PROJECT_VERSION"))
    logger.info("GIT_REPO: %s", os.environ.get("GIT_REPO"))

    logger.info("Input Directory: %s", inputdir)
    logger.info("Tag: %s", tag)
    logger.info("Output File: %s", outputfile)
    logger.info("Allow missing EAGLE_START: %s", str(allow_missing_eagle_start))
    logger.info("Module Path: %s", module_path)

    # create a temp directory for the output of doxygen
    output_directory = tempfile.TemporaryDirectory()

    if len(module_path) > 0:
        outputfile = "" if outputfile == "." else outputfile
        palettes_from_module(
            module_path, outfile=outputfile, recursive=recursive, split=split
        )
    else:
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
        _ = prepare_and_write_palette(nodes, outputfile)
    # cleanup the output directory
    output_directory.cleanup()
