# pylint: disable=invalid-name
# pylint: disable=bare-except
# pylint: disable=dangerous-default-value
# pylint: disable=too-many-branches
# pylint: disable=too-many-nested-blocks
# pylint: disable=eval-used
"""
dlg_paletteGen base functionality for the treatment of installed modules.
"""

import functools
import inspect
import re
import sys
import types
import typing
from typing import _SpecialForm

from .classes import DetailedDescription, DummyParam, DummySig, logger
from .support_functions import (
    constructNode,
    get_mod_name,
    get_submodules,
    import_using_name,
    populateDefaultFields,
    populateFields,
)


def get_class_members(cls, parent=None):
    """
    Inspect members of a class
    """
    try:
        content = inspect.getmembers(
            cls,
            lambda x: inspect.isfunction(x)
            or inspect.ismethod(x)
            or inspect.isbuiltin(x)
            or inspect.ismethoddescriptor(x),
        )
    except KeyError:
        logger.debug("Problem getting members of %s", cls)
        return {}

    content = [(n, m, False) for n, m in content]
    # deal with possibility that callables could be defined as annotations!!
    # Very bad style, but used in astropy.coordinates.SkyCoord
    if isinstance(cls, type):
        if sys.version_info.major == 3 and sys.version_info.minor > 9:
            ann = inspect.get_annotations(
                cls,
                globals=globals(),
                locals=sys.modules[cls.__module__].__dict__,
                eval_str=True,
            )
        else:
            ann = cls.__dict__.get("__annotations__", None)
    else:
        ann = getattr(cls, "__annotations__", None)

    if ann:
        # Add Callable annotations to the module content
        for aname, annotation in ann.items():
            if isinstance(annotation, typing._CallableGenericAlias):
                if isinstance(annotation.__args__[0], types.UnionType):
                    for union_member in typing.get_args(annotation.__args__[0]):
                        if hasattr(union_member, aname):
                            content.append((aname, getattr(union_member, aname), True))
                else:
                    content.append((aname, f"{cls.__name__}.{aname}", True))
    content = [
        (n, m, ann_fl)
        for n, m, ann_fl in content
        if re.match(r"^[a-zA-Z]", n) or n in ["__init__", "__cls__"]
    ]
    logger.debug("Member functions of class %s: %s", cls, [n for (n, _, _) in content])
    class_members = {}
    for n, m, ann_fl in content:
        if isinstance(m, functools.cached_property):
            logger.error("Found cached_property object!")
            continue
        mod_name = m.__qualname__ if not isinstance(m, str) else m
        if (
            not n.startswith("_")
            or mod_name.startswith(cls.__name__)
            or ann_fl
            or mod_name.startswith("PyCapsule")
            or mod_name == "object.__init__"
        ):
            node = construct_member_node(m, module=cls, parent=parent, name=n)
            if not node:
                logger.debug("Inspection of '%s' failed.", mod_name)
                continue
            class_members.update({node["name"]: node})
        else:
            logger.debug(
                "class name %s not start of qualified name: %s",
                cls.__name__,
                mod_name,
            )
    return class_members


def _get_name(name: str, member, module=None, parent=None) -> str:
    """
    Get a name and a qualified name for various cases.
    """
    member_name = get_mod_name(member)
    module_name = get_mod_name(module)
    if inspect.isclass(module):
        mname = f"{module_name}.{member_name}"
        # mname = qname = mname if isinstance(member, str) else member.__qualname__
        if mname.startswith("PyCapsule"):
            mname = mname.replace("PyCapsule", f"{module.__module__}.{module.__name__}")
        elif mname == "object.__init__":
            mname = f"{module.__name__}.__init__"
    elif inspect.isclass(member):
        mname = getattr(member, "__class__").__name__
    else:
        mname = f"{member_name}" if hasattr(member, "__name__") else f"{module_name}.name"
    logger.debug(">>>>> mname: %s, %s.%s", mname, parent, module_name)
    if name and not mname:
        mname = name
    return mname


def _get_docs(member, module, node) -> tuple:
    """
    Helper function to extract the main documentation and the parameter docs if available.
    """

    dd = None
    doc = inspect.getdoc(member)
    if (
        doc
        and len(doc) > 0
        and not doc.startswith(
            "Initialize self.  See help(type(self)) for accurate signature."
        )
    ):
        logger.debug(
            "Process documentation of %s %s", type(member).__name__, node["name"]
        )
        dd = DetailedDescription(doc, name=node["name"])
        node["description"] = f"{dd.description.strip()}"
        if len(dd.params) > 0:
            logger.debug("Identified parameters: %s", dd.params)
    if (
        node["name"].split(".")[-1] in ["__init__", "__cls__"]
        and inspect.isclass(module)
        and inspect.getdoc(module)
    ):
        logger.debug(
            "Using description of class '%s' for %s",
            module.__name__,
            node["name"],
        )
        node["category"] = "PythonMemberFunction"
        dd = DetailedDescription(inspect.getdoc(module), name=module.__name__)
        node["description"] += f"\n{dd.description.strip()}"
    if not dd:
        logger.debug("Entity '%s' has neither descr. nor __name__", node["name"])

    if type(member).__name__ in [
        "pybind11_type",
        "builtin_function_or_method",
    ]:
        logger.debug("!!! %s PyBind11 or builtin: Creating dummy signature !!!", member)
        try:
            # this will fail for e.g. pybind11 modules
            sig = inspect.signature(member)  # type: ignore
            return (sig, dd)
        except (ValueError, TypeError):
            logger.debug("Unable to get signature of %s: ", node["name"])
            dsig = DummySig(member)  # type: ignore
            node["description"] = dsig.docstring
            return (dsig, dd)
    else:
        try:
            # this will fail for some weird modules
            return (inspect.signature(member), dd)  # type: ignore
        except (ValueError, TypeError):
            logger.debug(
                "Unable to get signature of %s: %s",
                node["name"],
                type(member).__name__,
            )
            dsig = DummySig(member)  # type: ignore
            if dsig.docstring:
                node["description"] = dsig.docstring
            if not getattr(dsig, "parameters") and dd and len(dd.params) > 0:
                for p in dd.params.kyes():
                    dsig.parameters[p] = DummyParam()
            return (dsig, dd)


def construct_func_name(member_name: str, module_name: str) -> str:
    """
    Construct the function name of a member of a module or a class.

    Parameters:
    -----------
    member_name: str, the name of the member of the module or the class
    module_name: str, the name of the module or the class
    parent_name: str, the name of the parent

    Returns:
    --------
    str, the function_name of the member
    """
    if member_name and module_name:
        func_name = f"{member_name}.{module_name}"
    else:
        func_name = "test"
    return func_name


def construct_member_node(member, module=None, parent=None, name=None) -> dict:
    """
    Inspect a member function or method and construct a node for the palette.
    """
    node = constructNode()
    node["name"] = _get_name(name, member, module, parent)
    logger.debug(
        "Inspecting %s: %s, %s, %s, %s",
        type(member).__name__,
        node["name"],
        name,
        module,
        parent,
    )

    sig, dd = _get_docs(member, module, node)
    # fill custom ApplicationArguments first
    fields = populateFields(sig.parameters, dd)
    ind = -1
    load_name = node["name"]
    if hasattr(member, "__module__") and member.__module__:
        load_name = f"{member.__module__}.{node['name']}"
    elif hasattr(member, "__package__"):
        load_name = f"{member.__package__}.{load_name}"
    elif parent:
        load_name = f"{parent}.{load_name}"
    if load_name.find("PyCapsule"):
        load_name = load_name.replace("PyCapsule", get_mod_name(module))
    if load_name.find("object.__init__"):
        load_name = load_name.replace("object.__init__", node["name"])
    # fields["base_name"]["value"] = member.__qualname__.split(".", 1)[0]
    fields["base_name"]["value"] = ".".join(load_name.split(".")[:-1])
    fields["base_name"]["defaultValue"] = fields["base_name"]["value"]

    for k, field in fields.items():
        ind += 1
        if k == "self" and ind == 0:
            node["category"] = "PythonMemberFunction"
            if member.__name__ in ["__init__", "__cls__"]:
                fields["self"]["usage"] = "OutputPort"
            elif inspect.ismethoddescriptor(member):
                fields["self"]["usage"] = "InputOutput"
            else:
                fields["self"]["usage"] = "InputPort"
            fields["self"]["type"] = "Object:" + ".".join(load_name.split(".")[:-1])
            if fields["self"]["type"] == "numpy.ndarray":
                # just to make sure the type hints match the object type
                fields["self"]["type"] = "numpy.array"

        node["fields"].update({k: field})

    # now populate with default fields.
    node = populateDefaultFields(node)
    node["fields"]["func_name"]["defaultValue"] = load_name
    node["fields"]["func_name"]["value"] = node["fields"]["func_name"]["defaultValue"]
    if hasattr(sig, "ret"):
        logger.debug("Return type: %s", sig.ret)
    logger.debug("Constructed node for member %s: %s", node["name"], node)
    return node


def get_members(mod: types.ModuleType, module_members=[], parent=None):
    """
    Get members of a module

    :param mod: the imported module
    :param parent: the parent module
    :param member: filter the content of mod for this member
    """
    if not mod:
        return {}
    module_name = parent if parent else get_mod_name(mod)
    module_name = str(module_name)
    logger.debug(">>>>>>>>> Analysing members for module: %s", module_name)
    try:
        content = inspect.getmembers(mod)
    except:  # noqa: E722
        content = []
    logger.debug("Found %d members in %s", len(content), mod)
    members = {}
    i = 0
    for name, _ in content:
        if name in module_members:
            logger.debug("Skipping already existing member: %s", name)
            continue
        logger.debug("Analysing member: %s", name)
        # if not member or (member and name == member):
        if name[0] == "_" and name not in ["__init__", "__call__"]:
            # NOTE: PyBind11 classes can have multiple constructors
            continue
        m = getattr(mod, name)
        if not callable(m) or isinstance(m, _SpecialForm):
            # logger.warning("Member %s is not callable", m)
            # not sure what to do with these. Usually they
            # are class parameters.
            continue
        if inspect.isclass(m):
            if m.__module__.find(module_name) < 0:
                continue
            logger.debug("Processing class '%s'", name)
            nodes = get_class_members(m, parent=parent)
            logger.debug("Class members: %s", nodes.keys())
        else:
            nodes = {name: construct_member_node(m, module=mod, parent=parent, name=name)}

        for name, node in nodes.items():
            if name in module_members:
                logger.debug("!!!!! found duplicate: %s", name)
            else:
                module_members.append(name)
                members.update({name: node})

                if hasattr(m, "__members__"):
                    # this takes care of enum types, but needs some
                    # serious thinking for DALiuGE. Note that enums
                    # from PyBind11 have a generic type, but still
                    # the __members__ dict.
                    logger.info("\nMembers:")
                    logger.info(m.__members__)
                    # pass
        # elif member:  # we've found what we wanted
        #     # break
        i += 1
    logger.debug("Extracted %d members in module %s", len(members), module_name)
    return members


def module_hook(mod_name: str, modules: dict = {}, recursive: bool = True) -> tuple:
    """
    Function dissecting an imported module.

    :param mod_name: str, the name of the module to be treated
    :param modules: dictionary of modules
    :param recursive: bool, treat sub-modules [True]

    :returns: dict of modules processed
    """
    member = mod = None
    module_members = []
    for m in modules.values():
        module_members.extend([k.split(".")[-1] for k in m.keys()])
    try:
        logger.debug("Trying to use eval to load module %s", mod_name)
        mod = eval(mod_name)
        members = get_members(mod, module_members=module_members)
        modules.update({mod_name: members})
        logger.info("Found %d members in %s", len(members), mod_name)
    except NameError:
        try:
            logger.debug("Trying alternative load of %s", mod_name)
            # Need to check this again:
            # traverse = True if len(modules) == 0 else False
            mod = import_using_name(mod_name, traverse=True)
            m_name = get_mod_name(mod)
            if mod and mod_name != m_name:
                member = mod_name.split(".")[-1]
                mod_name = m_name
            members = get_members(
                mod,
                parent=mod_name,
                module_members=module_members,
            )
            module_members.extend([k.split(".") for k in members.keys()])
            modules.update({mod_name: members})
            sub_modules = []
            if not member and recursive and mod and mod not in sub_modules:
                sub_modules, _ = get_submodules(mod)
                logger.debug("Iterating over sub_modules of %s", mod_name)
                for sub_mod in sub_modules:
                    logger.debug("Treating sub-module: %s of %s", sub_mod, mod_name)
                    modules, _ = module_hook(sub_mod, modules=modules)
        except ImportError:
            logger.error("Module %s can't be loaded!", mod_name)
            return ({}, None)
    return modules, mod.__doc__
