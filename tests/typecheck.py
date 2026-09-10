from pathlib import Path

from snakemd import (
    Alert,
    Checklist,
    Code,
    Document,
    Heading,
    Inline,
    MDList,
    Paragraph,
    Table,
    TableOfContents,
    new_doc,
)
from snakemd.elements import Quote, Raw
from snakemd.templates import CSVTable

doc: Document = new_doc()
doc.add_heading("SnakeMD", level=1)
doc.add_paragraph("Typed Markdown")
doc.add_block(Paragraph([Inline("content", bold=True)]))
doc.add_block(MDList(["one", Inline("two")]))
doc.add_block(Code("print('hello')", lang="python"))
doc.add_block(Quote("quoted"))
doc.add_block(Raw("---\ntitle: example\n---"))
doc.add_table(["Name"], [["SnakeMD"]], align=[Table.Align.LEFT])
doc.add_table_from_csv(Path("items.csv"))
doc.add_table_of_contents(range(1, 3))
doc.add_alert("Check this", Alert.Kind.NOTE)
doc.add_checklist(["one", "two"])

heading: Heading = Heading("A heading", 2)
inline: Inline = Inline("styled").bold().breakline()
paragraph: Paragraph = Paragraph("text").insert_link("text", "https://example.com")
table: Table = Table(["A"], [["B"]])
table.add_row(["C"])
checklist: Checklist = Checklist(["task"], checked=True)
toc: TableOfContents = TableOfContents()
csv_table: CSVTable = CSVTable(Path("items.csv"))

assert heading.get_level() == 2
assert inline.get_link() is None
_ = (paragraph, table, checklist, toc, csv_table)
