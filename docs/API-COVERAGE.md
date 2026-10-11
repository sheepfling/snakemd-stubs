# SnakeMD API coverage evidence

This inventory records the published `snakemd-stubs 2.4.1.0` surface against
the official `SnakeMD 2.4.1` runtime source and wheel. The runtime release was
published May 30, 2026; the stubs were published September 10, 2026. The wheel
checksums verified during the comparison were:

- SnakeMD wheel: `3f1cc8547dbd5b28114be8c4a933159703ff81f0f1332ef4c03150a74193e60c`
- snakemd-stubs wheel: `02b299cc85b59de64a5af7d64db628e65602f39bc3c92dfa0b6fb01d5e4d821e`

The current runtime is [SnakeMD 2.4.1 on PyPI](https://pypi.org/project/SnakeMD/2.4.1/).
Its release notes describe only a logging-level change, and the upstream
`main` branch compared equal to the v2.4.1 release tag at the time of review.
The stub distribution declares `SnakeMD>=2.4.0,<2.5.0` and Python
`>=3.10,<4.0`; the runtime advertises Python 3.10 through 3.14.

## Public surface

SnakeMD's root package is the documented facade; its module docstring says
classes are imported there so users do not depend on the implementation file
layout. The package exposes these 17 classes and one convenience function:

`Alert`, `Block`, `Checklist`, `Code`, `CSVTable`, `Document`, `Element`,
`Heading`, `HorizontalRule`, `Inline`, `MDList`, `Paragraph`, `Quote`, `Raw`,
`Table`, `TableOfContents`, `Template`, and `new_doc()`.

The callable inventory below is grouped by the module that defines each class.
The annotations in the installed `.pyi` files are the declared parameter and
return types; the API audit compares them to runtime source annotations where
available and type-checks positive and negative consumer calls.

### `snakemd`

- **Function:** `new_doc()`.

### `snakemd.document`

- **Document:** `__init__(elements=None)`, `__str__()`, `__repr__()`,
  `get_elements()`, `add_block(block)`, `add_raw(text)`,
  `add_heading(text, level=1)`, `add_paragraph(text)`,
  `add_ordered_list(items)`, `add_unordered_list(items)`, `add_checklist(items)`,
  `add_table(header, data, align=None, indent=0)`, `add_table_from_csv(path)`,
  `add_code(code, lang="generic")`, `add_quote(text)`, `add_horizontal_rule()`,
  `add_table_of_contents(levels=range(2, 3))`,
  `add_alert(message, kind=Alert.Kind.NOTE)`, `scramble()`,
  `dump(name, directory="", ext="md", encoding="utf-8")`.

### `snakemd.elements`

- **Element:** abstract `__str__()`, abstract `__repr__()`.
- **Block:** no locally defined callable; abstract methods inherited from `Element`.
- **Inline:** `__init__(text, image=None, link=None, bold=False, italics=False,`
  `strikethrough=False, code=False, linebreak=False)`, `__str__()`, `__repr__()`,
  `is_text()`, `is_link()`, `get_text()`, `get_link()`, `bold()`, `unbold()`,
  `italicize()`, `unitalicize()`, `strikethrough()`, `unstrikethrough()`,
  `code()`, `uncode()`, `breakline()`, `unbreakline()`, `link(link)`, `unlink()`,
  `reset()`.
- **Code:** `__init__(code, lang="generic")`, `__str__()`, `__repr__()`,
  `__eq__(other)`.
- **Heading:** `__init__(text, level)`, `__str__()`, `__repr__()`, `promote()`,
  `demote()`, `get_text()`, `get_level()`.
- **HorizontalRule:** `__str__()`, `__repr__()`.
- **MDList:** `__init__(items, ordered=False, checked=None)`, `__str__()`,
  `__repr__()`.
- **Paragraph:** `__init__(content)`, `__str__()`, `__repr__()`, `add(text)`,
  `replace(target, replacement, count=-1)`,
  `insert_link(target, link, count=-1)`,
  `replace_link(target_link, replacement_link, count=-1)`.
- **Quote:** `__init__(content)`, `__str__()`, `__repr__()`.
- **Raw:** `__init__(text)`, `__str__()`, `__repr__()`.
- **Table:** `__init__(header, body=None, align=None, indent=0)`, `__str__()`,
  `__repr__()`, `add_row(row)`.

### `snakemd.templates`

- **Template:** abstract render methods inherited from `Element`, `__init__()`,
  `load(elements)`.
- **Alert:** `__init__(message, kind)`, `__str__()`, `__repr__()`.
- **Checklist:** `__init__(items, checked=False)`, `__str__()`, `__repr__()`.
- **CSVTable:** `__init__(path, encoding="utf-8")`, `__str__()`, `__repr__()`.
- **TableOfContents:** `__init__(levels=range(2, 3))`, `__str__()`, `__repr__()`.

There are 18 root facade names (17 classes and `new_doc`) and 90 owned public
callables, including constructors and dunder rendering methods. The audit
compares each callable's parameter names, ordering, kinds, required/optional
status, default values, annotations, and decorators. Two `path` parameter
widenings account for runtime implementations passing the value to `open`,
which accepts both strings and `os.PathLike`; both supported forms are
type-checked and executed by the consumer fixture. The runtime source
annotation is narrower, so the audit permits exactly this pair rather than
weakening annotation comparison generally:

- `Document.add_table_from_csv(path)`
- `CSVTable.__init__(path, encoding="utf-8")`

The third explicit correction is `Inline.get_link() -> str | None`. SnakeMD's
runtime source annotates the return as `str`, but the method returns its
`_link` field directly, which is `None` for an unlinked `Inline`. The fixture
checks that case at runtime and assigns the result to `str | None`; the audit
allows `None` only for this exact return value.

The abstract contract is explicit: `Element.__str__` and `Element.__repr__`
are abstract; `Block` and `Template` remain abstract through inheritance;
concrete element and template classes provide their render methods. The two
nested enums are checked member-by-member and value-by-value:

- `Table.Align`: `LEFT=1`, `RIGHT=2`, `CENTER=3`
- `Alert.Kind`: `NOTE=1`, `TIP=2`, `IMPORTANT=3`, `WARNING=4`, `CAUTION=5`

There are no public instance fields in the runtime classes. Their instance
state uses private names. The only supported class attributes are the nested
enum types and their members. The private `Inline._apply_styles_from` helper
was removed from the stubs; no single-underscore runtime implementation method
is declared as user API. The audit compares direct base classes and each
class's locally defined members to the runtime, inherited abstract-method
contracts, and public instance-attribute assignments.

## Runtime namespace bindings outside the API

The runtime has no `__all__`, so Python also exposes imported helper names.
The audit snapshots these bindings separately and fails if the set changes;
the stubs do not promote them into the supported facade.

- `snakemd`: `ABC`, `Enum`, `Iterable`, `abstractmethod`, `annotations`, `auto`,
  `csv`, `document`, `elements`, `logger`, `logging`, `os`, `pathlib`, `random`,
  `re`, `templates`.
- `snakemd.document`: `Alert`, `Block`, `CSVTable`, `Checklist`, `Code`,
  `Element`, `Heading`, `HorizontalRule`, `Inline`, `Iterable`, `MDList`,
  `Paragraph`, `Quote`, `Raw`, `Table`, `TableOfContents`, `Template`,
  `annotations`, `logger`, `logging`, `os`, `pathlib`, `random`.
- `snakemd.elements`: `ABC`, `Enum`, `Iterable`, `abstractmethod`, `annotations`,
  `auto`, `logger`, `logging`.
- `snakemd.templates`: `Block`, `Element`, `Enum`, `Heading`, `Inline`,
  `Iterable`, `MDList`, `Quote`, `Table`, `annotations`, `auto`, `csv`, `logger`,
  `logging`, `os`, `re`.

Only the three module logger globals remain in `stubtest-allowlist.txt`, and the
audit checks that each is a `logging.Logger`. The allowlist is exact: it has no
module-wide, regular-expression, or missing-module exemption. The stubs contain
no `Any`, dynamic fallback, wildcard import, or private method declaration.

## Durable checks

`tests/audit_api_coverage.py` loads the installed runtime and installed stub
wheel, verifies the stub package's runtime dependency range, checks every
facade export and module-owned definition, and compares signatures, defaults,
decorators, nested enums, abstract methods, and public attributes. It also
checks the namespace-binding snapshot and the narrow stubtest allowlist.

`tests/typecheck.py` calls every public constructor/method with supported input
types and assigns all returns to their intended types. The expected-negative
fixture checks invalid names, argument types, enum members, and abstract-class
instantiation under both mypy and Pyright. `tests/runtime_smoke.py` executes the
positive fixture against the installed runtime and checks document rendering
and `dump` output.

Run the build-and-consumer check from the repo root:

```shell
python tests/verify_compatibility.py --with-twine
```

It builds the wheel and sdist from a temporary copy, writes artifacts outside
the checkout, installs the wheel, and runs all fixtures from a separate
consumer directory. Alphus owns the ordered local aggregate in
`quality-gates.toml`; `mdrepo` and `rumdl` apply the repo's Markdown graph and
style policies. Merge CI runs this Python compatibility aggregate once on
Python 3.12 and the exact `SnakeMD==2.4.1` pin.

## Coverage boundaries

This is structural API and typing coverage, not a full semantic test of every
rendered Markdown edge case. The runtime smoke proves the calls can execute
against the pinned runtime and that a rendered document can be written. It does
not replace behavior-focused unit tests for escaping, Markdown rendering,
template mutation, CSV edge cases, or error conditions.

Routine CI covers Python 3.12 with SnakeMD 2.4.1. Python 3.10, 3.11, 3.13,
3.14 and the older supported runtime 2.4.0 remain release-only matrix checks,
as documented in the README. This distinction avoids presenting one interpreter
and one pinned runtime as evidence for the entire declared support range.
