"""Unit tests for Error and PythonError classes."""

import textwrap

from pathlib import Path

import pytest

from dbrownell_ParserLib.errors import Error, PythonError
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region


# ----------------------------------------------------------------------
class TestError:
    # ----------------------------------------------------------------------
    class TestConstruction:
        # ----------------------------------------------------------------------
        def test_SingleRegion(self):
            region = Region(
                filename=Path("test.txt"),
                begin=Location(line=1, column=1),
                end=Location(line=1, column=10),
            )

            error = Error(message="Test error", region_or_regions=region)

            assert error.message == "Test error"
            assert len(error.regions) == 1
            assert error.regions[0] == region

        # ----------------------------------------------------------------------
        def test_MultipleRegions(self):
            region1 = Region(
                filename=Path("test1.txt"),
                begin=Location(line=1, column=1),
                end=Location(line=1, column=10),
            )
            region2 = Region(
                filename=Path("test2.txt"),
                begin=Location(line=5, column=1),
                end=Location(line=5, column=20),
            )

            error = Error(message="Test error", region_or_regions=[region1, region2])

            assert error.message == "Test error"
            assert len(error.regions) == 2
            assert error.regions[0] == region1
            assert error.regions[1] == region2

        # ----------------------------------------------------------------------
        def test_EmptyRegionsListRaisesError(self):
            with pytest.raises(ValueError, match="At least one region must be provided"):
                Error(message="Test error", region_or_regions=[])

    # ----------------------------------------------------------------------
    class TestStr:
        # ----------------------------------------------------------------------
        def test_SingleLineMessageSingleRegion(self):
            region = Region(
                filename=Path("test.txt"),
                begin=Location(line=5, column=10),
                end=Location(line=5, column=10),
            )

            error = Error(message="Single line error", region_or_regions=region)

            assert str(error) == "Single line error (test.txt, Ln 5 Col 10)"

        # ----------------------------------------------------------------------
        def test_MultiLineMessage(self):
            region = Region(
                filename=Path("test.txt"),
                begin=Location(line=5, column=10),
                end=Location(line=5, column=10),
            )

            error = Error(message="Line one\nLine two", region_or_regions=region)

            expected = textwrap.dedent(
                """\
                Line one
                Line two

                    - test.txt, Ln 5 Col 10
                """
            )

            assert str(error) == expected

        # ----------------------------------------------------------------------
        def test_MultipleRegions(self):
            region1 = Region(
                filename=Path("test1.txt"),
                begin=Location(line=1, column=1),
                end=Location(line=1, column=1),
            )
            region2 = Region(
                filename=Path("test2.txt"),
                begin=Location(line=10, column=5),
                end=Location(line=10, column=5),
            )

            error = Error(message="Error message", region_or_regions=[region1, region2])

            expected = textwrap.dedent(
                """\
                Error message

                    - test1.txt, Ln 1 Col 1
                    - test2.txt, Ln 10 Col 5
                """
            )

            assert str(error) == expected

        # ----------------------------------------------------------------------
        def test_MessageWithTrailingWhitespace(self):
            region1 = Region(
                filename=Path("test.txt"),
                begin=Location(line=1, column=1),
                end=Location(line=1, column=1),
            )
            region2 = Region(
                filename=Path("test2.txt"),
                begin=Location(line=2, column=1),
                end=Location(line=2, column=1),
            )

            error = Error(message="Message with trailing space   \n", region_or_regions=[region1, region2])

            expected = textwrap.dedent(
                """\
                Message with trailing space

                    - test.txt, Ln 1 Col 1
                    - test2.txt, Ln 2 Col 1
                """
            )

            assert str(error) == expected


# ----------------------------------------------------------------------
class TestPythonError:
    # ----------------------------------------------------------------------
    class TestCreate:
        # ----------------------------------------------------------------------
        def test_CreateFromException(self):
            try:
                raise ValueError("Test exception message")
            except ValueError as ex:
                error = PythonError.Create(ex)

            expected_message = textwrap.dedent(
                """\
                Python Exception
                ----------------
                Test exception message
                """
            )

            assert error.message == expected_message
            assert error.ex is not None
            assert len(error.regions) > 0

        # ----------------------------------------------------------------------
        def test_ExceptionStored(self):
            original_exception = RuntimeError("Original error")

            try:
                raise original_exception
            except RuntimeError as ex:
                error = PythonError.Create(ex)

            assert error.ex is original_exception

        # ----------------------------------------------------------------------
        def test_MessageFormat(self):
            try:
                raise TypeError("Type mismatch")
            except TypeError as ex:
                error = PythonError.Create(ex)

            expected_message = textwrap.dedent(
                """\
                Python Exception
                ----------------
                Type mismatch
                """
            )

            assert error.message == expected_message

    # ----------------------------------------------------------------------
    class TestInheritance:
        # ----------------------------------------------------------------------
        def test_IsError(self):
            try:
                raise ValueError("Test")
            except ValueError as ex:
                error = PythonError.Create(ex)

            assert isinstance(error, Error)

        # ----------------------------------------------------------------------
        def test_HasStrMethod(self):
            region = Region(
                filename=Path("test.py"),
                begin=Location(line=10, column=1),
                end=Location(line=10, column=1),
            )
            ex = ValueError("Test exception")

            error = PythonError(
                message="Test message",
                region_or_regions=region,
                ex=ex,
            )

            assert str(error) == "Test message (test.py, Ln 10 Col 1)"
