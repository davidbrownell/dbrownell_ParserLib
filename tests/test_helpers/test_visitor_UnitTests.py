"""Unit tests for the test_visitor module."""

import io
import textwrap

from dataclasses import dataclass
from pathlib import Path
from typing import override

from dbrownell_ParserLib.element import Element
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_element import TerminalElement
from dbrownell_ParserLib.test_helpers import test_visitor


# ----------------------------------------------------------------------
def _CreateRegion(
    begin_line: int,
    begin_column: int,
    end_line: int | None = None,
    end_column: int | None = None,
) -> Region:
    begin = Location(line=begin_line, column=begin_column)
    end = begin if end_line is None or end_column is None else Location(line=end_line, column=end_column)

    return Region(filename=Path("test.txt"), begin=begin, end=end)


# ----------------------------------------------------------------------
@dataclass(eq=False)
class _DetailsElement(Element):
    """Element with details for testing detail visitation."""

    left: Element
    right: Element

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Element._GenerateAcceptDetailsResultType:
        yield "left", self.left
        yield "right", self.right


# ----------------------------------------------------------------------
@dataclass(eq=False)
class _ChildrenElement(Element):
    """Element with children for testing children visitation."""

    children: list[Element]

    # ----------------------------------------------------------------------
    @override
    def _GetAcceptChildren(self) -> Element._GetAcceptChildrenResultType:
        return ("children", self.children)


# ----------------------------------------------------------------------
def _Visit(element: Element) -> str:
    output = io.StringIO()

    element.Accept(test_visitor.TestVisitor(output))

    return output.getvalue()


# ----------------------------------------------------------------------
class TestTestVisitor:
    # ----------------------------------------------------------------------
    def test_ElementWithSingleLocationRegion(self):
        element = TerminalElement[int](_CreateRegion(3, 5), 42)

        assert _Visit(element) == "TerminalElement, Ln 3 Col 5 -> '42' [int]\n"

    # ----------------------------------------------------------------------
    def test_ElementWithRangeRegion(self):
        element = TerminalElement[int](_CreateRegion(1, 1, 2, 4), 42)

        assert _Visit(element) == "TerminalElement, Ln 1 Col 1 - Ln 2 Col 4 -> '42' [int]\n"

    # ----------------------------------------------------------------------
    def test_ElementWithDetails(self):
        element = _DetailsElement(
            _CreateRegion(1, 1, 1, 10),
            TerminalElement[int](_CreateRegion(1, 2), 1),
            TerminalElement[int](_CreateRegion(1, 8), 2),
        )

        assert _Visit(element) == textwrap.dedent(
            """\
            _DetailsElement, Ln 1 Col 1 - Ln 1 Col 10
              <<details>>
                TerminalElement, Ln 1 Col 2 -> '1' [int]
                TerminalElement, Ln 1 Col 8 -> '2' [int]
            """,
        )

    # ----------------------------------------------------------------------
    def test_ElementWithChildren(self):
        element = _ChildrenElement(
            _CreateRegion(1, 1, 3, 1),
            [
                TerminalElement[int](_CreateRegion(1, 5), 1),
                TerminalElement[int](_CreateRegion(2, 5), 2),
            ],
        )

        assert _Visit(element) == textwrap.dedent(
            """\
            _ChildrenElement, Ln 1 Col 1 - Ln 3 Col 1
              <<children: children>>
                TerminalElement, Ln 1 Col 5 -> '1' [int]
                TerminalElement, Ln 2 Col 5 -> '2' [int]
            """,
        )

    # ----------------------------------------------------------------------
    def test_NestedElements(self):
        element = _ChildrenElement(
            _CreateRegion(1, 1, 5, 1),
            [
                _DetailsElement(
                    _CreateRegion(2, 1, 2, 10),
                    TerminalElement[int](_CreateRegion(2, 2), 1),
                    TerminalElement[int](_CreateRegion(2, 8), 2),
                ),
                TerminalElement[int](_CreateRegion(4, 1), 3),
            ],
        )

        assert _Visit(element) == textwrap.dedent(
            """\
            _ChildrenElement, Ln 1 Col 1 - Ln 5 Col 1
              <<children: children>>
                _DetailsElement, Ln 2 Col 1 - Ln 2 Col 10
                  <<details>>
                    TerminalElement, Ln 2 Col 2 -> '1' [int]
                    TerminalElement, Ln 2 Col 8 -> '2' [int]
                TerminalElement, Ln 4 Col 1 -> '3' [int]
            """,
        )

    # ----------------------------------------------------------------------
    def test_DisabledElementIsNotVisited(self):
        child1 = TerminalElement[int](_CreateRegion(1, 5), 1)
        child2 = TerminalElement[int](_CreateRegion(2, 5), 2)

        element = _ChildrenElement(_CreateRegion(1, 1, 3, 1), [child1, child2])

        child1.Disable()

        assert _Visit(element) == textwrap.dedent(
            """\
            _ChildrenElement, Ln 1 Col 1 - Ln 3 Col 1
              <<children: children>>
                TerminalElement, Ln 2 Col 5 -> '2' [int]
            """,
        )
