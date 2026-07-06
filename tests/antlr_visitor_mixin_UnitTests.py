"""Unit tests for antlr_visitor_mixin.py."""

from pathlib import Path
from typing import cast

import antlr4

from antlr4.Token import CommonToken
from antlr4.tree.Tree import TerminalNodeImpl

from dbrownell_ParserLib.antlr.antlr_visitor_mixin import AntlrVisitorMixin, CreateEndLocation
from dbrownell_ParserLib.region import Location, Region


# ----------------------------------------------------------------------
_test_filename = Path("test_file.txt")


# ----------------------------------------------------------------------
class _GroupContext(antlr4.ParserRuleContext):
    """Context that dispatches to a custom visitation method, simulating ANTLR-generated contexts."""

    def accept(self, visitor: antlr4.ParseTreeVisitor) -> object:
        return cast("_Visitor", visitor).VisitGroup(self)


# ----------------------------------------------------------------------
class _Visitor(AntlrVisitorMixin, antlr4.ParseTreeVisitor):
    def visitTerminal(self, node: TerminalNodeImpl) -> None:
        self._stack.append(node.symbol.text)

    def VisitGroup(self, ctx: _GroupContext) -> None:
        self._stack.append(tuple(self.GetChildren(ctx)))


# ----------------------------------------------------------------------
def _CreateVisitor(
    on_progress_func=None,
    *,
    parser_newline_string: str | None = None,
    indent_token_type: int | None = None,
    dedent_token_type: int | None = None,
) -> _Visitor:
    return _Visitor(
        _test_filename,
        on_progress_func if on_progress_func is not None else lambda _: None,
        is_included_file=False,
        parser_newline_string=parser_newline_string,
        indent_token_type=indent_token_type,
        dedent_token_type=dedent_token_type,
    )


# ----------------------------------------------------------------------
def _CreateToken(
    text: str,
    line: int,
    column: int,
    token_type: int = 1,
) -> antlr4.Token:
    token = CommonToken(type=token_type)

    token.text = text
    token.line = line
    token.column = column

    return token


# ----------------------------------------------------------------------
def _CreateTerminalNode(
    text: str,
    line: int,
    column: int,
) -> antlr4.TerminalNode:
    return TerminalNodeImpl(_CreateToken(text, line, column))


# ----------------------------------------------------------------------
def _CreateContext(
    start_token: antlr4.Token,
    stop_token: antlr4.Token,
    num_children: int = 1,
) -> antlr4.ParserRuleContext:
    ctx = antlr4.ParserRuleContext()

    ctx.start = start_token
    ctx.stop = stop_token
    ctx.children = [None] * num_children

    return ctx


# ----------------------------------------------------------------------
class TestConstruction:
    # ----------------------------------------------------------------------
    def test_PublicAttributes(self):
        visitor = _Visitor(
            _test_filename,
            lambda _: None,
            is_included_file=True,
            parser_newline_string=None,
            indent_token_type=None,
            dedent_token_type=None,
        )

        assert visitor.filename == _test_filename
        assert visitor.is_included_file is True


# ----------------------------------------------------------------------
class TestCreateRegion:
    # ----------------------------------------------------------------------
    class TestTerminalNode:
        # ----------------------------------------------------------------------
        def test_SingleLineToken(self):
            visitor = _CreateVisitor()

            region = visitor.CreateRegion(_CreateTerminalNode("value", 2, 4))

            assert region == Region(_test_filename, Location(2, 5), Location(2, 10))

        # ----------------------------------------------------------------------
        def test_MultilineToken(self):
            visitor = _CreateVisitor()

            region = visitor.CreateRegion(_CreateTerminalNode("abc\ndefg", 1, 0))

            assert region == Region(_test_filename, Location(1, 1), Location(2, 5))

        # ----------------------------------------------------------------------
        def test_TokenWithTrailingNewline(self):
            visitor = _CreateVisitor()

            region = visitor.CreateRegion(_CreateTerminalNode("abc\n", 3, 2))

            assert region == Region(_test_filename, Location(3, 3), Location(3, 6))

        # ----------------------------------------------------------------------
        def test_TerminalNodeIgnoresNewlineString(self):
            # Terminal nodes are processed the same way regardless of the newline string.
            visitor = _CreateVisitor(parser_newline_string="newLine")

            region = visitor.CreateRegion(_CreateTerminalNode("abc", 1, 0))

            assert region == Region(_test_filename, Location(1, 1), Location(1, 4))

    # ----------------------------------------------------------------------
    class TestContextWithoutNewlineString:
        # ----------------------------------------------------------------------
        def test_SingleLineStopToken(self):
            visitor = _CreateVisitor()

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("abc", 1, 0),
                    _CreateToken("def", 1, 8),
                ),
            )

            assert region == Region(_test_filename, Location(1, 1), Location(1, 12))

        # ----------------------------------------------------------------------
        def test_MultilineStopToken(self):
            visitor = _CreateVisitor()

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("abc", 1, 0),
                    _CreateToken("xy\nz", 3, 0),
                ),
            )

            assert region == Region(_test_filename, Location(1, 1), Location(4, 2))

        # ----------------------------------------------------------------------
        def test_StopTokenWithTrailingBlankLines(self):
            visitor = _CreateVisitor()

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("abc", 2, 4),
                    _CreateToken("def\n\n", 5, 0),
                ),
            )

            assert region == Region(_test_filename, Location(2, 5), Location(5, 4))

    # ----------------------------------------------------------------------
    class TestContextWithNewlineString:
        # ----------------------------------------------------------------------
        def test_StopTokenMatchesNewlineString(self):
            visitor = _CreateVisitor(parser_newline_string="newLine")

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("abc", 1, 0),
                    _CreateToken("newLine", 1, 3),
                    num_children=2,
                ),
            )

            # The end location is based on the start token
            assert region == Region(_test_filename, Location(1, 1), Location(1, 4))

        # ----------------------------------------------------------------------
        def test_StopTokenMatchesWhitespaceRegex(self):
            visitor = _CreateVisitor(parser_newline_string="newLine")

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("value", 2, 4),
                    _CreateToken("\n    ", 2, 9),
                    num_children=2,
                ),
            )

            assert region == Region(_test_filename, Location(2, 5), Location(2, 10))

        # ----------------------------------------------------------------------
        def test_StopTokenMatchesCarriageReturnRegex(self):
            visitor = _CreateVisitor(parser_newline_string="newLine")

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("value", 2, 4),
                    _CreateToken("\r\n\t", 2, 9),
                    num_children=2,
                ),
            )

            assert region == Region(_test_filename, Location(2, 5), Location(2, 10))

        # ----------------------------------------------------------------------
        def test_DedentStopToken(self):
            visitor = _CreateVisitor(
                parser_newline_string="newLine",
                indent_token_type=41,
                dedent_token_type=42,
            )

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("abc", 1, 0),
                    _CreateToken("dedent", 5, 0, token_type=42),
                ),
            )

            # The end location is the start of the dedent token
            assert region == Region(_test_filename, Location(1, 1), Location(5, 1))

        # ----------------------------------------------------------------------
        def test_RegularStopToken(self):
            visitor = _CreateVisitor(parser_newline_string="newLine")

            region = visitor.CreateRegion(
                _CreateContext(
                    _CreateToken("abc", 1, 0),
                    _CreateToken("def", 2, 4),
                ),
            )

            assert region == Region(_test_filename, Location(1, 1), Location(2, 8))

    # ----------------------------------------------------------------------
    class TestProgressReporting:
        # ----------------------------------------------------------------------
        def test_ReportsEndLine(self):
            progress: list[int] = []

            visitor = _CreateVisitor(progress.append)

            visitor.CreateRegion(_CreateTerminalNode("abc\ndef", 2, 0))

            assert progress == [3]

        # ----------------------------------------------------------------------
        def test_ReportsOnlyIncreasingLines(self):
            progress: list[int] = []

            visitor = _CreateVisitor(progress.append)

            visitor.CreateRegion(_CreateTerminalNode("abc", 2, 0))
            visitor.CreateRegion(_CreateTerminalNode("def", 2, 4))
            visitor.CreateRegion(_CreateTerminalNode("ghi", 1, 0))
            visitor.CreateRegion(_CreateTerminalNode("jkl", 5, 0))

            assert progress == [2, 5]


# ----------------------------------------------------------------------
class TestGetChildren:
    # ----------------------------------------------------------------------
    def test_ReturnsVisitedChildren(self):
        visitor = _CreateVisitor()

        ctx = antlr4.ParserRuleContext()
        ctx.children = [
            _CreateTerminalNode("a", 1, 0),
            _CreateTerminalNode("b", 1, 2),
        ]

        assert visitor.GetChildren(ctx) == ["a", "b"]

    # ----------------------------------------------------------------------
    def test_EmptyChildren(self):
        visitor = _CreateVisitor()

        ctx = antlr4.ParserRuleContext()
        ctx.children = []

        assert visitor.GetChildren(ctx) == []

    # ----------------------------------------------------------------------
    def test_NestedContextsPreserveOuterResults(self):
        visitor = _CreateVisitor()

        group = _GroupContext()
        group.children = [
            _CreateTerminalNode("b", 1, 2),
            _CreateTerminalNode("c", 1, 4),
        ]

        ctx = antlr4.ParserRuleContext()
        ctx.children = [
            _CreateTerminalNode("a", 1, 0),
            group,
        ]

        # The result visited before the group remains available to the outer
        # invocation after the nested invocation completes.
        assert visitor.GetChildren(ctx) == ["a", ("b", "c")]

    # ----------------------------------------------------------------------
    def test_ConsecutiveInvocations(self):
        visitor = _CreateVisitor()

        ctx1 = antlr4.ParserRuleContext()
        ctx1.children = [_CreateTerminalNode("a", 1, 0)]

        ctx2 = antlr4.ParserRuleContext()
        ctx2.children = [_CreateTerminalNode("b", 2, 0)]

        # Results from the first invocation are consumed and do not leak into the second.
        assert visitor.GetChildren(ctx1) == ["a"]
        assert visitor.GetChildren(ctx2) == ["b"]


# ----------------------------------------------------------------------
class TestCreateEndLocation:
    # ----------------------------------------------------------------------
    class TestSingleLine:
        # ----------------------------------------------------------------------
        def test_AtOrigin(self):
            assert CreateEndLocation("test", 1, 1) == Location(1, 5)

        # ----------------------------------------------------------------------
        def test_WithLineAndColumnOffsets(self):
            assert CreateEndLocation("test", 4, 5) == Location(4, 9)

        # ----------------------------------------------------------------------
        def test_WithTrailingNewline(self):
            assert CreateEndLocation("test\n", 1, 1) == Location(1, 5)

        # ----------------------------------------------------------------------
        def test_WithTrailingBlankLine(self):
            assert CreateEndLocation("test\n\n", 1, 1) == Location(1, 5)

        # ----------------------------------------------------------------------
        def test_WithTrailingBlankLineAndOffsets(self):
            assert CreateEndLocation("test\n\n", 4, 5) == Location(4, 9)

        # ----------------------------------------------------------------------
        def test_WithTrailingWhitespaceOnlyLine(self):
            assert CreateEndLocation("test\n   \t\n", 1, 1) == Location(1, 5)

    # ----------------------------------------------------------------------
    class TestMultipleLines:
        # ----------------------------------------------------------------------
        def test_LastLineNonBlank(self):
            assert CreateEndLocation("abc\ndefg", 1, 1) == Location(2, 5)

        # ----------------------------------------------------------------------
        def test_WithTrailingBlankLines(self):
            assert CreateEndLocation("test\n\ntwo\n\n", 1, 1) == Location(3, 4)

        # ----------------------------------------------------------------------
        def test_WithLineAndColumnOffsets(self):
            # The line offset applies, but the column offset does not because the
            # last non-blank line is not the first line.
            assert CreateEndLocation("test\n\ntwo\n\n", 5, 10) == Location(7, 4)

        # ----------------------------------------------------------------------
        def test_WithWhitespaceOnlyLineBetweenContent(self):
            assert CreateEndLocation("test\n   \ntwo", 1, 1) == Location(3, 4)

        # ----------------------------------------------------------------------
        def test_WithCarriageReturns(self):
            assert CreateEndLocation("test\r\n\r\ntwo\r\n", 1, 1) == Location(3, 4)

        # ----------------------------------------------------------------------
        def test_WithTabs(self):
            # The tab-only line is blank; each tab in the last non-blank line counts
            # as a single column.
            assert CreateEndLocation("test\n\t\t\ntwo\tthree\n", 1, 1) == Location(3, 10)
