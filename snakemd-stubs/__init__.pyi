from .document import Document as Document
from .elements import Block as Block
from .elements import Code as Code
from .elements import Element as Element
from .elements import Heading as Heading
from .elements import HorizontalRule as HorizontalRule
from .elements import Inline as Inline
from .elements import MDList as MDList
from .elements import Paragraph as Paragraph
from .elements import Quote as Quote
from .elements import Raw as Raw
from .elements import Table as Table
from .templates import Alert as Alert
from .templates import Checklist as Checklist
from .templates import CSVTable as CSVTable
from .templates import TableOfContents as TableOfContents
from .templates import Template as Template

def new_doc() -> Document: ...
