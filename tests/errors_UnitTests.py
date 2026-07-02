"""Unit tests for Error and PythonError classes."""

import textwrap

from pathlib import Path

import pytest

from enum import Enum

from dbrownell_ParserLib.errors import CreateErrorType, Error, ErrorException, PythonError
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
    class TestCreateAsException:
        # ----------------------------------------------------------------------
        def test_ReturnsErrorException(self):
            region = Region(
                filename=Path("test.txt"),
                begin=Location(line=1, column=1),
                end=Location(line=1, column=10),
            )

            exception = Error.CreateAsException(message="Test error", region_or_regions=region)

            assert isinstance(exception, ErrorException)
            assert isinstance(exception.error, Error)
            assert exception.error.message == "Test error"
            assert exception.error.regions[0] == region

        # ----------------------------------------------------------------------
        def test_CanBeRaised(self):
            region = Region(
                filename=Path("test.txt"),
                begin=Location(line=5, column=1),
                end=Location(line=5, column=10),
            )

            with pytest.raises(ErrorException) as exc_info:
                raise Error.CreateAsException(message="Raised error", region_or_regions=region)

            assert exc_info.value.error.message == "Raised error"

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


# ----------------------------------------------------------------------
class TestErrorException:
    # ----------------------------------------------------------------------
    def test_Construction(self):
        error = Error(
            "Test error message",
            Region(Path("test.txt"), Location(1, 1), Location(1, 10)),
        )

        exception = ErrorException(error)

        assert exception.error is error
        assert str(exception) == str(error)

    # ----------------------------------------------------------------------
    def test_IsException(self):
        error = Error(
            "Test error",
            Region(Path("test.txt"), Location(1, 1), Location(1, 1)),
        )

        exception = ErrorException(error)

        assert isinstance(exception, Exception)

    # ----------------------------------------------------------------------
    def test_CanBeRaisedAndCaught(self):
        error = Error(
            "Catchable error",
            Region(Path("test.txt"), Location(5, 10), Location(5, 20)),
        )

        with pytest.raises(ErrorException) as exc_info:
            raise ErrorException(error)

        assert exc_info.value.error is error
        assert exc_info.value.error.message == "Catchable error"


# ----------------------------------------------------------------------
class TestCreateErrorType:
    # ----------------------------------------------------------------------
    def test_CreateWithStringAttribute(self):
        MyError = CreateErrorType(
            "Error with value: {value}",
            value=str,
        )

        region = Region(Path("test.txt"), Location(1, 1), Location(1, 10))
        error = MyError.Create(region, "test_value")

        assert error.message == "Error with value: test_value"
        assert error.value == "test_value"  # ty: ignore[unresolved-attribute]
        assert isinstance(error, Error)

    # ----------------------------------------------------------------------
    def test_CreateWithMultipleAttributes(self):
        MyError = CreateErrorType(
            "Found {count} errors in {filename}",
            count=int,
            filename=str,
        )

        region = Region(Path("test.txt"), Location(1, 1), Location(1, 10))
        error = MyError.Create(region, 5, "source.py")

        assert error.message == "Found 5 errors in source.py"
        assert error.count == 5  # ty: ignore[unresolved-attribute]
        assert error.filename == "source.py"  # ty: ignore[unresolved-attribute]

    # ----------------------------------------------------------------------
    def test_CreateWithEnumAttribute(self):
        class Severity(Enum):
            LOW = 1
            MEDIUM = 2
            HIGH = 3

        MyError = CreateErrorType(
            "Severity level: {severity}",
            severity=Severity,
        )

        region = Region(Path("test.txt"), Location(1, 1), Location(1, 10))
        error = MyError.Create(region, Severity.HIGH)

        assert error.message == "Severity level: HIGH"
        assert error.severity == Severity.HIGH  # ty: ignore[unresolved-attribute]

    # ----------------------------------------------------------------------
    def test_CreateWithListAttribute(self):
        MyError = CreateErrorType(
            "Missing items: {items}",
            items=list,
        )

        region = Region(Path("test.txt"), Location(1, 1), Location(1, 10))
        error = MyError.Create(region, ["a", "b", "c"])

        assert error.message == "Missing items: ['a', 'b', 'c']"
        assert error.items == ["a", "b", "c"]  # ty: ignore[unresolved-attribute]

    # ----------------------------------------------------------------------
    def test_IsFrozen(self):
        MyError = CreateErrorType(
            "Error: {msg}",
            msg=str,
        )

        region = Region(Path("test.txt"), Location(1, 1), Location(1, 10))
        error = MyError.Create(region, "test")

        with pytest.raises(AttributeError):
            error.msg = "modified"

    # ----------------------------------------------------------------------
    def test_InheritsErrorBehavior(self):
        MyError = CreateErrorType(
            "Custom error: {detail}",
            detail=str,
        )

        region = Region(Path("test.txt"), Location(5, 10), Location(5, 10))
        error = MyError.Create(region, "something went wrong")

        assert str(error) == "Custom error: something went wrong (test.txt, Ln 5 Col 10)"

    # ----------------------------------------------------------------------
    def test_CreateAsExceptionWorks(self):
        MyError = CreateErrorType(
            "Failed: {reason}",
            reason=str,
        )

        region = Region(Path("test.txt"), Location(1, 1), Location(1, 10))
        exception = MyError.CreateAsException(region, "timeout")

        assert isinstance(exception, ErrorException)
        assert exception.error.message == "Failed: timeout"
