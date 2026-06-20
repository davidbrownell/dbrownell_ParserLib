# noqa: D104
from pathlib import Path
from typing import TYPE_CHECKING

from dbrownell_Common import SubprocessEx

if TYPE_CHECKING:
    from dbrownell_Common.Streams.DoneManager import DoneManager


# ----------------------------------------------------------------------
def BuildAntlrGrammar(
    dm: DoneManager,
    antlr_grammar_filename: Path,
    output_dir: Path,
    *,
    create_init_file: bool = True,
    create_gitignore_file: bool = True,
) -> None:
    """Build the Antlr grammar; note that java must be available on the command line."""

    with dm.Nested(f"Generating '{antlr_grammar_filename.name}'...") as generate_dm:
        jar_filename = Path(__file__).parent / "antlr-4.13.2-complete.jar"
        assert jar_filename.is_file(), jar_filename

        command_line = f'java -jar "{jar_filename}" -Dlanguage=Python3 -o "{output_dir}" -no-listener -visitor "{antlr_grammar_filename}"'

        generate_dm.WriteVerbose(f"Command line: {command_line}\n\n")

        with generate_dm.YieldStream() as stream:
            generate_dm.result = SubprocessEx.Stream(command_line, stream)
            if generate_dm.result != 0:
                return

        if create_init_file:
            init_filename = output_dir / "__init__.py"

            if not init_filename.is_file():
                init_filename.touch()

        if create_gitignore_file:
            gitignore_filename = output_dir / ".gitignore"

            if not gitignore_filename.is_file():
                gitignore_filename.write_text("*\n")
