# noqa: D104

from importlib.metadata import version

from dbrownell_ParserLib.antlr import (
    AntlrParser,
    AntlrVisitorMixinBase,
    BuildAntlrGrammar,
    CreateAntlrParser,
    InsignificantWhitespaceAntlrVisitorMixin,
    SignificantWhitespaceAntlrVisitorMixin,
)
from dbrownell_ParserLib.errors import CreateErrorType, Error, ErrorException, PythonError
from dbrownell_ParserLib.expression import Expression
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_expression import TerminalExpression
from dbrownell_ParserLib.visitors import ExpressionVisitor, ExpressionVisitorHelper, VisitResult


# ----------------------------------------------------------------------
__all__ = [
    "AntlrParser",
    "AntlrVisitorMixinBase",
    "BuildAntlrGrammar",
    "CreateAntlrParser",
    "CreateErrorType",
    "Error",
    "ErrorException",
    "Expression",
    "ExpressionVisitor",
    "ExpressionVisitorHelper",
    "InsignificantWhitespaceAntlrVisitorMixin",
    "Location",
    "PythonError",
    "Region",
    "SignificantWhitespaceAntlrVisitorMixin",
    "TerminalExpression",
    "VisitResult",
    "__version__",
]


__version__ = version("dbrownell_ParserLib")
