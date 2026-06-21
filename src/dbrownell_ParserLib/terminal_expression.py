# noqa: D100
from dataclasses import dataclass
from typing import override

from dbrownell_ParserLib.expression import Expression


# ----------------------------------------------------------------------
@dataclass(eq=False)
class TerminalExpression[T](Expression):
    """Expression with a single value member, typically used with leaves in an abstract syntax tree."""

    # ----------------------------------------------------------------------
    value: T

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @override
    def _GetTerminalUniqueId(self) -> tuple[object, ...]:
        return (self.value,)
