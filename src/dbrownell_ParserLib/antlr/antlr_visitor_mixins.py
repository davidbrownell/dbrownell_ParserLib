"""Various ANTLR visitor mixins that can be used to add functionality to the generated visitor classes."""

import re

from abc import ABC, abstractmethod
from typing import cast, override, TYPE_CHECKING

import antlr4

from dbrownell_ParserLib.region import Location, Region

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


# ----------------------------------------------------------------------
class AntlrVisitorMixinBase(ABC):
    """Base class for visitor mixins. This class is not meant to be used directly, but rather to be inherited by other mixin classes."""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        filename: Path,
        on_progress_func: Callable[[int], None],
        *,
        is_included_file: bool,
    ) -> None:
        self.filename = filename
        self.is_included_file = is_included_file

        # Protected data
        self._on_progress_func = on_progress_func
        self._stack: list[object] = []

        # Private data
        self._current_line: int = 0

    # ----------------------------------------------------------------------
    def CreateRegion(
        self,
        ctx: antlr4.TerminalNode | antlr4.ParserRuleContext,
    ) -> Region:
        """Create a `Region` from the given context."""

        if isinstance(ctx, antlr4.TerminalNode):
            token = cast(antlr4.Token, ctx.symbol)  # ty: ignore[unresolved-attribute]

            assert token.column is not None

            start_line = token.line
            start_col = token.column + 1
            end_line = token.line
            end_col = token.column + 1 + len(token.text)

            assert start_line is not None
            assert end_line is not None

            region = Region(
                self.filename,
                Location(start_line, start_col),
                Location(end_line, end_col),
            )
        else:
            region = self._CreateRegionFromRule(ctx)

        self._OnProgress(region.end.line)

        return region

    # ----------------------------------------------------------------------
    def GetChildren(self, ctx: antlr4.ParserRuleContext) -> list[object]:
        """Return the results of visiting the children of the given context."""

        prev_num_stack_items = len(self._stack)

        cast(antlr4.ParseTreeVisitor, self).visitChildren(ctx)

        results = self._stack[prev_num_stack_items:]
        del self._stack[prev_num_stack_items:]

        return results

    # ----------------------------------------------------------------------
    # |  Protected Methods
    def _OnProgress(self, end_line: int) -> None:
        if end_line > self._current_line:
            self._current_line = end_line
            self._on_progress_func(end_line)

    # ----------------------------------------------------------------------
    @abstractmethod
    def _CreateRegionFromRule(self, ctx: antlr4.ParserRuleContext) -> Region: ...


# ----------------------------------------------------------------------
class InsignificantWhitespaceAntlrVisitorMixin(AntlrVisitorMixinBase):
    """Mixin that adds functionality used for grammars that ignore insignificant whitespace."""

    # ----------------------------------------------------------------------
    def _CreateRegionFromRule(self, ctx: antlr4.ParserRuleContext) -> Region:
        start_token = ctx.start
        stop_token = ctx.stop

        if start_token is None or stop_token is None:
            msg = "Context does not have start or stop token"
            raise ValueError(msg)

        start_line = start_token.line
        start_col = start_token.column + 1
        end_line = stop_token.line
        end_col = stop_token.column + 1 + len(stop_token.text)

        assert start_line is not None
        assert end_line is not None

        return Region(
            self.filename,
            Location(start_line, start_col),
            Location(end_line, end_col),
        )


# ----------------------------------------------------------------------
class SignificantWhitespaceAntlrVisitorMixin(AntlrVisitorMixinBase):
    """Mixin that adds functionality used for grammars that treat whitespace as significant."""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        dedent_token: int,
        newline_token: int,
        newline_token_string: str,
    ) -> None:
        self._dedent_token = dedent_token
        self._newline_token = newline_token
        self._newline_token_string = newline_token_string

        self._newline_indent_regex = re.compile(r"^\r?\n[ \t]*$")

    # ----------------------------------------------------------------------
    @override
    def _CreateRegionFromRule(
        self,
        ctx: antlr4.ParserRuleContext,
    ) -> Region:
        assert isinstance(ctx.start, antlr4.Token), ctx.start
        assert isinstance(ctx.stop, antlr4.Token), ctx.stop

        if ctx.stop.text == self._newline_token_string or self._newline_indent_regex.match(ctx.stop.text):
            assert ctx.stop.line == ctx.start.line or ctx.stop.line - 1 == ctx.start.line, (
                ctx.start.line,
                ctx.stop.line,
            )

            stop_line = ctx.start.line
            stop_column = ctx.start.column + 1 + len(ctx.start.text)

            return Region(
                self.filename,
                Location(ctx.start.line, ctx.start.column + 1),
                Location(stop_line, stop_column),
            )

        return Region(
            self.filename,
            Location(ctx.start.line, ctx.start.column + 1),
            Location(ctx.stop.line, ctx.stop.column + 1),
        )
