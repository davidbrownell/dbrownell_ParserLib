"""End-to-end tests for BuildAntlrGrammar."""

import shutil
import textwrap

from pathlib import Path
from typing import cast

import pytest

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent

from dbrownell_ParserLib.antlr.build_antlr_grammar import BuildAntlrGrammar


# ----------------------------------------------------------------------
def _JavaAvailable() -> bool:
    return shutil.which("java") is not None


# ----------------------------------------------------------------------
def _Antlr4Available() -> bool:
    try:
        import antlr4  # noqa: F401

        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------
# Sample ANTLR grammar for testing
SAMPLE_GRAMMAR = r"""grammar SimpleExpr;

expr: INT (PLUS INT)* ;
PLUS: '+' ;
INT: [0-9]+ ;
WS: [ \t\r\n]+ -> skip ;
"""


# ----------------------------------------------------------------------
@pytest.mark.skipif(
    not _JavaAvailable(),
    reason="Java is required to run these tests",
)
class TestBuildAntlrGrammar:
    # ----------------------------------------------------------------------
    class TestSuccessfulBuild:
        # ----------------------------------------------------------------------
        def test_GeneratesExpectedFiles(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
            )

            content = cast(str, next(dm_and_content))

            expected_content = textwrap.dedent(
                """\
                Heading...
                  Generating 'SimpleExpr.g4'...DONE! (0, <scrubbed duration>)
                DONE! (0, <scrubbed duration>)
                """
            )

            assert content == expected_content

            # ANTLR generates these files for a grammar with visitors enabled
            assert (output_dir / "SimpleExprLexer.py").is_file()
            assert (output_dir / "SimpleExprParser.py").is_file()
            assert (output_dir / "SimpleExprVisitor.py").is_file()
            assert (output_dir / "SimpleExpr.tokens").is_file()
            assert (output_dir / "SimpleExprLexer.tokens").is_file()
            assert (output_dir / "SimpleExprLexer.interp").is_file()
            assert (output_dir / "SimpleExpr.interp").is_file()

        # ----------------------------------------------------------------------
        def test_CreatesInitFile(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
                create_init_file=True,
            )

            cast(str, next(dm_and_content))

            init_file = output_dir / "__init__.py"

            assert init_file.is_file()
            assert init_file.read_text() == ""

        # ----------------------------------------------------------------------
        def test_CreatesGitignoreFile(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
                create_gitignore_file=True,
            )

            cast(str, next(dm_and_content))

            gitignore_file = output_dir / ".gitignore"

            assert gitignore_file.is_file()
            assert gitignore_file.read_text() == "*\n"

        # ----------------------------------------------------------------------
        def test_SkipsInitFileWhenDisabled(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
                create_init_file=False,
            )

            cast(str, next(dm_and_content))

            init_file = output_dir / "__init__.py"

            assert not init_file.exists()

        # ----------------------------------------------------------------------
        def test_SkipsGitignoreFileWhenDisabled(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
                create_gitignore_file=False,
            )

            cast(str, next(dm_and_content))

            gitignore_file = output_dir / ".gitignore"

            assert not gitignore_file.exists()

        # ----------------------------------------------------------------------
        def test_DoesNotOverwriteExistingInitFile(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            existing_init = output_dir / "__init__.py"
            existing_content = "# Existing content\n"
            existing_init.write_text(existing_content)

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
                create_init_file=True,
            )

            cast(str, next(dm_and_content))

            assert existing_init.read_text() == existing_content

        # ----------------------------------------------------------------------
        def test_DoesNotOverwriteExistingGitignoreFile(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            existing_gitignore = output_dir / ".gitignore"
            existing_content = "*.pyc\n"
            existing_gitignore.write_text(existing_content)

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
                create_gitignore_file=True,
            )

            cast(str, next(dm_and_content))

            assert existing_gitignore.read_text() == existing_content

    # ----------------------------------------------------------------------
    class TestGeneratedCodeFunctionality:
        # ----------------------------------------------------------------------
        @pytest.mark.skipif(
            not _Antlr4Available(),
            reason="antlr4-python3-runtime not installed",
        )
        def test_GeneratedParserCanParseInput(self, tmp_path: Path):
            grammar_file = tmp_path / "SimpleExpr.g4"
            grammar_file.write_text(SAMPLE_GRAMMAR)

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent(expected_result=0))
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
            )

            cast(str, next(dm_and_content))

            # Import the generated parser and test it
            import sys

            sys.path.insert(0, str(output_dir))
            with ExitStack(lambda: sys.path.pop(0)):
                from antlr4 import CommonTokenStream, InputStream

                from SimpleExprLexer import SimpleExprLexer  # ty: ignore[unresolved-import]
                from SimpleExprParser import SimpleExprParser  # ty: ignore[unresolved-import]

                input_stream = InputStream("1 + 2 + 3")
                lexer = SimpleExprLexer(input_stream)
                token_stream = CommonTokenStream(lexer)
                parser = SimpleExprParser(token_stream)

                tree = parser.expr()

                # Verify parsing succeeded
                assert parser.getNumberOfSyntaxErrors() == 0
                assert tree is not None

    # ----------------------------------------------------------------------
    class TestFailure:
        # ----------------------------------------------------------------------
        def test_InvalidGrammarReturnsNonZeroResult(self, tmp_path: Path):
            grammar_file = tmp_path / "Invalid.g4"
            grammar_file.write_text("this is not valid ANTLR grammar")

            output_dir = tmp_path / "output"
            output_dir.mkdir()

            dm_and_content = iter(GenerateDoneManagerAndContent())
            dm = cast(DoneManager, next(dm_and_content))

            BuildAntlrGrammar(
                dm,
                grammar_file,
                output_dir,
            )

            # Don't check expected_result in generator since we expect failure
            cast(str, next(dm_and_content))

            assert dm.result != 0
