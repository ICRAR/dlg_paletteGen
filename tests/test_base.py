# pylint: disable=too-few-public-methods
import inspect
import json
import logging
import os
import subprocess
import sys

import numpy
from pytest import LogCaptureFixture

from dlg_paletteGen.settings import DOXYGEN_SETTINGS
from dlg_paletteGen.__main__ import check_environment_variables, get_args
from dlg_paletteGen.module_base import module_hook, nodes_from_module
from dlg_paletteGen.source_base import Language, process_compounddefs
from dlg_paletteGen.support_functions import (
    guess_type_from_default,
    import_using_name,
    prepare_and_write_palette,
    process_doxygen,
    process_xml,
    NAME,
    this_module,
    typeFix,
)

pytest_plugins = ["pytester", "pytest-datadir"]


def start_process(args=(), **subproc_args):
    """
    Start 'dlg_paletteGen <args>' in a different process.

    This method returns the new process.
    """

    cmdline = ["dlg_paletteGen"]
    if args:
        cmdline.extend(args)
    return subprocess.Popen(cmdline, **subproc_args)


# class MainTest(unittest.TestCase):
def test_base():
    assert NAME == "dlg_paletteGen"


def test_CLI_run_numpy(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_numpy.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-r", "-s", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 9


def test_CLI_run_google(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_google.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-r", "-s", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 9


def test_CLI_run_eagle(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_eagle.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-r", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 6


def test_CLI_run_rest(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_rest.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-sr", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 9


def test_CLI_run_rascil(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_rascil.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-sr", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 12


def test_CLI_run_casatask(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_casatask.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-rs", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert newcontent["modelData"]["commitHash"] == "0.1"


def test_CLI_run_nr(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inputf = str(shared_datadir.absolute()) + "/example_casatask.py"
    logging.info("path: %s", inputf)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-s", "-v", inputf, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _ = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(inputf, "r", encoding="utf8") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 14


def test_CLI_fail():
    """
    Test the CLI just using no params should return help text

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    p = start_process(
        (),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, err = p.communicate()
    assert p.returncode == 1
    assert err[:26] == b"usage: dlg_paletteGen [-h]"


def test_CLI_module(tmpdir: str, shared_datadir: str):
    """
    Test the CLI using the module hook on itself

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    inp = str(shared_datadir.absolute())  # don't really need this
    output = tmpdir + "t.palette"
    p = start_process(
        ("-rsm", "json", inp, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, err = p.communicate()
    # assert p.returncode == 0
    logging.info("Captured output: %s", err)

    # Once we have output we can re-enable this
    # with open(input, "r") as f:
    #     content = f.read()
    # logging.info("INPUT: %s", content)
    # with open(output, "r") as f:
    #     newcontent = json.load(f)
    # logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    # assert newcontent["modelData"]["commitHash"] == "0.1"


def test_direct_cli():
    """
    Execute the cli directly to test the code itself.
    """

    class CliArgs:
        """
        Arguments for CLI
        """

        idir = "."
        tag = ""
        ofile = "."
        parse_all = False
        module = "dlg_paletteGen"
        recursive = True
        verbose = False
        split = False
        c = False
        prevent_cyclic = False
        quiet = False

        def __len__(self):
            return 10

    a = CliArgs()
    res = get_args(args=a)
    assert res[:3] == (".", "", "dlg_paletteGen.palette")


def test_direct_numpy(tmpdir: str, shared_datadir: str):
    """
    Test the numpy format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_numpy.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 9


def test_direct_rEST(tmpdir: str, shared_datadir: str):
    """
    Test the module processing format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    sys.path.append(str(shared_datadir.absolute()))
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"

    module_name = "example_rest"
    modules, module_doc = module_hook(
        module_name,
        modules={},
        recursive=True,
    )
    assert modules["example_rest"]["MainClass1.func_with_types"]["fields"]["arg1"][
        "type"
    ] in ["Boolean", "bool"]

    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)


def test_direct_google(tmpdir: str, shared_datadir: str):
    """ "
    Test the google format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_google.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 9


def test_direct_eagle(tmpdir: str, shared_datadir: str):
    """ "
    Test the numpy format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = False
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_eagle.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 6


def test_direct_oskar(tmpdir: str, shared_datadir: str):
    """ "
    Test the oskar (modified google) format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_oskar.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 8


def test_direct_rascil(tmpdir: str, shared_datadir: str):
    """ "
    Test the rascil format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_rascil.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 12


def test_direct_functions(tmpdir: str, shared_datadir: str):
    """ "
    Test the functions (modified google) format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_functions.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 5


def test_direct_casatask(tmpdir: str, shared_datadir: str):
    """ "
    Test the casatask format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    inputf = str(shared_datadir.absolute()) + "/example_casatask.py"
    logging.info("path: %s", inputf)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": inputf})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r", encoding="utf8") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 14


def test_direct_tabascal(tmpdir: str, shared_datadir: str):
    """
    Test the module processing format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    sys.path.append(str(shared_datadir.absolute()))
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"

    # module_name = "example_tabascal.generate_random_sky"
    module_name = "example_tabascal"
    modules, module_doc = module_hook(
        module_name,
        modules={},
        recursive=True,
    )
    assert (
        modules["example_tabascal"]["example_tabascal.generate_random_sky"]["fields"][
            "fov"
        ]["value"]
        == 1.0
    )

    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)
    prepare_and_write_palette(nodes, output_file, module_doc=module_doc)


def test_direct_pypeit(tmpdir: str, shared_datadir: str):
    """
    Test the module processing format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    sys.path.append(str(shared_datadir.absolute()))
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"

    # module_name = "example_tabascal.generate_random_sky"
    module_name = "example_pypeit"
    modules, module_doc = module_hook(
        module_name,
        modules={},
        recursive=True,
    )
    assert (
        modules["example_pypeit"]["example_pypeit.poly_map"]["fields"]["rawimg"]["type"]
        == "numpy.ndarray"
    )

    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)
    prepare_and_write_palette(nodes, output_file, module_doc=module_doc)


def test_import_using_name(caplog: LogCaptureFixture):
    """
    Directly test the import_using_name function

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    # module_name = "urllib.request.URLopener.retrieve"
    module_name = "numpy.array"
    mod = import_using_name(module_name, traverse=True)
    assert mod.__module__ == "numpy"

    module_name = "urllib.request.URLopener.retrieve"
    mod = import_using_name(module_name, traverse=True)
    assert mod.__module__ == "urllib.request"

    module_name = "print"
    mod = import_using_name(module_name, traverse=True)
    assert mod.__name__ == "print"


def test_typeFix(tmpdir: str, shared_datadir: str):
    """
    Test the type guessing functions
    """
    sys.path.append(str(shared_datadir.absolute()))
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"

    module_name = "example_options.testFieldSingle"
    modules, module_doc = module_hook(
        module_name,
        modules={},
        recursive=True,
    )
    assert list(modules.keys())[-1] == "testFieldSingle"
    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)
    prepare_and_write_palette(nodes, output_file, module_doc=module_doc)


def test_guess_type_from_default():
    """
    Test the function
    """
    assert guess_type_from_default(234) == "Integer"
    assert guess_type_from_default(234.0) == "Float"
    assert guess_type_from_default("[2,3,4]") == "List"
    assert guess_type_from_default({234}) == "Object"


def test_direct_module(tmpdir: str, shared_datadir: str):
    """
    Test the module processing format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    sys.path.append(str(shared_datadir.absolute()))
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"

    module_name = "dlg_paletteGen.module_base"
    nodes, module_doc = nodes_from_module(module_name, recursive=True)

    prepare_and_write_palette(nodes, output_file, module_doc=module_doc)
    assert len(nodes) == 17


def test_builtin_function(tmpdir: str, shared_datadir: str):
    """
    Test the module processing format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    sys.path.append(str(shared_datadir.absolute()))
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"

    module_name = "print"
    nodes, module_doc = nodes_from_module(module_name, recursive=True)

    prepare_and_write_palette(nodes, output_file, module_doc=module_doc)
    assert len(nodes) == 1


def test_full_numpy():
    """
    Test loading all of numpy. This takes a bit of time.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    module_name = "numpy.polynomial.polynomial"
    nodes = nodes_from_module(module_name, recursive=True)
    assert len(nodes[0]) in [42, 43]


def test_this_module():
    """
    Test loading this module.
    """
    module = this_module()
    assert module == "tests.test_base"


def test_typeFix():
    """
    Test loading the type_fix function.
    """
    values = [
        int,
        float,
        str,
        list,
        dict,
        tuple,
        set,
        bool,
        None,
        inspect._empty,
        type(numpy.array([])),
    ]
    guess_type = set()
    for v in values:
        guess_type.add(typeFix(v))
    assert guess_type == {
        "str",
        "builtins.tuple",
        "Boolean",
        "list",
        "int",
        "builtins.set",
        "dict",
        "ndarray",
        "float",
        "None",
    }
