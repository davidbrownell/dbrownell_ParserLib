"""Various ANTLR visitor mixins that can be used to add functionality to the generated visitor classes."""

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
    @abstractmethod
    def CreateRegion(
        self,
        ctx: antlr4.ParserRuleContext,
    ) -> Region:
        """Create a `Region` from the given context."""

        raise NotImplementedError()  # pragma: no cover

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
class InsignificantWhitespaceAntlrVisitorMixin(AntlrVisitorMixinBase):
    """Mixin that adds functionality used for grammars that ignore insignificant whitespace."""

    # ----------------------------------------------------------------------
    @override
    def CreateRegion(
        self,
        ctx: antlr4.ParserRuleContext,
    ) -> Region:
        """Create a `Region` from the given context."""

        start_token = ctx.start
        stop_token = ctx.stop

        if start_token is None or stop_token is None:
            msg = "Context does not have start or stop token"
            raise ValueError(msg)

        return Region(
            self.filename,
            Location(start_token.line, start_token.column),
            Location(stop_token.line, stop_token.column + len(stop_token.text)),
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

    # ----------------------------------------------------------------------
    @override
    def CreateRegion(
        self,
        ctx: antlr4.ParserRuleContext,
    ) -> Region:
        assert isinstance(ctx.start, antlr4.Token), ctx.start
        assert isinstance(ctx.stop, antlr4.Token), ctx.stop

        if ctx.stop.type == self._dedent_token:
            stop_line = ctx.stop.line
            stop_col = ctx.stop.column

        elif ctx.stop.type == self._newline_token and ctx.stop.text == self._newline_token_string:
            if ctx.stop.line == ctx.start.line:
                # This is the scenario where the statement is followed by a dedent followed by another
                # statement. We don't want the range of this item to overlap with the range of the
                # next item, so use the values as they are, even though it means that a statement
                # that terminates with a newline will not have the newline here.
                stop_line = ctx.stop.line
                stop_col = ctx.stop.column
            else:
                stop_line = ctx.stop.line
                stop_col = ctx.stop.column if ctx.stop.column == 0 else ctx.start.column

        else:
            stop_line = ctx.stop.line

            content = ctx.stop.text
            lines = content.split("\n")

            if ctx.stop.type == self._newline_token:
                assert content.startswith("\n"), content
                assert len(lines) == 2, lines  # noqa: PLR2004

            stop_col = len(lines[-1])

            if stop_line == ctx.stop.line:
                stop_col += ctx.stop.column

            stop_line += len(lines) - 1

        self._OnProgress(stop_line)

        return Region(
            self.filename,
            Location(ctx.start.line, ctx.start.column + 1),
            Location(stop_line, stop_col),
        )
