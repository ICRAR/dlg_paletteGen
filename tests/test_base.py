import json
import logging
import os
import subprocess
import sys
import unittest

from dlg_paletteGen.settings import DOXYGEN_SETTINGS, guess_type_from_default
from dlg_paletteGen.cli import NAME, check_environment_variables, get_args
from dlg_paletteGen.module_base import module_hook
from dlg_paletteGen.source_base import Language, process_compounddefs
from dlg_paletteGen.support_functions import (
    import_using_name,
    prepare_and_write_palette,
    process_doxygen,
    process_xml,
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
    input = str(shared_datadir.absolute()) + "/example_numpy.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-r", "-s", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 11


def test_CLI_run_google(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    input = str(shared_datadir.absolute()) + "/example_google.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-r", "-s", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 11


def test_CLI_run_eagle(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    input = str(shared_datadir.absolute()) + "/example_eagle.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-r", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
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
    input = str(shared_datadir.absolute()) + "/example_rest.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-sr", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 11


def test_CLI_run_rascil(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    input = str(shared_datadir.absolute()) + "/example_rascil.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-sr", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 14


def test_CLI_run_casatask(tmpdir: str, shared_datadir: str):
    """
    Test the CLI just using input and output.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    input = str(shared_datadir.absolute()) + "/example_casatask.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-rs", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
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
    input = str(shared_datadir.absolute()) + "/example_casatask.py"
    logging.info("path: %s", input)
    output = tmpdir + "t.palette"
    p = start_process(
        ("-s", "-v", input, output),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()
    assert p.returncode == 0
    # logging.info("Captured output: %s", err)
    with open(input, "r") as f:
        content = f.read()
    logging.info("INPUT: %s", content)
    with open(output, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 16


def test_CLI_fail(tmpdir: str, shared_datadir: str):
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
    out, err = p.communicate()
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
    out, err = p.communicate()
    assert p.returncode == 0
    # # logging.info("Captured output: %s", err)

    # TODO: Once we have output we can re-enable this
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

    class args:
        idir = "."
        tag = ""
        ofile = "t.palette"
        parse_all = False
        module = "dlg_paletteGen"
        recursive = True
        verbose = False
        split = False
        c = False
        quiet = False

        def __len__(self):
            return 10

    a = args()
    res = get_args(args=a)
    assert res[:3] == (".", "", "t.palette")


def test_direct_numpy(tmpdir: str, shared_datadir: str):
    """ "
    Test the numpy format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    input = str(shared_datadir.absolute()) + "/example_numpy.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 11


def test_direct_google(tmpdir: str, shared_datadir: str):
    """ "
    Test the google format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    input = str(shared_datadir.absolute()) + "/example_google.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 11


def test_direct_eagle(tmpdir: str, shared_datadir: str):
    """ "
    Test the numpy format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = False
    language = Language.PYTHON
    input = str(shared_datadir.absolute()) + "/example_eagle.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
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
    input = str(shared_datadir.absolute()) + "/example_oskar.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 10


def test_direct_rascil(tmpdir: str, shared_datadir: str):
    """ "
    Test the rascil format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    input = str(shared_datadir.absolute()) + "/example_rascil.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 14


def test_direct_functions(tmpdir: str, shared_datadir: str):
    """ "
    Test the functions (modified google) format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    input = str(shared_datadir.absolute()) + "/example_functions.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 7


def test_direct_casatask(tmpdir: str, shared_datadir: str):
    """ "
    Test the casatask format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    tag = ""
    allow_missing_eagle_start = True
    language = Language.PYTHON
    input = str(shared_datadir.absolute()) + "/example_casatask.py"
    logging.info("path: %s", input)
    output_directory = str(tmpdir)
    output_file = f"{output_directory}/t.palette"
    check_environment_variables()
    DOXYGEN_SETTINGS.update({"PROJECT_NAME": os.environ.get("PROJECT_NAME")})
    DOXYGEN_SETTINGS.update({"INPUT": input})
    DOXYGEN_SETTINGS.update({"OUTPUT_DIRECTORY": output_directory})
    process_doxygen()
    output_xml_filename = process_xml()
    nodes = process_compounddefs(
        output_xml_filename, tag, allow_missing_eagle_start, language
    )
    prepare_and_write_palette(nodes, output_file)

    with open(output_file, "r") as f:
        newcontent = json.load(f)
    logging.info("OUTPUT: %s", newcontent)
    # can't use a hash, since output contains hashed keys
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 16


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
    module_name = "example_tabascal.generate_random_sky"
    modules, module_doc = module_hook(
        module_name,
        recursive=True,
    )
    assert (
        modules["example_tabascal"]["generate_random_sky"]["fields"]["fov"]["value"]
        == 1.0
    )

    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)
    prepare_and_write_palette(nodes, output_file, module_doc=module_doc)


def test_import_using_name(tmpdir: str, shared_datadir: str, caplog):
    """
    Directly test the import_using_name function

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    # module_name = "urllib.request.URLopener.retrieve"
    module_name = "numpy.array"
    mod = import_using_name(module_name, traverse=True)
    assert mod.__name__ == "numpy"

    module_name = "urllib.request.URLopener.retrieve"
    mod = import_using_name(module_name, traverse=True)
    assert mod.__name__ == "urllib.request"

    module_name = "print"
    mod = import_using_name(module_name, traverse=True)
    assert "Error when loading module print" in caplog.text


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
        recursive=True,
    )
    assert list(modules.keys())[-1] == "example_options"
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
    assert guess_type_from_default("[2,3,4]") == "Json"
    assert guess_type_from_default({234}) == "Object"


def test_direct_module(tmpdir: str, shared_datadir: str):
    """
    Test the module processing format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    # module_name = "dlg_paletteGen.classes"
    module_name = "numpy.array"
    modules, module_doc = module_hook(module_name, recursive=True)
    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)
    assert len(nodes) in [1, 2]
    prepare_and_write_palette(nodes, "test.palette", module_doc=module_doc)


@unittest.skip
def test_full_numpy(tmpdir: str, shared_datadir: str):
    """
    Test loading all of numpy. This takes a bit of time.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    module_name = "numpy"
    modules, module_doc = module_hook(module_name, recursive=True)
    nodes = []
    for members in modules.values():
        for node in members.values():
            nodes.append(node)
    assert len(modules) in [1109, 1112]
