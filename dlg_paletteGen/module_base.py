"""
dlg_paletteGen base functionality for the treatment of installed modules.
"""
import inspect
import re
import sys
import types
from typing import _SpecialForm

from .classes import DetailedDescription, DummyParam, DummySig, logger
from .support_functions import (
    constructNode,
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
        logger.error("Problem getting members of %s", cls)
        return {}
    content = [
        (n, m)
        for n, m in content
        if re.match(r"^[a-zA-Z]", n) or n in ["__init__", "__cls__"]
    ]
    logger.debug("Member functions of class %s: %s", cls, content)
    class_members = {}
    for _, m in content:
        if m.__qualname__.startswith(
            cls.__name__
        ) or m.__qualname__.startswith("PyCapsule"):
            node = inspect_member(m, module=cls, parent=parent)
            if not node:
                logger.debug("Inspection of '%s' failed.", m.__qualname__)
                continue
            class_members.update({node.name: node})
        else:
            logger.debug(
                "class name %s not start of qualified name: %s",
                cls.__name__,
                m.__qualname__,
            )
    return class_members


def inspect_member(member, module=None, parent=None):
    """
    Inspect a member function or method.
    """
    node = constructNode()
    if inspect.isclass(module):
        name = member.__qualname__
        if name.startswith("PyCapsule"):
            name = name.replace(
                "PyCapsule", f"{module.__module__}.{module.__name__}"
            )
    else:
        name = (
            f"{parent}.{member.__name__}"
            if hasattr(member, "__name__")
            else f"{module.__name__}.Unknown"
        )
    # shorten node name, else EAGLE components are cluttered.
    # name = (
    #     f"{name.split('.')[0]}.{'.'.join(name.split('.')[-2:])}"
    #     if name.count(".") > 2
    #     else name
    # )
    node.name = name
    logger.debug("Inspecting %s: %s", type(member).__name__, member.__name__)

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
            f"Process documentation of {type(member).__name__} {name}"
        )
        dd = DetailedDescription(doc)
        node.description = f"{dd.description.strip()}"
        if len(dd.params) > 0:
            logger.debug("Identified parameters: %s", dd.params)
    if (
        member.__name__ in ["__init__", "__cls__"]
        and inspect.isclass(module)
        and inspect.getdoc(module)
    ):
        logger.debug(
            "Using description of class '%s' for %s",
            module.__name__,
            member.__name__,
        )
        dd = DetailedDescription(inspect.getdoc(module))
        node.description += f"\n{dd.description.strip()}"
    elif hasattr(member, "__name__"):
        logger.debug("Member '%s' has no description!", name)
    else:
        logger.debug("Entity '%s' has neither descr. nor __name__", name)

    if type(member).__name__ in [
        "pybind11_type",
        "builtin_function_or_method",
    ]:
        logger.debug("!!! PyBind11 or builtin: Creating dummy signature !!!")
        try:
            # this will fail for e.g. pybind11 modules
            sig = inspect.signature(member)  # type: ignore
        except ValueError:
            logger.debug("Unable to get signature of %s: ", name)
            sig = DummySig(member)
            node.description = sig.docstring
    else:
        try:
            # this will fail for e.g. pybind11 modules
            sig = inspect.signature(member)  # type: ignore
        except ValueError:
            logger.warning("Unable to get signature of %s: ", name)
            sig = DummySig(member)
            if sig.docstring:
                node.description = sig.docstring
            if not getattr(sig, "parameters") and dd and len(dd.params) > 0:
                for p, v in dd.params.items():
                    sig.parameters[p] = DummyParam()
    # fill custom ApplicationArguments first
    fields = populateFields(sig.parameters, dd)
    ind = -1
    for k, field in fields.items():
        ind += 1
        if k == "self" and ind == 0:
            if member.__name__ in ["__init__", "__cls__"]:
                fields["self"].usage = "OutputPort"
            else:
                fields["self"].usage = "InputPort"
            fields["self"].type = f"Object.{node.name.split('.')[0]}"

        node.fields.update({k: field})

        # now populate with default fields.
    node = populateDefaultFields(node)
    load_name = member.__qualname__
    if hasattr(member, "__module__") and member.__module__:
        load_name = f"{member.__module__}.{load_name}"
    elif hasattr(member, "__package__"):
        load_name = f"{member.__package__}.{load_name}"
    elif parent:
        load_name = f"{parent}.{load_name}"
    if load_name.find("PyCapsule"):
        load_name = load_name.replace("PyCapsule", module.__name__)
    node.fields["func_name"]["value"] = load_name
    node.fields["func_name"]["defaultValue"] = load_name
    if hasattr(sig, "ret"):
        logger.debug("Return type: %s", sig.ret)
    return node


def get_members(
    mod: types.ModuleType, module_members=[], parent=None, member=None
):
    """
    Get members of a module

    :param mod: the imported module
    :param parent: the parent module
    :param member: filter the content of mod for this member
    """
    if not mod:
        return {}
    module_name = parent if parent else mod.__name__
    logger.debug(f">>>>>>>>> Analysing members for module: {module_name}")
    content = inspect.getmembers(
        mod,
        lambda x: inspect.isfunction(x)
        or inspect.ismethod(x)
        or inspect.isclass(x)
        or inspect.isbuiltin(x),
    )
    count = 0
    # logger.debug("Members of %s: %s", name, [c for c, m in content])
    members = {}
    for c, m in content:
        if not member or (member and c == member):
            if c[0] == "_" and c not in ["__init__", "__call__"]:
                # TODO: Deal with __init__
                # NOTE: PyBind11 classes can have multiple constructors
                continue
            m = getattr(mod, c)
            if not callable(m) or isinstance(m, _SpecialForm):
                # logger.warning("Member %s is not callable", m)
                # # TODO: not sure what to do with these. Usually they
                # # are class parameters.
                continue
            if inspect.isclass(m):
                if m.__module__.find(module_name) < 0:
                    continue
                logger.debug("Processing class '%s'", c)
                nodes = get_class_members(m, parent=parent)
                logger.debug("Class members: %s", nodes.keys())

            else:
                nodes = {
                    m.__name__: inspect_member(m, module=mod, parent=parent)
                }

            for name, node in nodes.items():
                if name in module_members:
                    logger.debug("!!!!! found duplicate: %s", name)
                else:
                    module_members.append(name)
                    logger.debug(
                        ">>> member update with: %s",
                        name,
                    )
                    members.update({name: node})

                    if hasattr(m, "__members__"):
                        # this takes care of enum types, but needs some
                        # serious thinking for DALiuGE. Note that enums
                        # from PyBind11 have a generic type, but still
                        # the __members__ dict.
                        logger.info("\nMembers:")
                        logger.info(m.__members__)
                        # pass
            if member:  # we've found what we wanted
                break
    logger.debug("Analysed %d members in module %s", count, module_name)
    return members


def module_hook(
    mod_name: str, modules: dict = {}, recursive: bool = True
) -> tuple:
    """
    Function dissecting an imported module.

    :param mod_name: str, the name of the module to be treated
    :param modules: dictionary of modules
    :param recursive: bool, treat sub-modules [True]

    :returns: dict of modules processed
    """
    member = None
    module_members = []
    for m in modules.values():
        module_members.extend([k.split(".")[-1] for k in m.keys()])
    # member_names = [n.split(".")[-1] for n in module_members.keys()]
    if mod_name not in sys.builtin_module_names:
        try:
            traverse = True if len(modules) == 0 else False
            mod = import_using_name(mod_name, traverse=traverse)
            if mod and mod_name != mod.__name__:
                member = mod_name.split(".")[-1]
                mod_name = mod.__name__
            members = get_members(
                mod,
                parent=mod_name,
                module_members=module_members,
                member=member,
            )
            module_members.extend([k.split(".") for k in members.keys()])
            modules.update({mod_name: members})
            # mod_count += 1
            sub_modules = []
            if not member and recursive and mod and mod not in sub_modules:
                sub_modules = get_submodules(mod)
                # if len(sub_modules) > 0:
                logger.debug("Iterating over sub_modules of %s", mod_name)
                for sub_mod in sub_modules:
                    logger.info(
                        "Treating sub-module: %s of %s", sub_mod, mod_name
                    )
                    modules, _ = module_hook(sub_mod, modules=modules)
            # member_count = sum([len(m) for m in modules.values()])
        except ImportError:
            logger.error("Module %s can't be loaded!", mod_name)
            return ({}, None)
    return modules, mod.__doc__
