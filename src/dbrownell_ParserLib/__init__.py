# noqa: D104

from importlib.metadata import version

from dbrownell_ParserLib.antlr import (
    AntlrParser,
    AntlrParserException,
    AntlrVisitorMixinBase,
    BuildAntlrGrammar,
    CreateAntlrParser,
    InsignificantWhitespaceAntlrVisitorMixin,
    SignificantWhitespaceAntlrVisitorMixin,
)
from dbrownell_ParserLib.errors import Error, PythonError
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region


# ----------------------------------------------------------------------
__all__ = [
    "AntlrParser",
    "AntlrParserException",
    "AntlrVisitorMixinBase",
    "BuildAntlrGrammar",
    "CreateAntlrParser",
    "Error",
    "InsignificantWhitespaceAntlrVisitorMixin",
    "Location",
    "PythonError",
    "Region",
    "SignificantWhitespaceAntlrVisitorMixin",
    "__version__",
]


__version__ = version("dbrownell_ParserLib")
