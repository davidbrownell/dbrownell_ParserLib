"""Unit tests for multiline_strings module."""

import textwrap

from pathlib import Path

import pytest

from dbrownell_ParserLib.errors import ErrorException
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.multiline_strings import ExtractMultilineString, MisalignedMultilineStringError
from dbrownell_ParserLib.region import Region


# ----------------------------------------------------------------------
class TestMisalignedMultilineStringError:
    # ----------------------------------------------------------------------
    def test_ErrorMessage(self):
        region = Region(Path("test.txt"), Location(1, 1), Location(1, 1))
        error = MisalignedMultilineStringError.Create(region)

        assert (
            error.message
            == "All lines in a multiline string must be vertically aligned with the opening token."
        )

    # ----------------------------------------------------------------------
    def test_CreateAsException(self):
        region = Region(Path("test.txt"), Location(5, 10), Location(5, 10))
        exception = MisalignedMultilineStringError.CreateAsException(region)

        assert isinstance(exception, ErrorException)


# ----------------------------------------------------------------------
class TestExtractMultilineString:
    # ----------------------------------------------------------------------
    class TestValidStrings:
        # ----------------------------------------------------------------------
        def test_SimpleSingleLine(self):
            # Column 1 opening requires blank line before closing token
            content = textwrap.dedent(
                '''\
                """
                Hello
                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(4, 3))

            result = ExtractMultilineString(content, region)

            assert result == "Hello"

        # ----------------------------------------------------------------------
        def test_MultipleLines(self):
            # Column 1 opening requires blank line before closing token
            content = textwrap.dedent(
                '''\
                """
                Line one
                Line two
                Line three
                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(6, 3))

            result = ExtractMultilineString(content, region)

            assert result == "Line one\nLine two\nLine three"

        # ----------------------------------------------------------------------
        def test_IndentedOpeningToken(self):
            content = '"""\n    Line content\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(3, 8))

            result = ExtractMultilineString(content, region)

            assert result == "Line content"

        # ----------------------------------------------------------------------
        def test_IndentedMultipleLines(self):
            content = '"""\n    First line\n    Second line\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(4, 7))

            result = ExtractMultilineString(content, region)

            assert result == "First line\nSecond line"

        # ----------------------------------------------------------------------
        def test_IndentedMultipleLinesWithPrefixedEmpty(self):
            content = '"""\n    First line\n    \n    Second line\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(4, 7))

            result = ExtractMultilineString(content, region)

            assert result == "First line\n\nSecond line"

        # ----------------------------------------------------------------------
        def test_IndentedMultipleLinesWithBlankEmpty(self):
            content = '"""\n    First line\n\n    Second line\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(4, 7))

            result = ExtractMultilineString(content, region)

            assert result == "First line\n\nSecond line"

        # ----------------------------------------------------------------------
        def test_NoContent(self):
            content = textwrap.dedent(
                '''\
                """
                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(5, 3))

            result = ExtractMultilineString(content, region)

            assert result == ""

        # ----------------------------------------------------------------------
        def test_NoContentIndented(self):
            content = '"""\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(5, 8))

            result = ExtractMultilineString(content, region)

            assert result == ""

        # ----------------------------------------------------------------------
        def test_EmptyContentLines1(self):
            # Column 1: blank lines within content (not at prefix column)
            content = textwrap.dedent(
                '''\
                """

                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(5, 3))

            result = ExtractMultilineString(content, region)

            assert result == "\n"

        # ----------------------------------------------------------------------
        def test_EmptyContentLines2(self):
            # Column 1: blank lines within content (not at prefix column)
            content = textwrap.dedent(
                '''\
                """


                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(5, 3))

            result = ExtractMultilineString(content, region)

            assert result == "\n\n"

        # ----------------------------------------------------------------------
        def test_EmptyContentLines3(self):
            # Column 1: blank lines within content (not at prefix column)
            content = '"""\n\n\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(5, 7))

            result = ExtractMultilineString(content, region)

            assert result == "\n\n"

        # ----------------------------------------------------------------------
        def test_EmptyContentLines4(self):
            # Column 1: blank lines within content (not at prefix column)
            content = '"""\n    \n\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(5, 7))

            result = ExtractMultilineString(content, region)

            assert result == "\n\n"

        # ----------------------------------------------------------------------
        def test_CustomTokens(self):
            # Column 1 with single quote tokens
            content = textwrap.dedent(
                """\
                '''
                Content here
                '''"""
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(4, 3))

            result = ExtractMultilineString(
                content,
                region,
                opening_token="'''",
                closing_token="'''",
            )

            assert result == "Content here"

        # ----------------------------------------------------------------------
        def test_EscapedClosingToken(self):
            # Column 1 with escaped closing token in content
            content = textwrap.dedent(
                '''\
                """
                Text with \\"\\"\\"
                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(4, 3))

            result = ExtractMultilineString(content, region)

            assert result == 'Text with """'

        # ----------------------------------------------------------------------
        def test_MixedContentWithBlankLines(self):
            # Column 1: blank lines within content have prefix 1, matching column 1
            content = textwrap.dedent(
                '''\
                """
                First

                Third
                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(6, 3))

            result = ExtractMultilineString(content, region)

            assert result == "First\n\nThird"

        # ----------------------------------------------------------------------
        def test_IndentedContentWithIndentedBlankLine(self):
            content = '"""\n    First\n    \n    Third\n"""'
            region = Region(Path("test.txt"), Location(1, 1), Location(5, 4))

            result = ExtractMultilineString(content, region)

            assert result == "    First\n\n    Third"

        # ----------------------------------------------------------------------
        def test_IndentedContentWithIndentedBlankLineWithColumnOffset(self):
            content = '"""\n        First\n        \n        Third\n    """'
            region = Region(Path("test.txt"), Location(1, 5), Location(5, 7))

            result = ExtractMultilineString(content, region)

            assert result == "    First\n\n    Third"

        # ----------------------------------------------------------------------
        def test_TabPreservedAtColumnOne(self):
            # Column 1 opening: tabs in content are preserved since no stripping occurs
            content = '"""\n\tTabbed line\n"""'
            region = Region(Path("test.txt"), Location(1, 1), Location(3, 3))

            result = ExtractMultilineString(content, region)

            assert result == "\tTabbed line"

        # ----------------------------------------------------------------------
        def test_MultipleTabsPreservedAtColumnOne(self):
            # Column 1 opening: multiple tabs preserved
            content = '"""\n\t\tDouble tabbed\n"""'
            region = Region(Path("test.txt"), Location(1, 1), Location(3, 3))

            result = ExtractMultilineString(content, region)

            assert result == "\t\tDouble tabbed"

        # ----------------------------------------------------------------------
        def test_TabClosingToken(self):
            # Tab-indented closing token aligns with column 5 (1 tab = 4 spaces)
            content = '"""\n    Content line\n\t"""'
            region = Region(Path("test.txt"), Location(1, 5), Location(3, 7))

            result = ExtractMultilineString(content, region)

            assert result == "Content line"

        # ----------------------------------------------------------------------
        def test_MixedTabsAndSpacesPreserved(self):
            # Column 1: mixed tabs and spaces in content are preserved
            content = '"""\n\t    Mixed indentation\n"""'
            region = Region(Path("test.txt"), Location(1, 1), Location(3, 3))

            result = ExtractMultilineString(content, region)

            assert result == "\t    Mixed indentation"

        # ----------------------------------------------------------------------
        def test_MixedTabsAndSpacesPreservedIndented(self):
            # Column 1: mixed tabs and spaces in content are preserved
            content = '"""\n\t\t    Mixed indentation\n\t"""'
            region = Region(Path("test.txt"), Location(1, 5), Location(3, 8))

            result = ExtractMultilineString(content, region)

            assert result == "\t    Mixed indentation"

        # ----------------------------------------------------------------------
        def test_TabInBlankLineAtColumnOne(self):
            # Column 1 with tab-only blank line in content
            content = '"""\nFirst\n\t\nThird\n"""'
            region = Region(Path("test.txt"), Location(1, 1), Location(5, 3))

            result = ExtractMultilineString(content, region)

            assert result == "First\n\nThird"

    # ----------------------------------------------------------------------
    class TestErrors:
        # ----------------------------------------------------------------------
        def test_ContentImmediatelyAfterOpeningToken(self):
            content = textwrap.dedent(
                '''\
                """Content

                """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(3, 3))

            with pytest.raises(ErrorException) as exc_info:
                ExtractMultilineString(content, region)

            error = exc_info.value.error
            assert (
                error.message
                == "All lines in a multiline string must be vertically aligned with the opening token."
            )
            assert error.regions[0].begin.line == 1
            assert error.regions[0].begin.column == 4

        # ----------------------------------------------------------------------
        def test_MisalignedClosingToken1(self):
            # Column 1 opening, but closing has 2 spaces (prefix = 3)
            # Error reports line = opening_line + len(content_lines) + 1
            content = textwrap.dedent(
                '''\
                """
                Line content
                  """'''
            )
            region = Region(Path("test.txt"), Location(1, 1), Location(3, 5))

            with pytest.raises(ErrorException) as exc_info:
                ExtractMultilineString(content, region)

            error = exc_info.value.error
            assert (
                error.message
                == "All lines in a multiline string must be vertically aligned with the opening token."
            )
            assert error.regions[0].begin.line == 3
            assert error.regions[0].begin.column == 3

        # ----------------------------------------------------------------------
        def test_MisalignedClosingToken2(self):
            content = '"""\n    Line content\n  """'

            region = Region(Path("test.txt"), Location(1, 5), Location(3, 5))

            with pytest.raises(ErrorException) as exc_info:
                ExtractMultilineString(content, region)

            error = exc_info.value.error
            assert (
                error.message
                == "All lines in a multiline string must be vertically aligned with the opening token."
            )
            assert error.regions[0].begin.line == 3
            assert error.regions[0].begin.column == 3

        # ----------------------------------------------------------------------
        def test_IndentedOpeningWithMisalignedContent(self):
            # Column 5 opening (4 spaces), but content has only 2 spaces
            content = textwrap.dedent(
                '''\
                """
                  Wrong indent
                    """'''
            )
            region = Region(Path("test.txt"), Location(1, 5), Location(3, 7))

            with pytest.raises(ErrorException) as exc_info:
                ExtractMultilineString(content, region)

            error = exc_info.value.error
            assert error.regions[0].begin.line == 2
            assert error.regions[0].begin.column == 3

        # ----------------------------------------------------------------------
        def test_IndentedOpeningWithMisalignedClosing(self):
            # Column 5 opening (4 spaces), but closing has only 2 spaces
            # Error reports line = opening_line + len(content_lines) + 1
            content = textwrap.dedent(
                '''\
                """
                    Content
                  """'''
            )
            region = Region(Path("test.txt"), Location(1, 5), Location(3, 5))

            with pytest.raises(ErrorException) as exc_info:
                ExtractMultilineString(content, region)

            error = exc_info.value.error
            assert error.regions[0].begin.line == 3
            assert error.regions[0].begin.column == 3

        # ----------------------------------------------------------------------
        def test_TabMisalignedClosingToken(self):
            # Opening at column 1, but closing has 1 tab (column 5)
            content = '"""\nContent\n\t"""'
            region = Region(Path("test.txt"), Location(1, 1), Location(3, 5))

            with pytest.raises(ErrorException) as exc_info:
                ExtractMultilineString(content, region)

            error = exc_info.value.error
            assert (
                error.message
                == "All lines in a multiline string must be vertically aligned with the opening token."
            )
            assert error.regions[0].begin.line == 3
            assert error.regions[0].begin.column == 5

        # ----------------------------------------------------------------------
        def test_SpaceVsTabMisalignment(self):
            # Opening at column 5 (4 spaces), but closing has 1 tab
            # Both visually column 5, but _CalcPrefixColumn with max_column=None
            # for '\t' returns 5, which matches column 5, so this should PASS
            # This test verifies that visual alignment works for closing tokens
            content = '"""\n    Content\n\t"""'
            region = Region(Path("test.txt"), Location(1, 5), Location(3, 7))

            # This should NOT raise - tab visually aligns with 4 spaces
            result = ExtractMultilineString(content, region)

            assert result == "Content"
