# pylint: disable=invalid-name
# pylint: disable=bare-except
# pylint: disable=dangerous-default-value
# pylint: disable=too-many-branches
# pylint: disable=too-many-nested-blocks
# pylint: disable=eval-used
"""Provide base functionality for the treatment of installed modules."""

import functools
import inspect
import re
import sys
import types
import typing
from typing import Any, Tuple, _SpecialForm

from dlg_paletteGen.classes import DetailedDescription, DummyParam, DummySig
from dlg_paletteGen.source_base import FieldUsage
from dlg_paletteGen.support_functions import (
    constructNode,
    get_mod_name,
    get_submodules,
    import_using_name,
    populateDefaultFields,
    populateFields,
    prepare_and_write_palette,
)

from . import logger


def get_class_members(cls, parent=None):
    """Inspect members of a class."""
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
            try:
                ann = inspect.get_annotations(
                    cls,
                    globals=globals(),
                    locals=sys.modules[cls.__module__].__dict__,
                    eval_str=True,
                )
            except NameError:
                ann = cls.__dict__.get("__annotations__", None)
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
        logger.debug(">>> module type: %s", type(m))
        if not hasattr(m, "__qualname__"):
            continue
        mod_name = m.__qualname__ if not isinstance(m, str) else m
        if (
            not n.startswith("_")
            or mod_name.startswith(cls.__name__)
            or ann_fl
            or mod_name.startswith("PyCapsule")
            or mod_name == "object.__init__"
        ):
            node = construct_member_node(m, obj=cls, parent=parent, name=n)
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
    """Get a name and a qualified name for various cases."""
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
        mname = f"{member_name}" if hasattr(member, "__name__") else ""
    if name and not mname or name.rsplit(".", 1)[-1] == mname:
        mname = name
    logger.debug(">>>>> mname: %s, %s, %s", mname, parent, module_name)
    return mname


def _get_docs(member, module, node) -> tuple:
    """Extract the main documentation and the parameter docs if available."""
    dd = dd_mod = None
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
        dd_mod = DetailedDescription(inspect.getdoc(module), name=module.__name__)
        node["description"] += f"\n{dd_mod.description.strip()}"
    if not dd and dd_mod:
        dd = dd_mod
    elif not dd and not dd_mod:
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


def construct_func_name(load_name: str, module_name: str) -> str:
    """
    Construct the function name of a member of a module or a class.

    Parameters:
    -----------
    load_name: str, the string used to import the module, class or function
    module_name: str, the name of the module or the class
    parent_name: str, the name of the parent

    Returns:
    --------
    str, the function_name of the member
    """
    if load_name and module_name and load_name.startswith(module_name):
        return load_name
    if load_name and module_name and not load_name.startswith(module_name):
        func_name = f"{module_name}.{load_name}"
    else:
        func_name = "test"
    return func_name


def construct_member_node(member, obj=None, parent=None, name=None) -> dict:
    """Inspect a member function or method and construct a node for the palette."""
    node = constructNode()
    if parent and name and parent != name and parent != name.rsplit(".", 1)[0]:
        name = f"{parent}.{name}"
    node["name"] = _get_name(name, member, obj, parent)
    logger.debug(
        "Inspecting %s: %s, %s, %s, %s",
        type(member).__name__,
        node["name"],
        name,
        obj,
        parent,
    )

    sig, dd = _get_docs(member, obj, node)
    # fill custom ApplicationArguments first
    fields = populateFields(sig, dd)
    ind = -1
    load_name = node["name"]

    if not parent and not hasattr(parent, load_name):
        try:
            import_using_name(load_name, traverse=True)
        except (ModuleNotFoundError, AttributeError, ValueError):
            logger.critical("Cannot load %s, this method will likely fail", load_name)

    for k, field in fields.items():
        ind += 1
        if k == "self" and ind == 0:
            node["category"] = "PythonMemberFunction"
            fields["self"]["parameterType"] = "ComponentParameter"
            if member.__name__ in ["__init__", "__cls__"]:
                fields["self"]["usage"] = FieldUsage.OutputPort
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
    node["fields"]["func_name"]["defaultValue"] = construct_func_name(load_name, parent)
    node["fields"]["func_name"]["value"] = node["fields"]["func_name"]["defaultValue"]
    node["fields"]["base_name"]["value"] = ".".join(load_name.split(".")[:-1])
    node["fields"]["base_name"]["defaultValue"] = node["fields"]["base_name"]["value"]
    if hasattr(sig, "ret"):
        logger.debug("Return type: %s", sig.ret)
    logger.debug("Constructed node for member %s: %s", node["name"], node)
    return node


def get_members(obj: types.ModuleType, modules={}, parent=None):
    """
    Get members of an object.

    :param obj: the imported module
    :param parent: the parent module
    :param member: filter the content of mod for this member
    """
    if obj is None:
        return {}
    module_name = get_mod_name(obj)
    logger.debug(">>>>>>>>> Analysing members for module: %s", module_name)
    if inspect.isfunction(obj):
        content = [[get_mod_name(obj), obj]]
    else:
        try:
            content = inspect.getmembers(obj)
            # we only want to deal with the ones that are 'officially' exposed
            all_keys = [ak for k, ak in content if k == "__all__"]
            if all_keys:
                content = [c for c in content if c[0] in all_keys[0]]
            content = [
                c
                for c in content
                if not inspect.ismodule(c[1])
                and c[0] not in ["__init__", "__class__"]
                and not c[0].startswith("_")
            ]
        except:  # noqa: E722
            content = []
    logger.debug(
        "Found %d members in %s: %s", len(content), module_name, [n for n, _ in content]
    )
    members = {}
    i = 0
    member = obj
    for name, _ in content:
        if name in modules.keys():
            logger.debug(
                "Skipping already existing member: %s of module: %s", name, module_name
            )
            logger.debug("Module members: %s", modules.keys())
            continue
        logger.debug("Analysing member: %s", name)
        # if not member or (member and name == member):
        if name[0] == "_" and name not in ["__init__", "__call__"]:
            # NOTE: PyBind11 classes can have multiple constructors
            continue
        if not inspect.isfunction(obj):
            member = getattr(obj, name)
        if not callable(member) or isinstance(member, _SpecialForm):
            # logger.warning("Member %s is not callable", member)
            # not sure what to do with these. Usually they
            # are class parameters.
            continue
        if inspect.isclass(member):
            if member.__module__.find(module_name) < 0:
                continue
            logger.debug("Processing class '%s'", name)
            nodes = get_class_members(member, parent=parent)
            logger.debug("Class members: %s", nodes.keys())
        else:
            nodes = {
                name: construct_member_node(
                    member, obj=member, parent=module_name, name=name
                )
            }

        for name, node in nodes.items():
            if name in modules.keys():
                logger.debug("!!!!! found duplicate: %s", name)
            else:
                members.update({name: node})

                if hasattr(member, "__members__"):
                    # this takes care of enum types, but needs some
                    # serious thinking for DALiuGE. Note that enums
                    # from PyBind11 have a generic type, but still
                    # the __members__ dict.
                    logger.info("\nMembers:")
                    logger.info(member.__members__)
                    # pass
        # elif member:  # we've found what we wanted
        #     # break
        i += 1
    logger.debug("Extracted %d members in module %s", len(members), module_name)
    return members


def module_hook(import_name: str, modules: dict = {}, recursive: bool = True) -> tuple:
    """
    Import an object and analyse it recursively, if requested.

    The import_name can point to any object that can be imported.

    :param import_name: str, the name of the object to be analysed
    :param modules: dictionary of modules
    :param recursive: bool, treat sub-modules [True]

    :returns: dict of modules processed
    """
    obj_name = obj = None
    try:
        logger.debug("Trying to use eval to load object %s", import_name)
        obj = eval(import_name)
        members = get_members(obj, modules=modules)
        modules.update({import_name: members})
        logger.info("Found %d members in %s", len(members), import_name)
    except NameError:
        try:
            logger.debug("Trying alternative load of %s", import_name)
            # Need to check this again:
            # traverse = True if len(modules) == 0 else False
            obj = import_using_name(import_name, traverse=True)
            obj_name = get_mod_name(obj)
            if inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isbuiltin(obj):
                # the specified item is a function or method
                obj_name = obj_name.rsplit(".", 1)[0]
                members = {obj_name: obj}
            members = get_members(
                obj,
                parent=import_name.rsplit(".", 1)[0],
                modules=modules,
            )
            modules.update({obj_name: members})
            logger.debug("Found %d members in %s", len(members), obj_name)
            sub_modules, _ = get_submodules(obj)
            if sub_modules:
                logger.info("Found %d sub-modules in %s", len(sub_modules), obj_name)
            if sub_modules and recursive and obj and obj_name not in sub_modules:
                logger.debug("Iterating over sub_modules of %s", obj_name)
                for sub_mod in sub_modules:
                    logger.info("Treating sub-module: %s of %s", sub_mod, obj_name)
                    submod_dict, _ = module_hook(
                        sub_mod, modules=modules, recursive=recursive
                    )
                    mods_len = len(modules)
                    modules.update(submod_dict)
                    logger.debug(
                        "Added %d additional objects from sub-module %s, %d",
                        len(modules) - mods_len,
                        sub_mod,
                        len(modules),
                    )
        except (ImportError, NameError):
            logger.error("Module %s can't be loaded!", obj_name)
            return ({}, None)
    return modules, obj.__doc__


def nodes_from_module(module_path, recursive=True) -> Tuple[list, Any]:
    """
    Extract nodes from specified module.

    :param modules: modules dict as extracted by module_hook
    :param recursive: flag indicating wether to recurse down the hierarchy

    :returns: list of nodes (for now)
    """
    modules, module_doc = module_hook(module_path, recursive=recursive)
    logger.debug(
        ">>>>> Number of modules/members processed for %s: %d", module_path, len(modules)
    )
    logger.debug(
        "Modules/members found: %s",
        # modules
        {m: list(v.keys()) for m, v in modules.items() if v},
    )
    nodes = []
    for members in modules.values():
        for member, node in members.items():
            # TODO: remove once EAGLE can deal with dict fields pylint: disable=fixme
            if node is None or not node:
                continue
            try:
                if isinstance(node["fields"], list):
                    continue
                node["name"] = ".".join(node["name"].rsplit(".", 2)[-2:])
                node["fields"] = list(node["fields"].values())
                nodes.append(node)
            except TypeError:
                # logger.critical("Node has wrong type: %s", node)
                continue
            except KeyError:
                # logger.critical("Key 'fields' does not exist: %s: %s", member, node)
                continue
    return nodes, module_doc


def palettes_from_module(
    module_path: str,
    outfile: str = "",
    split: bool = False,
    recursive: bool = True,
) -> None:
    """
    Generate one or more palette files from the module specified.

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
        mod = import_using_name(module_path)
        sub_modules = [module_path] + list(get_submodules(mod)[0])
        # sub_modules, _ = [module_path, module_hook(module_path)]
        logger.info(
            "Splitting module %s into sub-module palettes: %s",
            module_path,
            sub_modules,
        )
    tot_nodes = 0
    for i, sub_mod in enumerate(sub_modules):
        logger.info("Extracting nodes from sub-module: %s, %d", sub_mod, i)
        if split:
            recursive = i != 0
        nodes, module_doc = nodes_from_module(sub_mod, recursive=recursive)
        if len(nodes) == 0:
            continue
        filename = (
            f"{outfile}{sub_mod.replace('.','_')}.palette" if not outfile else outfile
        )
        files[filename] = len(nodes)
        _ = prepare_and_write_palette(nodes, filename, module_doc=module_doc)
        tot_nodes += len(nodes)
        logger.info(
            "%s palette file written with %s components",
            filename,
            len(nodes),
        )
    logger.info(
        "\n\n>>>>>>> Extraction summary <<<<<<<<\n%s\n",
        "\n".join([f"Wrote {k} with {v} components" for k, v in files.items()]),
    )
    logger.info(
        "Total of %d components extracted from %d sub-modules",
        tot_nodes,
        len(sub_modules),
    )
