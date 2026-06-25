import sys
import tempfile
import textwrap

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import cast, override

import pytest

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent

from dbrownell_ParserLib import (
    AntlrParser,
    CreateAntlrParser,
    Error,
    Expression,
    InsignificantWhitespaceAntlrVisitorMixin,
    TerminalExpression,
)

from .test_helpers import BinaryExpression, OutputVisitor, UnaryExpression


# ----------------------------------------------------------------------
@pytest.fixture
def parser():
    sys.path.insert(0, str(Path(__file__).parent / "GeneratedCode" / "InsignificantWhitespace"))
    with ExitStack(lambda: sys.path.pop(0)):
        from insignificant_whitespaceLexer import insignificant_whitespaceLexer as Lexer  # ty: ignore[unresolved-import]
        from insignificant_whitespaceParser import insignificant_whitespaceParser as Parser  # ty: ignore[unresolved-import]
        from insignificant_whitespaceVisitor import insignificant_whitespaceVisitor as Visitor  # ty: ignore[unresolved-import]

    # ----------------------------------------------------------------------
    class MyVisitor(InsignificantWhitespaceAntlrVisitorMixin, Visitor):
        # ----------------------------------------------------------------------
        def visitExpr(self, ctx: Parser.ExprContext):
            if len(ctx.children) != 3:
                return self.visitChildren(ctx)

            operator = TerminalExpression[str](self.CreateRegion(ctx.children[1]), ctx.children[1].getText())

            children = self.GetChildren(ctx)
            assert len(children) == 2, children
            assert isinstance(children[0], Expression), children[0]
            assert isinstance(children[1], Expression), children[1]

            self._stack.append(
                BinaryExpression(
                    self.CreateRegion(ctx),
                    children[0],
                    operator,
                    children[1],
                ),
            )

        # ----------------------------------------------------------------------
        def visitUnary_expr(self, ctx: Parser.Unary_exprContext):
            children = self.GetChildren(ctx)
            assert len(children) == 1, children
            assert isinstance(children[0], Expression), children[0]

            self._stack.append(
                UnaryExpression(
                    self.CreateRegion(ctx),
                    TerminalExpression(self.CreateRegion(ctx.children[0]), ctx.children[0].getText()),
                    children[0],
                ),
            )

        # ----------------------------------------------------------------------
        def visitGrouped_expr(self, ctx: Parser.Grouped_exprContext):
            children = self.GetChildren(ctx)
            assert len(children) == 1, children
            assert isinstance(children[0], Expression), children[0]

            self._stack.append(children[0])

        # ----------------------------------------------------------------------
        def visitAtom(self, ctx: Parser.AtomContext):
            self._stack.append(TerminalExpression[int](self.CreateRegion(ctx), int(ctx.getText())))

    # ----------------------------------------------------------------------
    return CreateAntlrParser(
        Lexer,
        Parser,
        MyVisitor,
        lambda parser: parser.start__(),  # ty: ignore[unresolved-attribute]
    )


# ----------------------------------------------------------------------
def test_SingleFile(parser):
    dm_and_sink = iter(GenerateDoneManagerAndContent())

    dm = cast(DoneManager, next(dm_and_sink))

    result = parser(
        dm,
        Path(__file__).parent / "insignificant_whitespace.txt",
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
    visitor = OutputVisitor(output)

    for expression in result._stack:
        expression.Accept(visitor)

    assert output.getvalue() == textwrap.dedent(
        """\
        UnaryExpression, Ln 1 Col 1 - Ln 1 Col 16
        TerminalExpression, Ln 1 Col 1 - Ln 1 Col 2
        -
        BinaryExpression, Ln 1 Col 2 - Ln 1 Col 16
          BinaryExpression, Ln 1 Col 3 - Ln 1 Col 9
            TerminalExpression, Ln 1 Col 3 - Ln 1 Col 4
            1
            TerminalExpression, Ln 1 Col 5 - Ln 1 Col 6
            +
            TerminalExpression, Ln 1 Col 7 - Ln 1 Col 9
            22
          TerminalExpression, Ln 1 Col 11 - Ln 1 Col 12
          /
          TerminalExpression, Ln 1 Col 13 - Ln 1 Col 16
          333
        TerminalExpression, Ln 2 Col 1 - Ln 2 Col 2
        4
        BinaryExpression, Ln 3 Col 1 - Ln 3 Col 6
          TerminalExpression, Ln 3 Col 1 - Ln 3 Col 2
          5
          TerminalExpression, Ln 3 Col 3 - Ln 3 Col 4
          +
          TerminalExpression, Ln 3 Col 5 - Ln 3 Col 6
          6
        BinaryExpression, Ln 5 Col 1 - Ln 7 Col 10
          TerminalExpression, Ln 5 Col 1 - Ln 5 Col 2
          8
          TerminalExpression, Ln 6 Col 5 - Ln 6 Col 6
          *
          TerminalExpression, Ln 7 Col 9 - Ln 7 Col 10
          9
        """,
    )


# ----------------------------------------------------------------------
def test_SyntaxError(parser):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("1 +\n")  # Incomplete expression - missing operand
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
        assert error.regions[0].begin.line == 2
        assert error.regions[0].begin.column == 1
        assert error.regions[0].end == error.regions[0].begin
