"""Unit tests for CreateAntlrParser and AntlrParser."""

import sys
import tempfile

from datetime import datetime, UTC
from pathlib import Path
from typing import Callable, cast
from unittest.mock import MagicMock, patch

import antlr4
import pytest

from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent

from dbrownell_ParserLib.antlr.antlr_parser import AntlrParser, CreateAntlrParser
from dbrownell_ParserLib.errors import Error, ErrorException
from dbrownell_ParserLib.region import Location, Region


# ----------------------------------------------------------------------
# |
# |  Helper Functions and Classes
# |
# ----------------------------------------------------------------------
class MockLexer(antlr4.Lexer):
    """Mock lexer for testing."""

    def __init__(self, input_stream: antlr4.InputStream) -> None:
        self._input = input_stream
        self._listeners: list = []

    def removeErrorListeners(self) -> None:
        self._listeners.clear()

    def addErrorListener(self, listener) -> None:
        self._listeners.append(listener)


# ----------------------------------------------------------------------
class MockParser(antlr4.Parser):
    """Mock parser for testing."""

    def __init__(self, token_stream: antlr4.CommonTokenStream) -> None:
        self._input = token_stream
        self._listeners: list = []

    def removeErrorListeners(self) -> None:
        self._listeners.clear()

    def addErrorListener(self, listener) -> None:
        self._listeners.append(listener)


# ----------------------------------------------------------------------
class MockVisitor(antlr4.ParseTreeVisitor):
    """Mock visitor for testing."""

    def __init__(
        self,
        filename: Path,
        on_progress_func: Callable[[int], None],
        *,
        is_included_file: bool,
    ) -> None:
        self.filename = filename
        self.on_progress_func = on_progress_func
        self.is_included_file = is_included_file
        self.visited = False

    def visit(self, tree) -> None:
        self.visited = True


# ----------------------------------------------------------------------
class MockParserRuleContext(antlr4.ParserRuleContext):
    """Mock parser rule context for testing."""

    def accept(self, visitor: antlr4.ParseTreeVisitor) -> None:
        visitor.visit(self)


# ----------------------------------------------------------------------
def CreateMockVisitor(
    filename: Path,
    on_progress_func: Callable[[int], None],
    *,
    is_included_file: bool,
    parser_newline_string: str | None,
    indent_token_type: int | None,
    dedent_token_type: int | None,
) -> MockVisitor:
    return MockVisitor(filename, on_progress_func, is_included_file=is_included_file)


# ----------------------------------------------------------------------
def GetMockAst(parser: antlr4.Parser) -> MockParserRuleContext:
    return MockParserRuleContext()


# ----------------------------------------------------------------------
# |
# |  Tests
# |
# ----------------------------------------------------------------------
class TestCreateAntlrParser:
    # ----------------------------------------------------------------------
    def test_CreatesAntlrParser(self):
        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            CreateMockVisitor,
            GetMockAst,
        )

        assert isinstance(parser, AntlrParser)

    # ----------------------------------------------------------------------
    def test_WithCustomLexerInit(self):
        lexer_init_called = False

        def CustomLexerInit(lexer: antlr4.Lexer) -> None:
            nonlocal lexer_init_called
            lexer_init_called = True

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            CreateMockVisitor,
            GetMockAst,
            custom_lexer_init_func=CustomLexerInit,
        )

        assert isinstance(parser, AntlrParser)

    # ----------------------------------------------------------------------
    def test_WithCustomParserInit(self):
        parser_init_called = False

        def CustomParserInit(parser: antlr4.Parser) -> None:
            nonlocal parser_init_called
            parser_init_called = True

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            CreateMockVisitor,
            GetMockAst,
            custom_parser_init_func=CustomParserInit,
        )

        assert isinstance(parser, AntlrParser)


# ----------------------------------------------------------------------
class TestAntlrParserCall:
    # ----------------------------------------------------------------------
    class TestSingleFile:
        # ----------------------------------------------------------------------
        def test_ParsesSingleFile(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                test_file = temp_path / "test.txt"
                test_file.write_text("test content", encoding="utf-8")

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                    mock_token_stream.return_value = MagicMock()
                    mock_token_stream.return_value.fill = MagicMock()

                    result = parser(dm, test_file, None, single_threaded=True, quiet=True)

                cast(str, next(dm_and_content))

                assert isinstance(result, dict)
                assert len(result) == 1

                filename_key = Path(test_file.name)
                assert filename_key in result
                assert isinstance(result[filename_key], MockVisitor)

        # ----------------------------------------------------------------------
        def test_ParsesSingleFileWithSupportedExtensions(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                test_file = temp_path / "test.txt"
                test_file.write_text("test content", encoding="utf-8")

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                    mock_token_stream.return_value = MagicMock()
                    mock_token_stream.return_value.fill = MagicMock()

                    result = parser(dm, test_file, {".txt"}, single_threaded=True, quiet=True)

                cast(str, next(dm_and_content))

                assert isinstance(result, dict)
                assert len(result) == 1

    # ----------------------------------------------------------------------
    class TestMultipleFiles:
        # ----------------------------------------------------------------------
        def test_ParsesMultipleFiles(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                test_file1 = temp_path / "test1.txt"
                test_file2 = temp_path / "test2.txt"
                test_file1.write_text("content 1", encoding="utf-8")
                test_file2.write_text("content 2", encoding="utf-8")

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                    mock_token_stream.return_value = MagicMock()
                    mock_token_stream.return_value.fill = MagicMock()

                    result = parser(dm, [test_file1, test_file2], None, single_threaded=True, quiet=True)

                cast(str, next(dm_and_content))

                assert isinstance(result, dict)
                assert len(result) == 2

        # ----------------------------------------------------------------------
        def test_EmptyFilenamesRaisesError(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with pytest.raises(ValueError, match="Invalid filenames"):
                parser(dm, [], None, single_threaded=True, quiet=True)

        # ----------------------------------------------------------------------
        def test_FilesInDifferentDirectories(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                subdir = temp_path / "subdir"
                subdir.mkdir()

                test_file1 = temp_path / "test1.txt"
                test_file2 = subdir / "test2.txt"
                test_file1.write_text("content 1", encoding="utf-8")
                test_file2.write_text("content 2", encoding="utf-8")

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                    mock_token_stream.return_value = MagicMock()
                    mock_token_stream.return_value.fill = MagicMock()

                    result = parser(dm, [test_file1, test_file2], None, single_threaded=True, quiet=True)

                cast(str, next(dm_and_content))

                assert isinstance(result, dict)
                assert len(result) == 2

        # ----------------------------------------------------------------------
        @pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test for drive letters")
        def test_FilesOnDifferentDrivesRaisesError(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            file1 = Path("C:/test/file1.txt")
            file2 = Path("D:/test/file2.txt")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with pytest.raises(ValueError, match="don't have the same drive"):
                parser(dm, [file1, file2], None, single_threaded=True, quiet=True)

    # ----------------------------------------------------------------------
    class TestWorkspaces:
        # ----------------------------------------------------------------------
        def test_ParsesSingleWorkspace(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                def ContentFunc() -> tuple[str, datetime]:
                    return "test content", datetime.now(UTC)

                workspaces: dict[Path, dict[Path, Callable[[], tuple[str, datetime]]]] = {
                    temp_path: {
                        Path("test.txt"): ContentFunc,
                    },
                }

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                    mock_token_stream.return_value = MagicMock()
                    mock_token_stream.return_value.fill = MagicMock()

                    result = parser(dm, workspaces, None, single_threaded=True, quiet=True)

                cast(str, next(dm_and_content))

                assert isinstance(result, dict)
                assert len(result) == 1
                assert temp_path.resolve() in result

        # ----------------------------------------------------------------------
        def test_ParsesMultipleWorkspaces(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir1:
                with tempfile.TemporaryDirectory() as temp_dir2:
                    temp_path1 = Path(temp_dir1)
                    temp_path2 = Path(temp_dir2)

                    def ContentFunc1() -> tuple[str, datetime]:
                        return "content 1", datetime.now(UTC)

                    def ContentFunc2() -> tuple[str, datetime]:
                        return "content 2", datetime.now(UTC)

                    workspaces: dict[Path, dict[Path, Callable[[], tuple[str, datetime]]]] = {
                        temp_path1: {
                            Path("file1.txt"): ContentFunc1,
                        },
                        temp_path2: {
                            Path("file2.txt"): ContentFunc2,
                        },
                    }

                    dm_and_content = iter(GenerateDoneManagerAndContent())
                    dm = cast(DoneManager, next(dm_and_content))

                    with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                        mock_token_stream.return_value = MagicMock()
                        mock_token_stream.return_value.fill = MagicMock()

                        result = parser(dm, workspaces, None, single_threaded=True, quiet=True)

                    cast(str, next(dm_and_content))

                    assert isinstance(result, dict)
                    assert len(result) == 2
                    assert temp_path1.resolve() in result
                    assert temp_path2.resolve() in result

        # ----------------------------------------------------------------------
        def test_NestedWorkspacesRaisesError(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                nested_path = temp_path / "nested"
                nested_path.mkdir()

                def ContentFunc() -> tuple[str, datetime]:
                    return "content", datetime.now(UTC)

                workspaces: dict[Path, dict[Path, Callable[[], tuple[str, datetime]]]] = {
                    temp_path: {
                        Path("file1.txt"): ContentFunc,
                    },
                    nested_path: {
                        Path("file2.txt"): ContentFunc,
                    },
                }

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with pytest.raises(ValueError, match="nested within the root"):
                    parser(dm, workspaces, None, single_threaded=True, quiet=True)

        # ----------------------------------------------------------------------
        def test_NestedWorkspacesReversedOrderRaisesError(self):
            parser = CreateAntlrParser(
                MockLexer,
                MockParser,
                CreateMockVisitor,
                GetMockAst,
            )

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                nested_path = temp_path / "nested"
                nested_path.mkdir()

                def ContentFunc() -> tuple[str, datetime]:
                    return "content", datetime.now(UTC)

                workspaces: dict[Path, dict[Path, Callable[[], tuple[str, datetime]]]] = {
                    nested_path: {
                        Path("file2.txt"): ContentFunc,
                    },
                    temp_path: {
                        Path("file1.txt"): ContentFunc,
                    },
                }

                dm_and_content = iter(GenerateDoneManagerAndContent())
                dm = cast(DoneManager, next(dm_and_content))

                with pytest.raises(ValueError, match="nested within the root"):
                    parser(dm, workspaces, None, single_threaded=True, quiet=True)


# ----------------------------------------------------------------------
class TestCustomInitFunctions:
    # ----------------------------------------------------------------------
    def test_CustomLexerInitCalled(self):
        lexer_init_called = False

        def CustomLexerInit(lexer: antlr4.Lexer) -> None:
            nonlocal lexer_init_called
            lexer_init_called = True

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            CreateMockVisitor,
            GetMockAst,
            custom_lexer_init_func=CustomLexerInit,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

        assert lexer_init_called

    # ----------------------------------------------------------------------
    def test_CustomParserInitCalled(self):
        parser_init_called = False

        def CustomParserInit(parser: antlr4.Parser) -> None:
            nonlocal parser_init_called
            parser_init_called = True

        antlr_parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            CreateMockVisitor,
            GetMockAst,
            custom_parser_init_func=CustomParserInit,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                antlr_parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

        assert parser_init_called


# ----------------------------------------------------------------------
class TestVisitorCreation:
    # ----------------------------------------------------------------------
    def test_VisitorReceivesCorrectFilename(self):
        received_filename = None

        def TrackingVisitorFunc(
            filename: Path,
            on_progress_func: Callable[[int], None],
            *,
            is_included_file: bool,
            parser_newline_string: str | None,
            indent_token_type: int | None,
            dedent_token_type: int | None,
        ) -> MockVisitor:
            nonlocal received_filename
            received_filename = filename
            return MockVisitor(filename, on_progress_func, is_included_file=is_included_file)

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            TrackingVisitorFunc,
            GetMockAst,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "myfile.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

        assert received_filename is not None
        assert received_filename.name == "myfile.txt"

    # ----------------------------------------------------------------------
    def test_VisitorReceivesIsIncludedFileFalse(self):
        received_is_included = None

        def TrackingVisitorFunc(
            filename: Path,
            on_progress_func: Callable[[int], None],
            *,
            is_included_file: bool,
            parser_newline_string: str | None,
            indent_token_type: int | None,
            dedent_token_type: int | None,
        ) -> MockVisitor:
            nonlocal received_is_included
            received_is_included = is_included_file
            return MockVisitor(filename, on_progress_func, is_included_file=is_included_file)

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            TrackingVisitorFunc,
            GetMockAst,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

        assert received_is_included is False


# ----------------------------------------------------------------------
class TestErrorHandling:
    # ----------------------------------------------------------------------
    def test_ExceptionDuringParsingReturnsError(self):
        def FailingVisitorFunc(
            filename: Path,
            on_progress_func: Callable[[int], None],
            *,
            is_included_file: bool,
            parser_newline_string: str | None,
            indent_token_type: int | None,
            dedent_token_type: int | None,
        ) -> MockVisitor:
            raise RuntimeError("Parsing failed")

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            FailingVisitorFunc,
            GetMockAst,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                result = parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

            filename_key = Path(test_file.name)
            assert filename_key in result
            assert isinstance(result[filename_key], Error)

    # ----------------------------------------------------------------------
    def test_DoneManagerResultSetOnErrors(self):
        def FailingVisitorFunc(
            filename: Path,
            on_progress_func: Callable[[int], None],
            *,
            is_included_file: bool,
            parser_newline_string: str | None,
            indent_token_type: int | None,
            dedent_token_type: int | None,
        ) -> MockVisitor:
            raise RuntimeError("Parsing failed")

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            FailingVisitorFunc,
            GetMockAst,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

            assert dm.result == 1

    # ----------------------------------------------------------------------
    def test_ErrorExceptionReturnsError(self):
        def FailingVisitorFunc(
            filename: Path,
            on_progress_func: Callable[[int], None],
            *,
            is_included_file: bool,
            parser_newline_string: str | None,
            indent_token_type: int | None,
            dedent_token_type: int | None,
        ) -> MockVisitor:
            error = Error(
                "Syntax error in file",
                Region(filename, Location(1, 1), Location(1, 1)),
            )
            raise ErrorException(error)

        parser = CreateAntlrParser(
            MockLexer,
            MockParser,
            FailingVisitorFunc,
            GetMockAst,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.txt"
            test_file.write_text("test content", encoding="utf-8")

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            with patch.object(antlr4, "CommonTokenStream") as mock_token_stream:
                mock_token_stream.return_value = MagicMock()
                mock_token_stream.return_value.fill = MagicMock()

                result = parser(dm, test_file, None, single_threaded=True, quiet=True)

            cast(str, next(dm_and_content))

            filename_key = Path(test_file.name)
            assert filename_key in result
            assert isinstance(result[filename_key], Error)
            assert result[filename_key].message == "Syntax error in file"  # ty: ignore[unresolved-attribute]
