import sys
import tempfile
import textwrap

from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import cast

import pytest

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent

from dbrownell_ParserLib.antlr.antlr_parser import AntlrParser, CreateAntlrParser
from dbrownell_ParserLib.antlr.antlr_visitor_mixin import AntlrVisitorMixin
from dbrownell_ParserLib.errors import Error, ErrorException
from dbrownell_ParserLib.terminal_element import Element, TerminalElement
from dbrownell_ParserLib.test_helpers.test_visitor import TestVisitor

from .test_helpers import BinaryExpression, UnaryExpression


# ----------------------------------------------------------------------
@pytest.fixture
def parser():
    sys.path.insert(0, str(Path(__file__).parent / "GeneratedCode" / "SignificantWhitespace"))
    with ExitStack(lambda: sys.path.pop(0)):
        from significant_whitespaceLexer import significant_whitespaceLexer as Lexer  # ty: ignore[unresolved-import]
        from significant_whitespaceParser import significant_whitespaceParser as Parser  # ty: ignore[unresolved-import]
        from significant_whitespaceVisitor import significant_whitespaceVisitor as Visitor  # ty: ignore[unresolved-import]

    # ----------------------------------------------------------------------
    class MyVisitor(AntlrVisitorMixin, Visitor):
        # ----------------------------------------------------------------------
        def visitAtom_expr(self, ctx: Parser.Atom_exprContext):
            value: str = ctx.getText()

            value = value.rstrip()
            if value.endswith("newLine"):
                value = value[: -len("newLine")]

            self._stack.append(TerminalElement[int](self.CreateRegion(ctx), int(value)))

        # ----------------------------------------------------------------------
        def visitUnary_expr(self, ctx: Parser.Unary_exprContext):
            assert len(ctx.children) == 5
            operator = ctx.children[1].getText()
            operator_region = self.CreateRegion(ctx.children[1])

            children = self.GetChildren(ctx)
            assert len(children) == 1
            assert isinstance(children[0], Element), children[0]

            self._stack.append(
                UnaryExpression(
                    self.CreateRegion(ctx),
                    TerminalElement[str](operator_region, operator),
                    children[0],
                ),
            )

        # ----------------------------------------------------------------------
        def visitPower_expr(self, ctx: Parser.Power_exprContext):
            self.VisitBinaryExpression(ctx)

        # ----------------------------------------------------------------------
        def visitMul_div_expr(self, ctx: Parser.Mul_div_exprContext):
            self.VisitBinaryExpression(ctx)

        # ----------------------------------------------------------------------
        def visitAdd_sub_expr(self, ctx: Parser.Add_sub_exprContext):
            self.VisitBinaryExpression(ctx)

        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        def VisitBinaryExpression(self, ctx) -> None:
            assert len(ctx.children) == 5
            operator = ctx.children[0].getText()
            operator_region = self.CreateRegion(ctx.children[0])

            children = self.GetChildren(ctx)
            assert len(children) == 2, children
            assert isinstance(children[0], Element), children[0]
            assert isinstance(children[1], Element), children[1]

            self._stack.append(
                BinaryExpression(
                    self.CreateRegion(ctx),
                    children[0],
                    TerminalElement[str](operator_region, operator),
                    children[1],
                ),
            )

    # ----------------------------------------------------------------------
    def InitLexer(lexer):
        lexer.CustomInit()

    # ----------------------------------------------------------------------

    return CreateAntlrParser(
        Lexer,
        Parser,
        MyVisitor,
        lambda parser: parser.entry_point__(),  # ty: ignore[unresolved-attribute]
        InitLexer,
    )


# ----------------------------------------------------------------------
def test_SingleFile(parser):
    dm_and_sink = iter(GenerateDoneManagerAndContent())

    dm = cast(DoneManager, next(dm_and_sink))

    result = parser(
        dm,
        Path(__file__).parent / "significant_whitespace.txt",
        None,
    )

    content = cast(str, next(dm_and_sink))

    assert dm.result == 0, content

    assert content == textwrap.dedent(
        """\
        Heading...
          Parsing...DONE! (0, <scrubbed duration>, 1 item succeeded, no items with errors, no items with warnings)
        DONE! (0, <scrubbed duration>)
        """,
    )

    assert len(result) == 1, result
    result = next(iter(result.values()))

    output = StringIO()
    visitor = TestVisitor(output)

    for element in result._stack:
        element.Accept(visitor)
        output.write("\n")

    assert output.getvalue() == textwrap.dedent(
        """\
        UnaryExpression, Ln 1 Col 1 - Ln 7 Col 1
          <<details>>
            TerminalElement, Ln 1 Col 2 - Ln 1 Col 3 -> '-' [str]
            BinaryExpression, Ln 2 Col 5 - Ln 7 Col 1
              <<details>>
                BinaryExpression, Ln 3 Col 9 - Ln 5 Col 15
                  <<details>>
                    TerminalElement, Ln 4 Col 13 - Ln 4 Col 14 -> '1' [int]
                    TerminalElement, Ln 3 Col 9 - Ln 3 Col 10 -> '+' [str]
                    TerminalElement, Ln 5 Col 13 - Ln 5 Col 15 -> '22' [int]
                TerminalElement, Ln 2 Col 5 - Ln 2 Col 6 -> '/' [str]
                TerminalElement, Ln 6 Col 9 - Ln 6 Col 12 -> '333' [int]

        TerminalElement, Ln 8 Col 1 - Ln 8 Col 2 -> '4' [int]

        BinaryExpression, Ln 10 Col 1 - Ln 13 Col 1
          <<details>>
            TerminalElement, Ln 11 Col 5 - Ln 11 Col 6 -> '5' [int]
            TerminalElement, Ln 10 Col 1 - Ln 10 Col 2 -> '+' [str]
            TerminalElement, Ln 12 Col 5 - Ln 12 Col 6 -> '6' [int]

        BinaryExpression, Ln 14 Col 1 - Ln 17 Col 1
          <<details>>
            TerminalElement, Ln 15 Col 5 - Ln 15 Col 6 -> '8' [int]
            TerminalElement, Ln 14 Col 1 - Ln 14 Col 2 -> '*' [str]
            TerminalElement, Ln 16 Col 5 - Ln 16 Col 9 -> '9999' [int]

        """,
    )


# ----------------------------------------------------------------------
def test_SyntaxError(parser):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(
            textwrap.dedent(
                """\
                +
                    1
                """,
            ),
        )

        temp_path = Path(f.name)

    with ExitStack(temp_path.unlink):
        dm_and_sink = iter(GenerateDoneManagerAndContent())
        dm = cast(DoneManager, next(dm_and_sink))

        result = parser(
            dm,
            temp_path,
            None,
        )

        content = cast(str, next(dm_and_sink))

        # dm.result reflects the error count
        assert dm.result == 1, content

        # The task completes successfully, but dm.result is set to error count afterwards
        assert content == textwrap.dedent(
            """\
            Heading...
              Parsing...DONE! (0, <scrubbed duration>, 1 item succeeded, no items with errors, no items with warnings)
            DONE! (1, <scrubbed duration>)
            """,
        )

        assert len(result) == 1, result
        error = next(iter(result.values()))

        assert isinstance(error, Error), error
        assert "no viable alternative" in error.message or "mismatched input" in error.message
        assert len(error.regions) == 1, error.regions
        assert error.regions[0].begin.line == 3
        assert error.regions[0].begin.column == 1
        assert error.regions[0].end == error.regions[0].begin
