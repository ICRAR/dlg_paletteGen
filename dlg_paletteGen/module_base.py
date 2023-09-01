"""
dlg_paletteGen base functionality for the treatment of installed modules.
"""
import inspect
import sys
import types
from typing import _SpecialForm

from .classes import DetailedDescription, DummySig, logger
from .support_functions import (
    constructNode,
    get_submodules,
    import_using_name,
    populateDefaultFields,
    populateFields,
)


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
    name = parent if parent else mod.__name__
    logger.debug(f">>>>>>>>> Analysing members for module: {name}")
    content = inspect.getmembers(
        mod,
        lambda x: inspect.isfunction(x)
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
            else:
                node = constructNode()
                count += 1
                name = (
                    f"{parent}.{m.__name__}"
                    if hasattr(m, "__name__")
                    else f"{mod.__name__}.Unknown"
                )
                logger.info("Inspecting %s: %s", type(m).__name__, m.__name__)

                dd = None
                if m.__doc__ and len(m.__doc__) > 0:
                    logger.info(
                        f"Process documentation of {type(m).__name__} {name}"
                    )
                    dd = DetailedDescription(m.__doc__)
                    logger.debug(f"Full description: {dd.description}")
                    node.description = f"{dd.description.strip()}"
                    node.text = m.__name__
                    if len(dd.params) > 0:
                        logger.debug("Desc. parameters: %s", dd.params)
                elif hasattr(m, "__name__"):
                    logger.warning("Member '%s' has no description!", name)
                else:
                    logger.warning(
                        "Entity '%s' has neither descr. nor __name__", m
                    )

                if type(m).__name__ in [
                    "pybind11_type",
                    # "builtin_function_or_method",
                ]:
                    logger.info(
                        "!!! PyBind11 or builtin: Creting dummy signature !!!"
                    )
                    sig = DummySig(m)
                else:
                    try:
                        # this will fail for e.g. pybind11 modules
                        sig = inspect.signature(m)  # type: ignore
                    except ValueError:
                        logger.warning(
                            "Unable to get signature of %s: ", m.__name__
                        )
                        continue
                # fill custom ApplicationArguments first
            fields = populateFields(sig.parameters, dd)
            for k, field in fields.items():
                node.fields.update({k: field})

            # now populate with default fields.
            node = populateDefaultFields(node)
            node.fields["func_name"]["value"] = name
            node.fields["func_name"]["defaultValue"] = name
            if hasattr(sig, "ret"):
                logger.debug("Return type: %s", sig.ret)
            logger.debug(
                ">>> member update with: %s", {name: node.dump_json_str()}
            )
            if m.__name__ in module_members:
                logger.debug("!!!!! found existing member: %s", m.__name__)
            else:
                module_members.append(m.__name__)
                members.update({name: node})

                if hasattr(m, "__members__"):
                    # this takes care of enum types, but needs some
                    # serious thinking for DALiuGE. Note that enums
                    # from PyBind11 have a generic type, but still
                    # the __members__ dict.
                    logger.info("\nMembers:")
                    logger.info(m.__members__)
                    # pass
            if member:
                break
    logger.info("Analysed %d members in module %s", count, name)
    return members


def module_hook(
    mod_name: str, modules: dict = {}, recursive: bool = True
) -> "dict":
    """
    Function dissecting the an imported module.

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
            if not member and recursive and mod:
                sub_modules = get_submodules(mod)
                # if len(sub_modules) > 0:
                logger.info("Iterating over sub_modules of %s", mod_name)
                for sub_mod in sub_modules:
                    logger.info("Treating sub-module: %s", sub_mod)
                    modules = module_hook(sub_mod, modules=modules)
            # member_count = sum([len(m) for m in modules.values()])
        except ImportError:
            logger.error("Module %s can't be loaded!", mod_name)
    return modules
