# pylint: disable=consider-using-with
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
from typing import Any

import pkg_resources

from .module_base import module_hook
from .settings import DOXYGEN_SETTINGS, Language, logger
from .source_base import process_compounddefs
from .support_functions import (
    get_submodules,
    import_using_name,
    prepare_and_write_palette,
    process_doxygen,
    process_xml,
)

NAME = "dlg_paletteGen"
VERSION = pkg_resources.require(NAME)[0].version


def get_args(args=None):
    # def get_args():
    """
    Deal with the command line arguments

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
    parser.add_argument("-m", "--module", help="Module load path name", default="")
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
        "-S",
        "--split",
        help="Split into sub-module palettes",
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
            print("\x1b[31;20mInsufficient number of " + "arguments provided!!!\n\x1b[0m")
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
        args.ofile = args.idir = "."
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


def nodes_from_module(module_path, recursive=True) -> tuple[list, Any]:
    """
    Extract nodes from specified module.

    :param modules: modules dict as extracted by module_hook
    :param recursive: flag indicating wether to recurse down the hierarchy

    :returns: list of nodes (for now)
    """
    modules, module_doc = module_hook(module_path, recursive=recursive)
    logger.debug(">>>>> Number of modules/members processed: %d", len(modules))
    logger.debug(
        "Modules/members found: %s",
        # modules
        {m: list(v.keys()) for m, v in modules.items() if v},
    )
    nodes = []
    for members in modules.values():
        for node in members.values():
            # TODO: remove once EAGLE can deal with dict fields pylint: disable=fixme
            if isinstance(node["fields"], list):
                continue
            node["fields"] = list(node["fields"].values())
            nodes.append(node)
    return nodes, module_doc


def palettes_from_module(
    module_path: str,
    outfile: str = "",
    split: bool = False,
    recursive: bool = True,
) -> None:
    """
    Generates one or more palette files from the module specified.

    :param module_path: dot delimited module path
    :param outfile: name of palette file, if left blank the module name will be
                     used. If split is True and a name is specified it will be
                     prepended to the module name(s).
    :param split: If True (default False), the module will be split into
                  palettes one for each sub-module.
    :param recursive: flag indicating wether to recurse down the hierarchy

    returns: None
    """
    module_doc = ""
    files = {}
    sub_modules = [module_path]
    if split:
        mod = import_using_name(module_path, traverse=True)
        sub_modules = [module_path] + list(get_submodules(mod)[0])
        # sub_modules, _ = [module_path, module_hook(module_path)]
        logger.info(
            "Splitting module %s into sub-module palettes: %s",
            module_path,
            sub_modules,
        )
        top_recursive = recursive
    else:
        sub_modules = [module_path]
        top_recursive = False
    for i, m in enumerate(sub_modules):
        logger.debug("Extracting nodes from module: %s", m)
        top_recursive = False if i == 0 else True
        nodes, module_doc = nodes_from_module(m, recursive=top_recursive)
        if len(nodes) == 0:
            continue
        filename = outfile if not split else f"{outfile}{m.replace('.','_')}.palette"
        files[filename] = len(nodes)
        _ = prepare_and_write_palette(nodes, filename, module_doc=module_doc)
        logger.debug(
            "%s palette file written with %s components\n%s",
            filename,
            len(nodes),
            m,
        )
    logger.info(
        "\n\n>>>>>>> Extraction summary <<<<<<<<\n%s\n",
        "\n".join([f"Wrote {k} with {v} components" for k, v in files.items()]),
    )


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
