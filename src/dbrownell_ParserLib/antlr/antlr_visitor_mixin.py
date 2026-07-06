# noqa: D100
import re

from typing import cast, TYPE_CHECKING

import antlr4

from dbrownell_ParserLib.region import Location, Region

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path


# ----------------------------------------------------------------------
class AntlrVisitorMixin:
    """Mixin that provides common visitation functionality; it is used along side ANTLR-generated visitors."""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        filename: Path,
        on_progress_func: Callable[[int], None],
        *,
        is_included_file: bool,
        parser_newline_string: str | None,
        indent_token_type: int | None,
        dedent_token_type: int | None,
    ) -> None:
        self.filename = filename
        self.is_included_file = is_included_file

        # Protected data
        self._on_progress_func = on_progress_func
        self._parser_newline_string = parser_newline_string
        self._indent_token_type = indent_token_type
        self._dedent_token_type = dedent_token_type
        self._stack: list[object] = []

        # Private data
        self._current_line: int = 0
        self._stop_token_regex = re.compile(r"^\r?\n[ \t]*$")

    # ----------------------------------------------------------------------
    def CreateRegion(
        self,
        ctx: antlr4.TerminalNode | antlr4.ParserRuleContext,
    ) -> Region:
        """Create a `Region` from the given context."""

        if isinstance(ctx, antlr4.TerminalNode):
            start_token = cast(antlr4.Token, ctx.symbol)  # ty: ignore[unresolved-attribute]
            end_location = self._CreateEndLocation(start_token)
        else:
            start_token = ctx.start
            stop_token = ctx.stop

            assert ctx.children is not None
            assert start_token is not None
            assert stop_token is not None

            end_location: Location | None = None

            if self._parser_newline_string is not None:
                if self._IsStopToken(stop_token):
                    assert len(ctx.children) == 2, ctx.children  # noqa: PLR2004
                    end_location = self._CreateEndLocation(start_token)
                elif stop_token.type == self._dedent_token_type:
                    end_location = Location(stop_token.line, stop_token.column + 1)

            if end_location is None:
                end_location = self._CreateEndLocation(stop_token)

        assert start_token.line is not None
        assert start_token.column is not None

        region = Region(
            self.filename,
            Location(start_token.line, start_token.column + 1),
            end_location,
        )

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
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _CreateEndLocation(token: antlr4.Token) -> Location:
        assert token.text is not None
        assert token.line is not None
        assert token.column is not None

        return CreateEndLocation(token.text, token.line, token.column + 1)

    # ----------------------------------------------------------------------
    def _IsStopToken(self, token: antlr4.Token) -> bool:
        assert token.text is not None

        return (
            token.text == self._parser_newline_string or self._stop_token_regex.match(token.text) is not None
        )


# ----------------------------------------------------------------------
def CreateEndLocation(text: str, line: int, column: int) -> Location:
    """Create a `Location` based on the text and current line and column."""

    # Note that this function will not be invoked outside of this file; it is implemented as a
    # function so that it can be exercised by automated tests.

    assert line > 0, line
    assert column > 0, column

    lines = text.splitlines()

    last_nonblank_line = None

    for line_index, line_text in enumerate(lines):
        if line_text.strip():
            last_nonblank_line = line_index

    assert last_nonblank_line is not None

    if last_nonblank_line == 0:
        return Location(line, column + len(lines[0]))

    return Location(line + last_nonblank_line, len(lines[last_nonblank_line]) + 1)
