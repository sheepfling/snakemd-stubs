"""Compare the installed SnakeMD runtime surface with the installed stubs.

The audit intentionally treats ``snakemd`` as the supported public facade and
each implementation module's locally defined classes/functions as its owned
surface. Public names imported into a module as implementation helpers are
recorded separately; they are not promoted to supported API just because the
runtime module lacks ``__all__``.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import logging
from enum import Enum
from importlib.metadata import distribution, version
from pathlib import Path
from types import ModuleType
from typing import NoReturn, cast

from alphus_stub_quality.api_audit_support import (
    assigned_public_instance_attributes,
    decorator_names,
    validate_enum,
    validate_signature,
)
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

MODULES = {
    "snakemd": "__init__.pyi",
    "snakemd.document": "document.pyi",
    "snakemd.elements": "elements.pyi",
    "snakemd.templates": "templates.pyi",
}
ANNOTATION_WIDENINGS = {
    ("snakemd.document.Document.add_table_from_csv", "path"): (("name", "str"),),
    ("snakemd.templates.CSVTable.__init__", "path"): (("name", "str"),),
}
RETURN_ANNOTATION_WIDENINGS = {
    "snakemd.elements.Inline.get_link": (("name", "None"),),
}
SCOPED_TYPE_NAMES = frozenset({"Kind", "Align"})

# Snapshot every other non-private runtime binding so wildcard imports and
# imported implementation helpers cannot silently become an unreviewed API.
EXPECTED_NON_API_BINDINGS = {
    "snakemd": {
        "ABC",
        "Enum",
        "Iterable",
        "abstractmethod",
        "annotations",
        "auto",
        "csv",
        "document",
        "elements",
        "logger",
        "logging",
        "os",
        "pathlib",
        "random",
        "re",
        "templates",
    },
    "snakemd.document": {
        "Alert",
        "Block",
        "CSVTable",
        "Checklist",
        "Code",
        "Element",
        "Heading",
        "HorizontalRule",
        "Inline",
        "Iterable",
        "MDList",
        "Paragraph",
        "Quote",
        "Raw",
        "Table",
        "TableOfContents",
        "Template",
        "annotations",
        "logger",
        "logging",
        "os",
        "pathlib",
        "random",
    },
    "snakemd.elements": {
        "ABC",
        "Enum",
        "Iterable",
        "abstractmethod",
        "annotations",
        "auto",
        "logger",
        "logging",
    },
    "snakemd.templates": {
        "Block",
        "Element",
        "Enum",
        "Heading",
        "Inline",
        "Iterable",
        "MDList",
        "Quote",
        "Table",
        "annotations",
        "auto",
        "csv",
        "logger",
        "logging",
        "os",
        "re",
    },
}
STUB_REJECTIONS = {
    "Any",
    "__getattr__",
    "__getattribute__",
    "__dir__",
}
CLASS_METADATA = {
    "__abstractmethods__",
    "__classcell__",
    "__dict__",
    "__doc__",
    "__module__",
    "__weakref__",
}


def fail(message: str) -> NoReturn:
    raise SystemExit(f"API coverage audit failed: {message}")


def module_api_objects(module: ModuleType) -> dict[str, object]:
    """Return classes/functions defined in a runtime module, not imports."""
    return {
        name: value
        for name, value in vars(module).items()
        if not name.startswith("_")
        and (inspect.isclass(value) or inspect.isfunction(value))
        and getattr(value, "__module__", None) == module.__name__
    }


def root_api_objects(module: ModuleType, package_modules: set[str]) -> dict[str, object]:
    """Return the supported root facade's own objects and package re-exports."""
    return {
        name: value
        for name, value in vars(module).items()
        if not name.startswith("_")
        and (inspect.isclass(value) or inspect.isfunction(value))
        and getattr(value, "__module__", None) in package_modules
    }


def top_level_names(tree: ast.Module, *, include_imports: bool) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif include_imports and isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif include_imports and isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.partition(".")[0])
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def function_nodes(tree: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def class_nodes(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def class_member_nodes(node: ast.ClassDef) -> dict[str, ast.AST]:
    members: dict[str, ast.AST] = {}
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            members[child.name] = child
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            targets = child.targets if isinstance(child, ast.Assign) else [child.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    members[target.id] = child
    return members


def visible_class_member(name: str, value: object) -> bool:
    if name in CLASS_METADATA:
        return False
    if not name.startswith("_"):
        return True
    return (
        name.startswith("__")
        and name.endswith("__")
        and (inspect.isroutine(value) or isinstance(value, (staticmethod, classmethod, property)))
    )


def validate_stub_tree(
    module_name: str, tree: ast.Module, runtime_module: ModuleType, source_path: Path
) -> tuple[int, int]:
    source_tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in STUB_REJECTIONS:
            fail(f"{module_name} stub uses forbidden broad/dynamic name {node.id!r}")
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in STUB_REJECTIONS
        ):
            fail(f"{module_name} stub defines a dynamic fallback {node.name!r}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name.startswith("_") and not (
                node.name.startswith("__") and node.name.endswith("__")
            ):
                fail(f"{module_name} stub exposes private declaration {node.name!r}")
        if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
            fail(f"{module_name} stub uses a wildcard import")

    runtime_own = module_api_objects(runtime_module)
    stub_own = top_level_names(tree, include_imports=False)
    if set(runtime_own) != stub_own:
        fail(
            f"{module_name} owned definitions differ: "
            f"runtime {sorted(runtime_own)}; stubs {sorted(stub_own)}"
        )

    stub_classes = class_nodes(tree)
    source_classes = class_nodes(source_tree)
    function_defs = function_nodes(tree)
    source_functions = function_nodes(source_tree)
    runtime_methods = 0
    enum_count = 0
    for name, value in runtime_own.items():
        if inspect.isfunction(value):
            stub_function = function_defs.get(name)
            if stub_function is None:
                fail(f"missing function stub {module_name}.{name}")
            source_function = source_functions.get(name)
            if source_function is None:
                fail(f"missing runtime source for {module_name}.{name}")
            validate_signature(
                f"{module_name}.{name}",
                stub_function,
                source_function,
                value,
                annotation_widenings=ANNOTATION_WIDENINGS,
                return_annotation_widenings=RETURN_ANNOTATION_WIDENINGS,
                scoped_type_names=SCOPED_TYPE_NAMES,
            )
            runtime_methods += 1
            continue

        if not inspect.isclass(value):
            fail(f"runtime API member {module_name}.{name} is not a class or function")
        runtime_class = value
        stub_class = stub_classes[name]
        source_class = source_classes.get(name)
        if source_class is None:
            fail(f"missing runtime source class for {module_name}.{name}")
        stub_bases = [
            base.id
            if isinstance(base, ast.Name)
            else base.attr
            if isinstance(base, ast.Attribute)
            else ast.unparse(base)
            for base in stub_class.bases
        ]
        runtime_bases = [base.__name__ for base in runtime_class.__bases__]
        if not stub_bases and runtime_bases == ["object"]:
            runtime_bases = []
        if stub_bases != runtime_bases:
            fail(
                f"base classes differ for {module_name}.{name}: "
                f"stub {stub_bases!r}; runtime {runtime_bases!r}"
            )
        source_methods = {
            member.name: member
            for member in source_class.body
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if issubclass(runtime_class, Enum):
            enum_count += 1
        if issubclass(runtime_class, Enum):
            validate_enum(f"{module_name}.{name}", runtime_class, stub_class)
            continue

        stub_members = class_member_nodes(stub_class)
        runtime_member_values = {
            member_name: member
            for member_name, member in vars(runtime_class).items()
            if visible_class_member(member_name, member)
        }
        if set(runtime_member_values) != set(stub_members):
            fail(
                f"class members differ for {module_name}.{name}: "
                f"stub {sorted(stub_members)}; runtime {sorted(runtime_member_values)}"
            )

        for member_name, runtime_member in runtime_member_values.items():
            stub_member = stub_members[member_name]
            label = f"{module_name}.{name}.{member_name}"
            if isinstance(stub_member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not inspect.isroutine(runtime_member) and not isinstance(
                    runtime_member, (staticmethod, classmethod, property)
                ):
                    fail(f"stub callable {label} is not a runtime callable")
                source_member = source_methods.get(member_name)
                if source_member is None:
                    fail(f"missing runtime source method for {label}")
                validate_signature(
                    label,
                    stub_member,
                    source_member,
                    runtime_member,
                    owner_class=name,
                    annotation_widenings=ANNOTATION_WIDENINGS,
                    return_annotation_widenings=RETURN_ANNOTATION_WIDENINGS,
                    scoped_type_names=SCOPED_TYPE_NAMES,
                )
                runtime_methods += 1
            elif isinstance(stub_member, ast.ClassDef):
                if not inspect.isclass(runtime_member):
                    fail(f"stub nested class {label} is not a runtime class")
                if not issubclass(runtime_member, Enum):
                    fail(f"nested class {label} is not an enum and needs explicit audit support")
                enum_count += 1
                validate_enum(label, runtime_member, stub_member)
            else:
                if inspect.isroutine(runtime_member) or isinstance(
                    runtime_member, (staticmethod, classmethod, property)
                ):
                    fail(f"runtime callable {label} is not declared as a stub method")

        assigned = assigned_public_instance_attributes(source_path, name)
        declared_attributes = {
            member_name
            for member_name, member in stub_members.items()
            if isinstance(member, (ast.Assign, ast.AnnAssign))
        }
        property_attributes = {
            member_name
            for member_name, member in stub_members.items()
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
            and "property" in decorator_names(member)
        }
        if assigned - declared_attributes - property_attributes:
            fail(
                f"public instance attributes missing from {module_name}.{name}: "
                f"{sorted(assigned - declared_attributes - property_attributes)}"
            )

        for member_name, runtime_member in runtime_member_values.items():
            declared_member = stub_members.get(member_name)
            if not isinstance(declared_member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            stub_abstract = "abstractmethod" in decorator_names(declared_member)
            runtime_abstract = bool(getattr(runtime_member, "__isabstractmethod__", False))
            if stub_abstract != runtime_abstract:
                fail(f"abstractmethod marker differs for {module_name}.{name}.{member_name}")

    return runtime_methods, enum_count


def declared_abstract_methods(
    runtime_class: type[object], trees: dict[str, ast.Module]
) -> set[str]:
    abstract: set[str] = set()
    for base in reversed(runtime_class.__mro__):
        module_tree = trees.get(cast(str, getattr(base, "__module__", "")))
        if module_tree is None:
            continue
        class_node = class_nodes(module_tree).get(base.__name__)
        if class_node is None:
            continue
        for name, member in class_member_nodes(class_node).items():
            if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if "abstractmethod" in decorator_names(member):
                abstract.add(name)
            else:
                abstract.discard(name)
    return abstract


def main() -> None:
    runtime_modules = {name: importlib.import_module(name) for name in MODULES}
    package_module_names = set(MODULES)
    runtime_root = runtime_modules["snakemd"]
    stub_distribution = distribution("snakemd-stubs")
    stub_root = Path(str(stub_distribution.locate_file("snakemd-stubs")))

    runtime_version = version("SnakeMD")
    required = [
        Requirement(item)
        for item in (stub_distribution.requires or ())
        if canonicalize_name(Requirement(item).name) == canonicalize_name("SnakeMD")
    ]
    if len(required) != 1 or runtime_version not in required[0].specifier:
        fail(
            f"installed SnakeMD {runtime_version} is outside the installed stub "
            f"requirement {required!r}"
        )

    trees: dict[str, ast.Module] = {}
    stub_paths: dict[str, Path] = {}
    for module_name, relative in MODULES.items():
        stub_path = stub_root / relative
        runtime_module = runtime_modules[module_name]
        if not stub_path.is_file():
            fail(f"installed stub artifact is missing {relative}")
        stub_text = stub_path.read_text(encoding="utf-8")
        if any(
            marker in stub_text.lower()
            for marker in ("type: ignore", "pyright: ignore", "mypy: ignore")
        ):
            fail(f"{relative} contains a type-checker suppression")
        trees[module_name] = ast.parse(stub_text, filename=str(stub_path))
        stub_paths[module_name] = Path(cast(str, runtime_module.__file__))

    root_api = root_api_objects(runtime_root, package_module_names)
    root_declared = top_level_names(trees["snakemd"], include_imports=True)
    if set(root_api) != root_declared:
        fail(f"root facade differs: runtime {sorted(root_api)}; stubs {sorted(root_declared)}")

    for module_name, runtime_module in runtime_modules.items():
        non_api = {name for name in vars(runtime_module) if not name.startswith("_")} - set(
            module_api_objects(runtime_module)
        )
        if module_name == "snakemd":
            non_api -= set(root_api)
        if non_api != EXPECTED_NON_API_BINDINGS[module_name]:
            fail(
                f"runtime namespace bindings changed for {module_name}: "
                f"expected {sorted(EXPECTED_NON_API_BINDINGS[module_name])}; "
                f"found {sorted(non_api)}"
            )

    # All package-owned root re-exports must come from an audited owner module.
    for name, value in root_api.items():
        owner = cast(str, getattr(value, "__module__", ""))
        if owner not in package_module_names:
            fail(f"root API symbol {name} has an unaudited owner {owner!r}")

    total_methods = 0
    total_enums = 0
    total_classes = 0
    for module_name, runtime_module in runtime_modules.items():
        methods, enums = validate_stub_tree(
            module_name,
            trees[module_name],
            runtime_module,
            stub_paths[module_name],
        )
        total_methods += methods
        total_enums += enums
        total_classes += len(class_nodes(trees[module_name]))

    for module_name, runtime_module in runtime_modules.items():
        for name, value in module_api_objects(runtime_module).items():
            if not inspect.isclass(value) or issubclass(value, Enum):
                continue
            runtime_abstract = set(getattr(value, "__abstractmethods__", ()))
            stub_abstract = declared_abstract_methods(value, trees)
            if stub_abstract != runtime_abstract:
                fail(
                    f"abstract class contract differs for {module_name}.{name}: "
                    f"stub {sorted(stub_abstract)}; runtime {sorted(runtime_abstract)}"
                )

    # The allowlist is deliberately exact and limited to runtime loggers.
    allowlist_path = Path("stubtest-allowlist.txt")
    allowlist = {
        line.strip()
        for line in allowlist_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    expected_allowlist = {
        "snakemd.document.logger",
        "snakemd.elements.logger",
        "snakemd.templates.logger",
    }
    if allowlist != expected_allowlist:
        fail(
            f"stubtest allowlist changed: "
            f"expected {sorted(expected_allowlist)}; found {sorted(allowlist)}"
        )
    for dotted_name in allowlist:
        module_name, attribute_name = dotted_name.rsplit(".", 1)
        value = getattr(runtime_modules[module_name], attribute_name, None)
        if not isinstance(value, logging.Logger):
            fail(f"allowlisted implementation detail is not a logger: {dotted_name}")

    print(f"Runtime SnakeMD {runtime_version} satisfies {required[0].specifier}.")
    print(
        f"Root facade: {len(root_api)} class/function exports checked "
        f"across {len(MODULES)} modules."
    )
    print(
        f"Owned declarations: {total_classes} classes, {total_enums} nested enums, "
        f"and {total_methods} public callables checked."
    )
    print(
        "Signatures, parameter kinds, defaults, decorators, enum members/values, "
        "and public attributes match."
    )
    print(
        "Runtime import leakage is inventoried; no Any or dynamic fallback is present in the stubs."
    )
    print("stubtest allowlist is exactly three module logger implementation details.")


if __name__ == "__main__":
    main()
