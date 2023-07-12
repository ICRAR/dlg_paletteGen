import re
import xml.etree.ElementTree as ET
from typing import Union

from dlg_paletteGen.support_functions import (
    VALUE_TYPES,
    Language,
    cleanString,
    logger,
    typeFix,
)


class DetailedDescription:
    """
    Class performs parsing of detailed description elements.
    This class is used for both compound (e.g. class) level descriptions
    as well as function/method level.
    """

    KNOWN_FORMATS = {
        "rEST": r"\n(:param|:returns|Returns:) .*",
        "Google": r"\nArgs:",
        "Numpy": r"\nParameters\n----------",
        "casa": r"\n-{2,20}? parameter",
    }

    def __init__(self, descr: str):
        """
        :param descr: Text of the detaileddescription node
        """
        self.description = descr
        self.format = ""
        self._identify_format()
        self.main_descr, self.params = self.process_descr()

    def _process_rEST(self, detailed_description) -> tuple:
        """
        Parse parameter descirptions found in a detailed_description tag. This
        assumes rEST style documentation.

        :param detailed_description: str, the content of the description XML
                                     node

        :returns: tuple, description and parameter dictionary
        """
        logger.debug("Processing rEST style doc_strings")
        result = {}

        if detailed_description.find("Returns:") >= 0:
            split_str = "Returns:"
        elif detailed_description.find(":returns") >= 0:
            split_str = ":returns"
        else:
            split_str = ""
        detailed_description = (
            detailed_description.split(split_str)[0]
            if split_str
            else detailed_description
        )
        param_lines = [
            p.replace("\n", "").strip()
            for p in detailed_description.split(":param")[1:]
        ]
        type_lines = [
            p.replace("\n", "").strip()
            for p in detailed_description.split(":type")[1:]
        ]
        # param_lines = [line.strip() for line in detailed_description]

        for p_line in param_lines:
            # logger.debug("p_line: %s", p_line)

            try:
                index_of_second_colon = p_line.index(":", 0)
            except ValueError:
                # didnt find second colon, skip
                # logger.debug("Skipping this one: %s", p_line)
                continue

            param_name = p_line[:index_of_second_colon].strip()
            param_description = p_line[
                index_of_second_colon + 2 :  # noqa: E203
            ].strip()  # noqa: E203
            t_ind = param_description.find(":type")
            t_ind = t_ind if t_ind > -1 else None
            param_description = param_description[:t_ind]
            # logger.debug("%s description: %s", param_name,
            # param_description)

            if len(type_lines) != 0:
                result.update(
                    {param_name: {"desc": param_description, "type": None}}
                )
            else:
                result.update(
                    {
                        param_name: {
                            "desc": param_description,
                            "type": typeFix(
                                re.split(
                                    r"[,\s\n]", param_description.strip()
                                )[0]
                            ),
                        }
                    }
                )

        for t_line in type_lines:
            # logger.debug("t_line: %s", t_line)

            try:
                index_of_second_colon = t_line.index(":", 0)
            except ValueError:
                # didnt find second colon, skip
                # logger.debug("Skipping this one: %s", t_line)
                continue

            param_name = t_line[:index_of_second_colon].strip()
            param_type = t_line[
                index_of_second_colon + 2 :  # noqa: E203
            ].strip()
            p_ind = param_type.find(":param")
            p_ind = p_ind if p_ind > -1 else None
            param_type = param_type[:p_ind]
            param_type = typeFix(param_type)

            # if param exists, update type
            if param_name in result:
                result[param_name]["type"] = param_type
            else:
                logger.warning(
                    "Type spec without matching description %s", param_name
                )

        return detailed_description.split(":param")[0], result

    def _process_Numpy(self, dd: str) -> tuple:
        """
        Process the Numpy-style docstring

        :param dd: str, the content of the detailed description tag

        :returns: tuple, description and parameter dictionary
        """
        logger.debug("Processing Numpy style doc_strings")
        ds = dd
        # ds = "\n".join(
        #     [d.strip() for d in dd.split("\n")]
        # )  # remove whitespace from lines
        # extract main documentation (up to Parameters line)
        (description, rest) = ds.split("\nParameters\n----------\n")
        has_params = description != rest
        # extract parameter documentation (up to Returns line)
        pds = re.split(r"\nReturns\n-------\n", rest)
        spds = re.split(r"([\w_]+) : ", pds[0])[1:]  # split param lines
        if has_params and len(spds) == 0:
            spds = re.split(r"([\w_]+)\n    ", pds[0])[1:]  # split param lines
        pdict = dict(zip(spds[::2], spds[1::2]))  # create initial param dict
        pdict = {
            k: {
                "desc": v.replace("\n", " "),
                # this cryptic line tries to extract the type
                "type": typeFix(re.split(r"[,\n\s]", v.strip())[0]),
            }
            for k, v in pdict.items()
        }
        logger.debug("numpy_style param dict %r", pdict)
        # extract return documentation
        rest = pds[1] if len(pds) > 1 else ""
        return description, pdict

    def _process_Google(self, dd: str):
        """
        Process the Google-style docstring
        TODO: not yet implemented

        :param dd: str, the content of the detailed description tag

        :returns: tuple, description and parameter dictionary
        """
        logger.debug("Processing Google style doc_strings")
        indent = len(re.findall(r"[ ]", re.findall(r"\n[ ]*Args:", dd)[0]))
        dd = dd.replace(" " * indent, "")
        # remove indent from lines
        # extract main documentation (up to Parameters line)
        (description, rest) = dd.split("\nArgs:\n")
        # logger.debug("Splitting: %s %s", description, rest)
        # extract parameter documentation (up to Returns line)
        pds = rest.split("\nReturns:\n")[0]
        indent = len(re.findall(r"^ +", pds)[0])
        pds = re.sub(r"\n" + r" " * indent, "\n", pds)  # remove indentation

        # split param lines
        spds = re.split(r"[\n ]+([\w_]+)\s?\(([`\:\w+\.\[\]\, ]+)\)\s?:", pds)[
            1:
        ]
        pdict = dict(
            zip(spds[::3], zip(spds[1::3], spds[2::3]))
        )  # create initial param dict
        pdict = {
            k: {
                "desc": v[1].replace("\n", " ").strip(),  # type: ignore
                "type": typeFix(v[0]),  # type: ignore
            }
            for k, v in pdict.items()
        }
        # extract return documentation
        rest = pds[1] if len(pds) > 1 else ""
        return description, pdict

    def _process_casa(self, dd: str):
        """
        Parse the special docstring for casatasks
        Extract the parameters from the casatask doc string.

        :param task: The casatask to derive the parameters from.

        :returns: Dictionary of form {<paramKey>:<paramDoc>}

        TODO: Description of component still missing in palette!
        TODO: ports are not populated
        TODO: type of self is not Object.ClassName
        TODO: self arg should show brief description of component
        TODO: multi-line argument doc-strings are scrambled
        """
        dStr = cleanString(dd)
        dList = dStr.split("\n")
        try:
            start_ind = [
                idx
                for idx, s in enumerate(dList)
                if re.findall(r"-{1,20} parameter", s)
            ][0] + 1
            end_ind = [
                idx
                for idx, s in enumerate(dList)
                if re.findall(r"-{1,20} example", s)
            ][0]
        except IndexError:
            logger.debug(
                "Problems finding start or end index for task: {task}"
            )
            return {}, ""
        paramsList = dList[start_ind:end_ind]
        paramsSidx = [
            idx + 1
            for idx, p in enumerate(paramsList)
            if len(p) > 0 and p[0] != " "
        ]
        paramsEidx = paramsSidx[1:] + [len(paramsList) - 1]
        paramFirstLine = [
            (p.strip().split(" ", 1)[0], p.strip().split(" ", 1)[1].strip())
            for p in paramsList
            if len(p) > 0 and p[0] != " "
        ]
        paramNames = [p[0] for p in paramFirstLine]
        paramDocs = [p[1].strip() for p in paramFirstLine]
        for i in range(len(paramDocs)):
            if paramsSidx[i] < paramsEidx[i]:
                pl = [
                    p.strip()
                    for p in paramsList[
                        paramsSidx[i] : paramsEidx[i] - 1  # noqa: E203
                    ]
                    if len(p.strip()) > 0
                ]
                paramDocs[i] = paramDocs[i] + " " + " ".join(pl)
        params = dict(zip(paramNames, paramDocs))
        comp_description = "\n".join(
            dList[: start_ind - 1]
        )  # return main description as well
        logger.debug(">>> CASA: finished processing of descr: %s", params)
        return (comp_description, params)

    def _identify_format(self):
        """
        Identifying docstring format using the format templates
        defined in KNOWN_FORMATS.
        """
        logger.debug("Identifying doc_string style format")
        ds = self.description if self.description else ""
        if ds and ds.count("\n") > 0:
            dd = self.description.split("\n")
            ds = "\n".join([d.strip() for d in dd])
        for k, v in self.KNOWN_FORMATS.items():
            rc = re.compile(v)
            if rc.search(ds):
                self.format = k
        if not self.format:
            logger.warning("Unknown param desc format!")

    def process_descr(self):
        """
        Helper function to provide plugin style parsers for various
        formats.
        """
        do = f"_process_{self.format}"
        if hasattr(self, do) and callable(func := getattr(self, do)):
            logger.debug("Calling %s parser function", do)
            return func(self.description)
        else:
            logger.warning("Format not recognized or can't execute %s", do)
            logger.warning("Returning description unparsed!")
            return (self.description, {})


class GreatGrandChild:
    """
    The great-grandchild class performs most of the parsing to construct the
    palette nodes from the doxygen XML.
    """

    def __init__(
        self,
        ggchild: ET.Element = ET.Element("dummy"),
        func_name: str = "Unknown",
        return_type: str = "Unknown",
        parent_member: Union["Child", None] = None,
    ):
        """
        Constructor of great-grandchild object.

        :param ggchild: dict, if existing great-grandchild
        :param func_name: str, the function name
        :param return_type: str, the return type of the component
        :param parent_member: dict, contains the descriptions found in parent
        """

        self.func_path = ""
        self.func_name = func_name
        self.func_title = func_name
        self.return_type = return_type
        self.is_init = False
        self.is_init = False
        self.is_classmethod = False
        self.is_member = False
        if ggchild:
            self.member = self.process_GreatGrandChild(
                ggchild, parent_member=parent_member
            )
        else:
            self.member = {"params": []}

    def process_GreatGrandChild(
        self, ggchild: ET.Element, parent_member: Union["Child", None] = None
    ):
        """
        Process GreatGrandChild

        :param ggchild: dict, the great grandchild element
        :param parent_member: dict, member dict from parent class
        """

        # logger.debug("Initialized ggchild member: %s", self.member)
        logger.debug(
            "New GreatGrandChild element: %s", ggchild.tag  # type: ignore
        )
        if ggchild.tag == "name":  # type: ignore
            self.func_name = (
                ggchild.text  # type: ignore
                if self.func_name == "Unknown"
                else self.func_name
            )
            logger.debug("Function name: %s", self.func_name)
        elif ggchild.tag == "argsstring":  # type: ignore
            args = ggchild.text[1:-1]  # type: ignore
            args = [a.strip() for a in args.split(",")]
            if "cls" in args:
                self.func_title = self.func_title.replace(".", "@")
            elif "self" in args:
                self.func_title = self.func_title.replace(".", "::")
            self.member["params"].append(
                {"key": "text", "value": self.func_title}
            )

        elif ggchild.tag == "detaileddescription":  # type: ignore
            # this contains the main description of the function and the
            # parameters.
            # Might not be complete or correct and has to be merged with
            # the information in the param section below.
            if (
                len(ggchild) > 0
                and len(ggchild[0]) > 0
                and ggchild[0][0].text is not None
            ):
                # get detailed description text
                dd = ggchild[0][0].text
                ddO = DetailedDescription(dd)
                if ddO.format:
                    (desc, params) = (ddO.main_descr, ddO.params)
                else:
                    (desc, params) = dd, {}

                # use the params above
                for p_key, p_value in params.items():
                    self.set_param_description(
                        p_key,
                        p_value["desc"],
                        p_value["type"],
                        self.member["params"],
                    )
                if self.is_classmethod:
                    desc = f"_@classmethod_: {desc}"
                elif self.is_member:
                    desc = f"_::memberfunction_: {desc}"
                logger.debug(
                    "adding description param: %s",
                    {"key": "description", "value": desc},
                )
                self.member["params"].append(
                    {"key": "description", "value": desc}
                )

        elif ggchild.tag == "param":  # type: ignore
            # Depending on the format used this section only contains
            # parameter names
            # this should be merged with the detaileddescription element
            # above, keeping in
            # mind that the description might be wrong and/or incomplete.
            value_type = ""
            name = ""
            default_value = ""

            for gggchild in ggchild:
                if gggchild.tag == "type":
                    value_type = gggchild.text  # type:ignore
                    if value_type not in VALUE_TYPES.values():
                        value_type = f"Object.{value_type}"
                    # also look at children with ref tag
                    for ggggchild in gggchild:
                        if ggggchild.tag == "ref":
                            value_type = ggggchild.text  # type:ignore
                if gggchild.tag == "declname":
                    name = gggchild.text  # type:ignore
                if gggchild.tag == "defname":
                    name = gggchild.text  # type:ignore
                if gggchild.tag == "defval":
                    default_value = gggchild.text  # type:ignore
            name = str(name)
            if (
                name in self.member["params"]
                and "type" in self.member["params"][name]
            ):
                logger.debug(
                    "Existing type definition found for %s: %s",
                    name,
                    self.member["params"][name]["type"],
                )
                value_type = self.member["params"][name]["type"]

            # type recognised - else convert?
            value_type = typeFix(value_type, default_value=default_value)

            # add the param
            if str(value_type) == "String":
                default_value = str(default_value).replace("'", "")
                if default_value.find("/") >= 0:
                    default_value = f'"{default_value}"'
            # attach description from parent, if available
            if parent_member and name in parent_member.member["params"]:
                member_desc = parent_member.member["params"][name]
            else:
                member_desc = ""
            if name in ["self", "cls"]:
                port = (
                    "InputPort"
                    if self.func_name[-8:] not in ["__init__", "__call__"]
                    else "OutputPort"
                )
                if name == "cls":
                    name = "self"
                    self.is_classmethod = True
                    port = "OutputPort"
                    value_type = "Object.self"
                elif name == "self":
                    self.is_member = True
                access = "readonly"
                member_desc = "Object reference"
            else:
                access = "readwrite"
                port = "NoPort"
            value = (
                f"{default_value}/{value_type}/ApplicationArgument/{port}/"
                + f"{access}//False/False/{member_desc}"
            )
            logger.debug(
                "adding param: %s", {"key": str(name), "value": value}
            )
            self.member["params"].append({"key": name, "value": value})

        elif ggchild.tag == "definition":  # type: ignore
            self.return_type = ggchild.text.strip().split(" ")[  # type: ignore
                0
            ]
            func_path = ggchild.text.strip().split(" ")[-1]  # type: ignore
            # skip function if it begins with a single underscore,
            # but keep __init__ and __call__
            if func_path.find(".") >= 0:
                self.func_path, self.func_name = func_path.rsplit(".", 1)
            logger.info(
                "Found function name: '%s:%s'",
                self.func_path,
                self.func_name,
            )

            if self.func_name in ["__init__", "__call__"]:
                self.is_init = True
                self.func_title = (
                    f"{self.func_path.rsplit('.',1)[-1]}.{self.func_name}"
                )
                self.func_name = self.func_path
                logger.debug(
                    "Using name %s for %s function",
                    self.func_path,
                    self.func_name,
                )
            elif (
                self.func_name.startswith("_")
                or self.func_path.find("._") >= 0
            ):
                logger.debug("Skipping %s.%s", self.func_path, self.func_name)
                self.member = None  # type: ignore
            else:
                self.func_title = (
                    f"{self.func_path.rsplit('.',1)[-1]}.{self.func_name}"
                )
                self.func_name = f"{self.func_path}.{self.func_name}"
            if self.member:
                self.return_type = (
                    "None" if self.return_type == "def" else self.return_type
                )
                self.member["params"].append(
                    {
                        "key": "input_parser",
                        "value": "pickle/Select/"
                        + "ComponentParameter/NoPort/readwrite/pickle,eval,"
                        + "npy,path,dataurl/False/False/Input port "
                        + "parsing technique",
                    }
                )
                self.member["params"].append(
                    {
                        "key": "output_parser",
                        "value": "pickle/Select/"
                        + "ComponentParameter/NoPort/readwrite/pickle,eval,"
                        + "npy,path,dataurl/False/False/Output port parsing "
                        + "technique",
                    }
                )
                self.member["params"].append(
                    {
                        "key": "func_name",
                        "value": self.func_name
                        + "/String/ComponentParameter/NoPort/readonly/"
                        + "/False/False/Name of function",
                    }
                )
        else:
            logger.debug(
                "Ignored great grandchild element: %s",
                ggchild.tag,  # type: ignore
            )

    def set_param_description(
        self, name: str, description: str, p_type: str, params: dict
    ):
        """
        Set the description field of a of parameter <name> from parameters.
        TODO: This should really be part of a class

        :param name: str, the parameter to set the description
        :param descrition: str, the description to add to the existing string
        :param p_type: str, the type of the parameter if known
        :param params: dict, the set of parameters
        """
        p_type = "" if not p_type else p_type
        for p in params:
            if p["key"] == name:
                p["value"] = p["value"] + description
                # insert the type
                pp = p["value"].split("/", 2)
                p["value"] = "/".join(pp[:1] + [p_type] + pp[2:])
                p["type"] = p_type
                break


class Child:
    def __init__(
        self,
        child: ET.Element,
        language: Language,
        parent: Union["Child", None] = None,
    ):
        """
        Private function to process a child element.

        :param child: dict, the parsed child element from XML
        :param language,
        :param parent, Child, parent object or None
        """
        members = []
        self.type = "generic"
        self.member: dict = {"params": []}
        self.format = ""
        self.description = ""
        self.casa_mode: bool = False
        # logger.debug("Initialized child member: %s", member)

        logger.debug(
            "Found child element: %s with tag: %s; kind: %s; parent: %s",
            child,
            child.tag,  # type: ignore
            child.get("kind"),
            parent.type if parent else "<unavailable>",
        )
        if parent and hasattr(parent, "casa_mode"):
            self.casa_mode = parent.casa_mode
        if (
            child.tag == "detaileddescription"  # type: ignore
            and len(child) > 0
        ):
            logger.debug("Parsing detaileddescription")
            # logger.debug("Child: %s", ET.tostring(child, encoding="unicode"))
            self.type = "description"
            # TODO: The following likely means that we are dealing with a C
            #       module and this is just a dirty workaround rather than
            #        a fix probably need to add a plain C parser.
            dStr = child[0][0].text if len(child[0]) > 0 else child[0]
            self.description = dStr  # type: ignore
            ddO = DetailedDescription(dStr)  # type: ignore
            self.format = ddO.format
            if self.format == "casa":
                self.casa_mode = True
                self.description, self.member["params"] = (
                    ddO.main_descr,
                    ddO.params,
                )

        if child.tag == "sectiondef" and child.get("kind") in [  # type: ignore
            "func",
            "public-func",
        ]:
            self.type = "function"
            logger.debug(
                "Processing %d grand children; parent: %s",
                len(child),
                parent.member if parent else "<undefined>",
            )
            for grandchild in child:
                gmember = self._process_grandchild(
                    grandchild,
                    language,
                    # parent=self
                )
                if gmember is None:
                    logger.debug("Bailing out of grandchild processing!")
                    continue
                elif gmember != self.member:
                    # logger.debug("Adding grandchild members: %s", gmember)
                    self.member["params"].extend(gmember["params"])
                    members.append(gmember)
            logger.debug("Finished processing grand children")
        self.members = members

    def _process_grandchild(
        self,
        gchild: ET.Element,
        language: Language,
        # parent: Union["Child", None] = None,
    ) -> Union[dict, None]:
        """
        Private function to process a grandchild element
        Starts the construction of the member data structure

        :param gchild: dict, the parsed grandchild element from XML
        :param language: int, the languange indicator flag,
                        0 unknown, 1: Python, 2: C

        :returns: dict, the member data structure
        """
        member: dict = {"params": []}
        # logger.debug("Initialized grandchild member: %s", member)

        if (
            gchild.tag == "memberdef"  # type: ignore
            and gchild.get("kind") == "function"
        ):
            logger.debug("Start processing of new function definition.")

            if language == Language.C:
                member["params"].append(
                    {
                        "key": "category",
                        "value": "DynlibApp",
                    }
                )
                member["params"].append(
                    {
                        "key": "libpath",
                        "value": " //String/ComponentParameter/NoPort/"
                        + "readwrite//False/False/The location of the shared "
                        + "object/DLL that implements this application",
                    }
                )
            elif language == Language.PYTHON:
                member["params"].append(
                    {
                        "key": "category",
                        "value": "PythonApp",
                    }
                )
                member["params"].append(
                    {
                        "key": "dropclass",
                        "value": "dlg.apps.pyfunc.PyFuncApp/"
                        + "String/ComponentParameter/NoPort/readonly//False/"
                        + "False/"
                        + "The python class that implements this application",
                    }
                )

            member["params"].append(
                {
                    "key": "execution_time",
                    "value": "5/Integer/ComponentParameter/NoPort/"
                    + "readwrite//False/False/Estimate of execution time "
                    + "(in seconds) for this application.",
                }
            )
            member["params"].append(
                {
                    "key": "num_cpus",
                    "value": "1/Integer/ComponentParameter/NoPort/"
                    + "readwrite//False/False/Number of cores used.",
                }
            )
            member["params"].append(
                {
                    "key": "group_start",
                    "value": "false/Boolean/ComponentParameter/NoPort/"
                    + "readwrite//False/False/Is this node the start of "
                    + "a group?",
                }
            )

            logger.debug("Processing %d great grand children", len(gchild))
            gg = GreatGrandChild()
            for ggchild in gchild:
                gg.process_GreatGrandChild(ggchild, parent_member=self)
                if gg.member is None:
                    logger.debug(
                        "Bailing out ggchild processing: %s", gg.member
                    )
                    del gg
                    return None
            if gg.member != member and gg.member["params"] not in [None, []]:
                gg.member["params"].extend(member["params"])
                member["params"] = gg.member["params"]
                logger.debug("member after adding gg_members: %s", member)
            logger.info(
                "Finished processing of function definition: '%s:%s'",
                gg.func_path,
                gg.func_name,
            )
            del gg

        return member
