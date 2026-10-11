"""Positive consumer probe for the complete supported SnakeMD API."""

from __future__ import annotations

from pathlib import Path

from snakemd import (
    Alert,
    Block,
    Checklist,
    Code,
    Document,
    Element,
    Heading,
    HorizontalRule,
    Inline,
    MDList,
    Paragraph,
    Quote,
    Raw,
    Table,
    TableOfContents,
    Template,
    new_doc,
)
from snakemd.document import Document as ModuleDocument
from snakemd.elements import (
    Block as ModuleBlock,
)
from snakemd.elements import (
    Code as ModuleCode,
)
from snakemd.elements import (
    Element as ModuleElement,
)
from snakemd.elements import (
    Heading as ModuleHeading,
)
from snakemd.elements import (
    HorizontalRule as ModuleHorizontalRule,
)
from snakemd.elements import (
    Inline as ModuleInline,
)
from snakemd.elements import (
    MDList as ModuleMDList,
)
from snakemd.elements import (
    Paragraph as ModuleParagraph,
)
from snakemd.elements import (
    Quote as ModuleQuote,
)
from snakemd.elements import (
    Raw as ModuleRaw,
)
from snakemd.elements import (
    Table as ModuleTable,
)
from snakemd.templates import (
    Alert as ModuleAlert,
)
from snakemd.templates import (
    Checklist as ModuleChecklist,
)
from snakemd.templates import (
    CSVTable,
)
from snakemd.templates import (
    TableOfContents as ModuleTableOfContents,
)
from snakemd.templates import (
    Template as ModuleTemplate,
)


class SampleBlock(Block):
    def __str__(self) -> str:
        return "sample block"

    def __repr__(self) -> str:
        return "SampleBlock()"


class SampleTemplate(Template):
    def __str__(self) -> str:
        return "sample template"

    def __repr__(self) -> str:
        return "SampleTemplate()"


def exercise_public_api(csv_path: Path, output_dir: Path) -> str:
    """Call each public constructor, method, enum, and supported default."""
    initial_elements: list[Element] = [Raw("initial block")]
    doc: Document = Document(initial_elements)
    created_doc: Document = new_doc()
    _ = str(created_doc)
    _ = repr(doc)

    added_block: Block = doc.add_block(SampleBlock())
    raw: Raw = doc.add_raw("raw Markdown")
    heading: Heading = doc.add_heading("default heading")
    explicit_heading: Heading = doc.add_heading("level two", level=2)
    paragraph: Paragraph = doc.add_paragraph("paragraph text")
    ordered: MDList = doc.add_ordered_list(["first", "second"])
    unordered: MDList = doc.add_unordered_list(["one", "two"])
    checklist: Checklist = doc.add_checklist(["typed", "checked"])
    table: Table = doc.add_table(
        ["left", "center", "right"],
        [["a", "b", "c"]],
        align=[Table.Align.LEFT, Table.Align.CENTER, Table.Align.RIGHT],
        indent=2,
    )
    csv_table = doc.add_table_from_csv(csv_path)
    string_csv_table = doc.add_table_from_csv(str(csv_path))
    code: Code = doc.add_code("print('typed')", lang="python")
    quote: Quote = doc.add_quote("quoted text")
    horizontal_rule: HorizontalRule = doc.add_horizontal_rule()
    table_of_contents: TableOfContents = doc.add_table_of_contents(range(1, 4))
    alert: Alert = doc.add_alert("important", Alert.Kind.IMPORTANT)
    for kind in Alert.Kind:
        _ = Alert("all kinds are typed", kind)
    elements: list[Element] = doc.get_elements()

    styled = Inline(
        "inline",
        image="image.png",
        link="https://example.com",
        bold=True,
        italics=True,
        strikethrough=True,
        code=True,
        linebreak=True,
    )
    inline: Inline = (
        Inline("styled")
        .bold()
        .unbold()
        .italicize()
        .unitalicize()
        .strikethrough()
        .unstrikethrough()
        .code()
        .uncode()
        .breakline()
        .unbreakline()
        .link("https://example.com")
        .unlink()
        .reset()
    )
    doc.add_block(Paragraph([styled, inline]))
    doc.scramble()
    doc.dump("consumer-probe", directory=output_dir, ext="md", encoding="utf-8")
    _ = str(styled), repr(styled), inline.is_text(), inline.is_link()
    inline_text: str = inline.get_text()
    inline_link: str | None = inline.get_link()
    if inline_link is not None:
        raise AssertionError("unlink() should leave no link")
    _ = inline_text

    direct_code: Code = Code(code, lang="text")
    _ = direct_code == Code("print('typed')", lang="text")
    direct_heading: Heading = Heading(["one", Inline("two")], 3)
    direct_heading = direct_heading.promote().demote()
    _ = str(direct_heading), repr(direct_heading)
    _ = direct_heading.get_text(), direct_heading.get_level()
    direct_rule: HorizontalRule = HorizontalRule()
    _ = str(direct_rule), repr(direct_rule)
    direct_list: MDList = MDList(["one", Inline("two"), SampleBlock()], ordered=True)
    checked_list: MDList = MDList(["done"], checked=True)
    _ = str(direct_list), repr(direct_list), str(checked_list)
    direct_paragraph: Paragraph = Paragraph(["one", Inline("two")])
    direct_paragraph = (
        direct_paragraph.add("three")
        .replace("one", "first", count=1)
        .insert_link("first", "https://example.com", count=1)
        .replace_link("https://example.com", "https://example.org", count=1)
    )
    _ = str(direct_paragraph), repr(direct_paragraph)
    direct_quote: Quote = Quote(["quoted", SampleBlock()])
    direct_raw: Raw = Raw("raw")
    _ = str(direct_quote), repr(direct_quote), str(direct_raw), repr(direct_raw)
    direct_table: Table = Table(["header"], [["cell"]])
    direct_table.add_row(["another cell"])
    _ = str(direct_table), repr(direct_table)

    template = SampleTemplate()
    template.load([direct_heading, direct_paragraph])
    direct_alert: Alert = Alert("note", Alert.Kind.NOTE)
    direct_checklist: Checklist = Checklist(["task"], checked=[True])
    direct_csv: CSVTable = CSVTable(csv_path, encoding="utf-8")
    string_path_csv: CSVTable = CSVTable(str(csv_path))
    direct_toc: TableOfContents = TableOfContents()
    direct_toc.load([direct_heading])
    _ = (
        str(template),
        repr(template),
        str(direct_alert),
        repr(direct_alert),
        str(direct_checklist),
        repr(direct_checklist),
        str(direct_csv),
        repr(direct_csv),
        str(string_path_csv),
        repr(string_path_csv),
        str(direct_toc),
        repr(direct_toc),
    )

    _ = (
        ModuleDocument(),
        ModuleBlock,
        ModuleCode,
        ModuleElement,
        ModuleHeading,
        ModuleHorizontalRule,
        ModuleInline,
        ModuleMDList,
        ModuleParagraph,
        ModuleQuote,
        ModuleRaw,
        ModuleTable,
        ModuleAlert,
        ModuleChecklist,
        ModuleTableOfContents,
        ModuleTemplate,
    )

    # Keep each return visible to the strict checker without forcing runtime
    # behavior into this structural probe.
    _ = (
        added_block,
        raw,
        heading,
        explicit_heading,
        paragraph,
        ordered,
        unordered,
        checklist,
        table,
        csv_table,
        string_csv_table,
        code,
        quote,
        horizontal_rule,
        table_of_contents,
        alert,
        elements,
    )
    return str(doc)
