import subprocess
import logging
import os
import json
from dlg_paletteGen.cli import NAME
from dlg_paletteGen.base import (
    Language,
    prepare_and_write_palette,
    process_compounddefs,
)
from dlg_paletteGen.support_functions import (
    DOXYGEN_SETTINGS,
    process_doxygen,
    process_xml,
)
from dlg_paletteGen.cli import check_environment_variables

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
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 8


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
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 17


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
    # ret_code == 2 because it failed
    assert p.returncode == 1
    # The CLI output should contain a short help message
    assert err[:26] == b"usage: dlg_paletteGen [-h]"


def test_direct_numpy(tmpdir: str, shared_datadir: str):
    """ "
    Test the numpy format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    # inputdir,
    # tag,
    # outputfile,
    # allow_missing_eagle_start,
    # module_path,
    # language,
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
    # inputdir,
    # tag,
    # outputfile,
    # allow_missing_eagle_start,
    # module_path,
    # language,
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
    # inputdir,
    # tag,
    # outputfile,
    # allow_missing_eagle_start,
    # module_path,
    # language,
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
    assert len(newcontent["nodeDataArray"][0]["fields"]) == 8


def test_direct_oskar(tmpdir: str, shared_datadir: str):
    """ "
    Test the oskar (modified google) format by calling the methods directly.

    :param tmpdir: the path to the temp directory to use
    :param shared_datadir: the path the the local directory
    """
    # inputdir,
    # tag,
    # outputfile,
    # allow_missing_eagle_start,
    # module_path,
    # language,
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
    # inputdir,
    # tag,
    # outputfile,
    # allow_missing_eagle_start,
    # module_path,
    # language,
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
    # inputdir,
    # tag,
    # outputfile,
    # allow_missing_eagle_start,
    # module_path,
    # language,
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
