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
from typing import NoReturn, cast

from alphus_stub_quality.runtime_audit import (
    class_nodes,
    declared_abstract_methods,
    module_api_objects,
    root_api_objects,
    top_level_names,
    validate_stub_tree,
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
            forbidden_names=frozenset(STUB_REJECTIONS),
            annotation_widenings=ANNOTATION_WIDENINGS,
            return_annotation_widenings=RETURN_ANNOTATION_WIDENINGS,
            scoped_type_names=SCOPED_TYPE_NAMES,
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
        logger_value = getattr(runtime_modules[module_name], attribute_name, None)
        if not isinstance(logger_value, logging.Logger):
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
