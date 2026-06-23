import textwrap

from pathlib import Path
from typing import cast

import pytest

from dbrownell_Common.Streams.DoneManager import DoneManager
from dbrownell_Common.TestHelpers.StreamTestHelpers import GenerateDoneManagerAndContent

from dbrownell_ParserLib import BuildAntlrGrammar


# ----------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def build_ignore_whitespace_grammar():
    grammar_filename = Path(__file__).parent / "ignore_whitespace.g4"
    assert grammar_filename.is_file(), grammar_filename

    dm_and_sink = iter(GenerateDoneManagerAndContent())

    dm = cast(DoneManager, next(dm_and_sink))

    BuildAntlrGrammar(
        dm,
        grammar_filename,
        Path(__file__).parent / "GeneratedCode" / "IgnoreWhitespace",
    )

    content = cast(str, next(dm_and_sink))

    assert dm.result == 0, content

    assert content == textwrap.dedent(
        """\
        Heading...
          Generating 'ignore_whitespace.g4'...DONE! (0, <scrubbed duration>)
        DONE! (0, <scrubbed duration>)
        """,
    )
