"""Unit tests for ANTLR visitor mixins."""

from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

import antlr4
import pytest

from dbrownell_ParserLib.antlr.antlr_visitor_mixins import (
    AntlrVisitorMixinBase,
    InsignificantWhitespaceAntlrVisitorMixin,
    SignificantWhitespaceAntlrVisitorMixin,
)
from dbrownell_ParserLib.region import Location, Region


# ----------------------------------------------------------------------
# |
# |  Helper Classes
# |
# ----------------------------------------------------------------------
class ConcreteVisitorMixin(InsignificantWhitespaceAntlrVisitorMixin, antlr4.ParseTreeVisitor):
    """Concrete implementation for testing the base class functionality."""


# ----------------------------------------------------------------------
class ConcreteSignificantWhitespaceMixin(SignificantWhitespaceAntlrVisitorMixin, antlr4.ParseTreeVisitor):
    """Concrete implementation for testing SignificantWhitespaceAntlrVisitorMixin."""

    def __init__(
        self,
        filename: Path,
        on_progress_func: Callable[[int], None],
        *,
        is_included_file: bool,
        dedent_token: int,
        newline_token: int,
        newline_token_string: str,
    ) -> None:
        SignificantWhitespaceAntlrVisitorMixin.__init__(
            self, dedent_token, newline_token, newline_token_string
        )
        AntlrVisitorMixinBase.__init__(self, filename, on_progress_func, is_included_file=is_included_file)


# ----------------------------------------------------------------------
def CreateMockToken(
    line: int,
    column: int,
    text: str = "token",
    token_type: int = 0,
) -> MagicMock:
    """Create a mock ANTLR token."""
    token = MagicMock(spec=antlr4.Token)
    token.line = line
    token.column = column
    token.text = text
    token.type = token_type
    return token


# ----------------------------------------------------------------------
def CreateMockContext(
    start_line: int,
    start_column: int,
    stop_line: int,
    stop_column: int,
    stop_text: str = "token",
    stop_token_type: int = 0,
) -> MagicMock:
    """Create a mock parser rule context."""
    ctx = MagicMock(spec=antlr4.ParserRuleContext)
    ctx.start = CreateMockToken(start_line, start_column)
    ctx.stop = CreateMockToken(stop_line, stop_column, stop_text, stop_token_type)
    return ctx


# ----------------------------------------------------------------------
# |
# |  Tests
# |
# ----------------------------------------------------------------------
class TestAntlrVisitorMixinBase:
    # ----------------------------------------------------------------------
    class TestInit:
        # ----------------------------------------------------------------------
        def test_SetsFilename(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            assert mixin.filename == filename

        # ----------------------------------------------------------------------
        def test_SetsIsIncludedFileTrue(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=True)

            assert mixin.is_included_file is True

        # ----------------------------------------------------------------------
        def test_SetsIsIncludedFileFalse(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            assert mixin.is_included_file is False

    # ----------------------------------------------------------------------
    class TestGetChildren:
        # ----------------------------------------------------------------------
        def test_ReturnsEmptyListWhenNoChildren(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            ctx = MagicMock(spec=antlr4.ParserRuleContext)
            ctx.getChildCount.return_value = 0
            ctx.children = None

            result = mixin.GetChildren(ctx)

            assert result == []


# ----------------------------------------------------------------------
class TestInsignificantWhitespaceAntlrVisitorMixin:
    # ----------------------------------------------------------------------
    class TestCreateRegion:
        # ----------------------------------------------------------------------
        def test_CreatesRegionFromContext(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            # ANTLR columns are 0-based; Location columns are 1-based, so +1 is added
            ctx = CreateMockContext(1, 1, 1, 10, "hello")

            region = mixin.CreateRegion(ctx)

            assert region.filename == filename
            assert region.begin == Location(1, 2)  # 1 + 1 = 2
            assert region.end == Location(1, 16)  # 10 + 1 + len("hello") = 16

        # ----------------------------------------------------------------------
        def test_CreatesRegionSpanningMultipleLines(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            # ANTLR columns are 0-based; Location columns are 1-based, so +1 is added
            ctx = CreateMockContext(1, 5, 10, 20, "end")

            region = mixin.CreateRegion(ctx)

            assert region.filename == filename
            assert region.begin == Location(1, 6)  # 5 + 1 = 6
            assert region.end == Location(10, 22)  # 20 + 2 = 22 (no text length added for multi-line)

        # ----------------------------------------------------------------------
        def test_RaisesErrorWhenStartTokenIsNone(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            ctx = MagicMock(spec=antlr4.ParserRuleContext)
            ctx.start = None
            ctx.stop = CreateMockToken(1, 0)

            with pytest.raises(ValueError, match="Context does not have start or stop token"):
                mixin.CreateRegion(ctx)

        # ----------------------------------------------------------------------
        def test_RaisesErrorWhenStopTokenIsNone(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteVisitorMixin(filename, on_progress, is_included_file=False)

            ctx = MagicMock(spec=antlr4.ParserRuleContext)
            ctx.start = CreateMockToken(1, 0)
            ctx.stop = None

            with pytest.raises(ValueError, match="Context does not have start or stop token"):
                mixin.CreateRegion(ctx)


# ----------------------------------------------------------------------
class TestSignificantWhitespaceAntlrVisitorMixin:
    # ----------------------------------------------------------------------
    class TestCreateRegion:
        # ----------------------------------------------------------------------
        def test_WithDedentToken(self):
            filename = Path("test.txt")
            on_progress = MagicMock()
            dedent_token = 1

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=dedent_token,
                newline_token=2,
                newline_token_string="<NEWLINE>",
            )

            ctx = CreateMockContext(1, 0, 5, 4, "dedent", dedent_token)

            region = mixin.CreateRegion(ctx)

            assert region.begin == Location(1, 1)
            assert region.end == Location(5, 4)
            on_progress.assert_called_once_with(5)

        # ----------------------------------------------------------------------
        def test_WithNewlineTokenSameLine(self):
            filename = Path("test.txt")
            on_progress = MagicMock()
            newline_token = 2

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=1,
                newline_token=newline_token,
                newline_token_string="<NEWLINE>",
            )

            ctx = CreateMockContext(5, 0, 5, 10, "<NEWLINE>", newline_token)

            region = mixin.CreateRegion(ctx)

            assert region.begin == Location(5, 1)
            assert region.end == Location(5, 10)

        # ----------------------------------------------------------------------
        def test_WithNewlineTokenDifferentLineColumnNonZeroFallsBackToStartColumn(self):
            filename = Path("test.txt")
            on_progress = MagicMock()
            newline_token = 2

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=1,
                newline_token=newline_token,
                newline_token_string="<NEWLINE>",
            )

            # When stop.column != 0, uses start.column for stop_col
            ctx = CreateMockContext(1, 5, 3, 8, "<NEWLINE>", newline_token)

            region = mixin.CreateRegion(ctx)

            assert region.begin == Location(1, 6)
            assert region.end == Location(3, 5)

        # ----------------------------------------------------------------------
        def test_WithOtherTokenSingleLine(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=1,
                newline_token=2,
                newline_token_string="<NEWLINE>",
            )

            ctx = CreateMockContext(5, 10, 5, 15, "identifier", 99)

            region = mixin.CreateRegion(ctx)

            assert region.begin == Location(5, 11)
            assert region.end == Location(5, 25)

        # ----------------------------------------------------------------------
        def test_WithOtherTokenMultiLine(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=1,
                newline_token=2,
                newline_token_string="<NEWLINE>",
            )

            ctx = CreateMockContext(1, 0, 1, 0, "line1\nline2\nline3", 99)

            region = mixin.CreateRegion(ctx)

            assert region.begin == Location(1, 1)
            assert region.end == Location(3, 5)

        # ----------------------------------------------------------------------
        def test_WithNewlineTokenContainingActualNewline(self):
            filename = Path("test.txt")
            on_progress = MagicMock()
            newline_token = 2

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=1,
                newline_token=newline_token,
                newline_token_string="<NEWLINE>",
            )

            # When newline token text doesn't match newline_token_string exactly,
            # falls through to else branch: stop_col = len(last_line) + ctx.stop.column
            # "\n    " splits to ["", "    "], last_line = "    " (len 4)
            # stop_col = 4 + 10 = 14, stop_line = 1 + 1 = 2
            ctx = CreateMockContext(1, 0, 1, 10, "\n    ", newline_token)

            region = mixin.CreateRegion(ctx)

            assert region.begin == Location(1, 1)
            assert region.end == Location(2, 14)

        # ----------------------------------------------------------------------
        def test_CallsOnProgress(self):
            filename = Path("test.txt")
            on_progress = MagicMock()

            mixin = ConcreteSignificantWhitespaceMixin(
                filename,
                on_progress,
                is_included_file=False,
                dedent_token=1,
                newline_token=2,
                newline_token_string="<NEWLINE>",
            )

            ctx = CreateMockContext(1, 0, 10, 5, "token", 99)

            mixin.CreateRegion(ctx)

            on_progress.assert_called_once_with(10)
