"""
The main classes used by this module.
"""

import inspect
import re
import xml.etree.ElementTree as ET
from typing import Union

from .settings import VALUE_TYPES, Language, logger
from .support_functions import cleanString, guess_type_from_default, typeFix


class DummySig:
    """
    Dummy signature class for PyBind11 functions
    """

    def __init__(self, module):
        self.module = module
        self.name = module.__name__ if inspect.ismodule(module) else module
        self.docstring = inspect.getdoc(module)
        self.parameters, self.ret = self.get_pb11_sig()

    def get_pb11_sig(self):
        """
        Process the docstring from the PyBind11 functions
        """
        parameters = {}
        ret = None
        if self.docstring:
            try:
                # TODO: replace the parsing of the call_line with ast
                # NOTE: ast does not seem to deal with return types
                # NOTE: numpy.array has a '*' on the call_line, which is invalid!
                doc_split = re.split(r"\n *\n", self.docstring, 1)
                if len(doc_split) == 1:
                    call_line = doc_split[0]
                elif len(doc_split) > 1:
                    call_line, self.docstring = doc_split[:2]
                try:
                    params = re.findall(r"\(.*\n*.*\)", call_line)[0]
                    params = re.sub(r"\n {2,}", " ", params)
                    params = re.findall(
                        r"(?:([\w_\.]+)(?:[\: ]*([\w_\:\.\[\]]*)(?: *= *([\w\.\'\-]*))*\,*))",  # noqa: E501
                        params,
                    )
                    ret = re.findall(r"-> ([\w_\:\.\[\]]+)", call_line)
                except IndexError:
                    logger.debug("First line is likely not a call line: %s", call_line)
                    desc = DetailedDescription(self.docstring)
                    params = desc.params
            except:  # noqa: E722
                logger.debug(
                    ">>>> param matching failed: %s",
                    self.docstring,
                )
                return {}, None
            ret = ret[0] if ret else None
            if inspect.ismethoddescriptor(self.module):
                # make sure methoddescriptors have a self parameter
                parameters["self"] = DummyParam()
                if hasattr(self.module, "__objclass__"):
                    parameters["self"].annotation = f"{self.module.__objclass__}"
                elif hasattr(self.module, "__module__"):
                    parameters["self"].annotation = f"{self.module.__module__}"
            if isinstance(params, dict):
                for k, v in params.items():
                    parameters[k] = DummyParam()
                    t = v["type"]
                    if t and isinstance(t, str) and typeFix(t) in VALUE_TYPES.values():
                        t = [k for k, v in VALUE_TYPES.items() if v == typeFix(t)][0]
                    desc = v["desc"]
                    parameters[k].annotation = t
                    parameters[k].default = None
            elif isinstance(params, list):
                for k, t, v in params:
                    parameters[k] = DummyParam()
                    # replace with actual supported type rather than string
                    if t and isinstance(t, str) and typeFix(t) in VALUE_TYPES.values():
                        t = [k for k, v in VALUE_TYPES.items() if v == typeFix(t)][0]
                    elif not t and v:  # try to guess from default value
                        t = guess_type_from_default(v, raw=True)
                    parameters[k].annotation = t
                    parameters[k].default = v
        elif self.docstring and len(self.docstring) == 0:
            logger.warning("Module %s docstring is empty.", self.docstring)
        elif self.docstring and len(self.docstring) > 0:
            logger.info('Non-standard PB11 docstring found: "%s"', self.docstring)
        return parameters, ret


class DummyParam:  # no-eq: R0903
    """
    Dummy Parameter class
    """

    annotation = None
    kind = "POSITIONAL_OR_KEYWORD"
    default = inspect._empty


class DetailedDescription:
    """
    Class performs parsing of detailed description elements.
    This class is used for both compound (e.g. class) level descriptions
    as well as function/method level.
    """

    KNOWN_FORMATS = {
        "rEST": r"\n(:param|:returns|Returns:) .*",
        "Google": r"\nArgs:",
        "Numpy": r"\n *Parameters *:* *\n *----------",
        "casa": r"\n-{2,20}? parameter",
    }

    def __init__(self, descr: Union[str | None], name=None):
        """
        :param descr: Text of the detaileddescription node
        """
        self.name = name
        self.description = descr if descr else ""
        self.format = ""
        self._identify_format()
        self.main_descr, self.params = self.process_descr()
        self.brief_descr = self.main_descr.split(".")[0] + "." if self.main_descr else ""

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

        indent = re.findall(r"(\n *):param", detailed_description)
        if indent:
            ds = re.sub(
                re.findall(r"(\n *):param", detailed_description)[0],
                "\n",
                detailed_description,
            )
        else:
            ds = detailed_description
        ds = ds.lstrip()

        if ds.find("Returns:") >= 0:
            split_str = "Returns:"
        elif ds.find(":returns:") >= 0:
            split_str = ":returns:"
        elif ds.find(":return:") >= 0:  # take care of mis-spelling
            split_str = ":return:"
        else:
            split_str = ""
        ds = ds.split(split_str)[0] if split_str else ds
        param_lines = [p.replace("\n", "").strip() for p in ds.split(":param")[1:]]
        type_lines = [p.replace("\n", "").strip() for p in ds.split(":type")[1:]]
        # param_lines = [line.strip() for line in ds]

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
            t_ind = t_ind if t_ind > -1 else None  # type: ignore
            param_description = param_description[:t_ind]
            # logger.debug("%s description: %s", param_name,
            # param_description)

            if len(type_lines) != 0:
                result.update({param_name: {"desc": param_description, "type": None}})
            else:
                result.update(
                    {
                        param_name: {
                            "desc": param_description,
                            "type": typeFix(
                                re.split(r"[,\s\n]", param_description.strip())[0]
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
            param_type = t_line[index_of_second_colon + 2 :].strip()  # noqa: E203
            p_ind = param_type.find(":param")
            p_ind = p_ind if p_ind > -1 else None  # type: ignore
            param_type = param_type[:p_ind]
            param_type = typeFix(param_type)

            # if param exists, update type
            if param_name in result:
                result[param_name]["type"] = param_type
            else:
                logger.warning("Type spec without matching description %s", param_name)

        return ds.split(":param")[0].strip(), result

    def _process_Numpy(self, dd: str) -> tuple:
        """
        Process the Numpy-style docstring

        :param dd: str, the content of the detailed description tag

        :returns: tuple, description and parameter dictionary
        """
        logger.debug("Processing Numpy style doc_strings")
        if not dd:
            return ("", {})
        ds = dd.strip("\n")
        split = re.split(r"\n([\w ]+):*\n---*\n", ds.lstrip())
        split = ["Description"] + split
        dsplit = dict(zip(split[::2], split[1::2]))

        description = dsplit["Description"]
        parameters = dsplit["Parameters"] if "Parameters" in dsplit else ""
        returns = dsplit["Returns"] if "Returns" in dsplit else None

        # split param lines
        spds = re.split(r"([\w_]+) *: ", parameters)[1:]
        pdict = dict(zip(spds[::2], spds[1::2]))
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
        return description, pdict, returns

    def _process_Google(self, dd: str):
        """
        Process the Google-style docstring
        TODO: still some corner cases of OSKAR to be fixed:
        oskar.Telescope.set_noise_freq

        :param dd: str, the content of the detailed description tag

        :returns: tuple, description and parameter dictionary
        """
        logger.debug("Processing Google style doc_strings")
        indent = len(re.findall(r"[ ]", re.findall(r"\n[ ]*Args:", dd)[0]))
        dd = dd.replace(" " * indent, "")
        # remove indent from lines
        # extract main documentation (up to Parameters line)
        description = dd
        rest = ""
        sdd = dd.split("\nArgs:\n", 1)
        if len(sdd) > 1:
            (description, rest) = sdd
        elif len(sdd) == 1:
            description = sdd[0]

        # logger.debug("Splitting: %s %s", description, rest)
        # extract parameter documentation (up to Returns line)
        pds = rest.split("\nReturns:\n")[0]
        indent = len(re.findall(r"^ *", pds)[0])
        pds = re.sub(r"\n" + r" " * indent, "\n", "\n" + pds)  # remove indentation
        # split param lines
        spds = re.findall(r"\n([\w_.]+)\s*:[\n ]*([\w \-_\,\.']+)", pds)
        if not spds:
            logger.debug(">>> pds matching: spds no match 1")
            spds = re.findall(
                r"\n([\w_.]+)\s*\(([\w\-_ .\,]+)\]*\):[\n ]*([\w \-_\,\'.]+)",
                pds,
            )
        if not spds:
            logger.debug(">>> pds matching: spds no match 2")
            spds = re.findall(
                r"\n([\w_]+)\s\((?:Optional\[)*([\w_\.\-]*)[\, ]"
                + r"*([\w\-_ ]+)\]*\):[\n ]*([\w \-_\,\.\/\^']+)",
                pds,
            )
        try:
            pdict = {}
            for item in spds:
                if len(item) == 4:
                    pdict[item[0]] = {
                        "type": f"{item[1]},{item[2]}",
                        "desc": item[3],
                    }
                elif len(item) == 3:
                    pdict[item[0]] = {"type": item[1], "desc": item[2]}
                elif len(item) == 2 and len(pds.split("\n")[0].split(":")) == 2:
                    pdict[item[0]] = {"desc": item[1], "type": "Object"}
                elif len(item) == 2 and len(pds.split("\n")[0].split(":")) == 1:
                    pdict[item[0]] = {"type": item[1], "desc": ""}

        except IndexError:
            logger.debug(">>> spds matching failed %s %s:", pds, spds)
            raise
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
                idx for idx, s in enumerate(dList) if re.findall(r"-{1,20} parameter", s)
            ][0] + 1
        except IndexError:
            start_ind = 0
        try:
            end_ind = [
                idx for idx, s in enumerate(dList) if re.findall(r"-{1,20} example", s)
            ][0]
        except IndexError:
            end_ind = -1
        paramsList = dList[start_ind:end_ind]
        paramsSidx = [
            idx + 1 for idx, p in enumerate(paramsList) if len(p) > 0 and p[0] != " "
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
                    for p in paramsList[paramsSidx[i] : paramsEidx[i] - 1]  # noqa: E203
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
            logger.debug("Unknown param desc format!")

    def _gen_code_block(self):
        """
        Update indenation for pre-formatting the description
        """
        if self.description:
            self.description = self.description.replace("\n", "\n    ")

    def process_descr(self):
        """
        Helper function to provide plugin style parsers for various
        formats.
        """
        # self._gen_code_block()
        do = f"_process_{self.format}"
        if hasattr(self, do) and callable(func := getattr(self, do)):
            logger.debug("Calling %s parser function", do)
            pd = func(self.description)
            # self.description = pd[0].replace("\n\n", "\n")
            self.description = pd[0]
            self._gen_code_block()
            return self.description, pd[1]
        logger.debug("Format not recognized or can't execute %s", do)
        logger.debug("Returning description unparsed!")
        return (self._gen_code_block(), {})


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
            self.member = {"params": {}}

    def process_GreatGrandChild(
        self, ggchild: ET.Element, parent_member: Union["Child", None] = None
    ):
        """
        Process GreatGrandChild

        :param ggchild: dict, the great grandchild element
        :param parent_member: dict, member dict from parent class
        """

        # logger.debug("Initialized ggchild member: %s", self.member)
        logger.debug("New GreatGrandChild element: %s", ggchild.tag)  # type: ignore
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
            self.member["params"].update({"text": self.func_title})

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
                    desc,
                )
                self.member["params"]["description"] = desc

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
                    # Not sure whether we should do this:
                    # if value_type not in VALUE_TYPES.values():
                    #     value_type = f"Object.{value_type}"
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
            if parent_member and parent_member.casa_mode and name == "self":
                logger.debug("Skipping 'self' for casatasks")
            else:
                value = (
                    f"{default_value}/{value_type}/ApplicationArgument/{port}/"
                    + f"{access}//False/False/{member_desc}"
                )
                logger.debug("adding param: %s", {"key": str(name), "value": value})
                self.member["params"].update({name: value})

        elif ggchild.tag == "definition":  # type: ignore
            self.return_type = ggchild.text.strip().split(" ")[0]  # type: ignore
            func_path = ggchild.text.strip().split(" ")[-1]  # type: ignore
            # skip function if it begins with a single underscore,
            # but keep __init__ and __call__
            if func_path.find(".") >= 0:
                self.func_path, self.func_name = func_path.rsplit(".", 1)
            logger.info(
                "Found function [path:name]: '%s:%s'",
                self.func_path,
                self.func_name,
            )

            if self.func_name in ["__init__", "__call__"]:
                self.is_init = True
                if parent_member and not parent_member.casa_mode:
                    self.func_title = (
                        f"{self.func_path.rsplit('.',1)[-1]}.{self.func_name}"
                    )
                else:
                    self.func_title = self.func_path.rsplit("._", 1)[-1]
                    self.func_path = self.func_path.rsplit("._")[0]
                self.func_name = self.func_path
                logger.info(
                    "Using title %s for %s function",
                    self.func_title,
                    self.func_name,
                )
            elif self.func_name.startswith("_") or self.func_path.find("._") >= 0:
                logger.debug("Skipping %s.%s", self.func_path, self.func_name)
                self.member = None  # type: ignore
            else:
                self.func_title = f"{self.func_path.rsplit('.',1)[-1]}.{self.func_name}"
                self.func_name = f"{self.func_path}.{self.func_name}"
            if self.member:
                self.return_type = (
                    "None" if self.return_type == "def" else self.return_type
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
        if name in params:
            params[name] += description
            # if p["key"] == name:
            #     p["value"] = p["value"] + description
            #     # insert the type
            #     pp = p["value"].split("/", 2)
            #     p["value"] = "/".join(pp[:1] + [p_type] + pp[2:])
            #     p["type"] = p_type
            #     break


class Child:
    """
    Child class for hierarchy.
    """

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
        self.member: dict = {"params": {}}
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
        if child.tag == "detaileddescription" and len(child) > 0:  # type: ignore
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
                gmember = self._process_grandchild(grandchild, language, parent=parent)
                if gmember is None:
                    logger.debug("Bailing out of grandchild processing!")
                    continue
                if gmember != self.member:
                    # logger.debug("Adding grandchild members: %s", gmember)
                    self.member["params"].update(gmember["params"])
                    members.append(gmember)
            logger.debug("Finished processing grand children")
        self.members = members

    def _process_grandchild(
        self,
        gchild: ET.Element,
        language: Language,
        parent: Union["Child", None] = None,
    ) -> Union[dict, None]:
        """
        Private function to process a grandchild element
        Starts the construction of the member data structure

        :param gchild: dict, the parsed grandchild element from XML
        :param language: int, the languange indicator flag,
                        0 unknown, 1: Python, 2: C

        :returns: dict, the member data structure
        """
        member: dict = {"params": {}}
        # logger.debug("Initialized grandchild member: %s", member)

        if gchild.tag == "memberdef" and gchild.get("kind") == "function":  # type: ignore
            logger.debug("Start processing of new function definition.")

            member["params"].update(
                {
                    "input_parser": "pickle/Select/"
                    + "ComponentParameter/NoPort/readwrite/pickle,eval,"
                    + "npy,path,dataurl/False/False/Input port "
                    + "parsing technique",
                }
            )
            member["params"].update(
                {
                    "output_parser": "pickle/Select/"
                    + "ComponentParameter/NoPort/readwrite/pickle,eval,"
                    + "npy,path,dataurl/False/False/Output port parsing "
                    + "technique",
                }
            )

            member["params"].update(
                {
                    "execution_time": "5/Integer/ComponentParameter/NoPort/"
                    + "readwrite//False/False/Estimate of execution time "
                    + "(in seconds) for this application."
                }
            )
            member["params"].update(
                {
                    "num_cpus": "1/Integer/ComponentParameter/NoPort/"
                    + "readwrite//False/False/Number of cores used."
                }
            )
            member["params"].update(
                {
                    "group_start": "false/Boolean/ComponentParameter/NoPort/"
                    + "readwrite//False/False/Is this node the start of "
                    + "a group?"
                }
            )
            if language == Language.C:
                member["params"].update(
                    {
                        "category": "DynlibApp",
                    }
                )
                member["params"].update(
                    {
                        "libpath": " //String/ComponentParameter/NoPort/"
                        + "readwrite//False/False/The location of the shared "
                        + "object/DLL that implements this application",
                    }
                )
            elif language == Language.PYTHON:
                member["params"].update({"category": "PythonApp"})
                member["params"].update(
                    {
                        "dropclass": "dlg.apps.pyfunc.PyFuncApp/"
                        + "String/ComponentParameter/NoPort/readonly//False/"
                        + "False/"
                        + "The python class that implements this application",
                    }
                )

            logger.debug("Processing %d great grand children", len(gchild))
            if parent:
                self.member["params"].update(parent.member["params"])
                member["description"] = parent.description
            gg = GreatGrandChild()
            for ggchild in gchild:
                gg.process_GreatGrandChild(ggchild, parent_member=self)
                if gg.member is None:
                    logger.debug("Bailing out ggchild processing: %s", gg.member)
                    del gg
                    return None
            if gg.member != member and gg.member["params"] not in [None, {}]:
                gg.member["params"].update(member["params"])

                gg.member["params"].update(
                    {
                        "func_name": gg.func_name
                        + "/String/ComponentParameter/NoPort/readonly/"
                        + "/False/False/Complete import path of function",
                    }
                )

                member["params"] = gg.member["params"]
                logger.debug("member after adding gg_members: %s", member)
            logger.info(
                "Finished processing of function definition: '%s:%s'",
                gg.func_path,
                gg.func_name,
            )
            del gg

        return member
