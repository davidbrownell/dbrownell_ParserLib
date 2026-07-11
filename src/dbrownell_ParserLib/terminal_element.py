# noqa: D100
from dataclasses import dataclass
from typing import override

from dbrownell_ParserLib.element import Element


# ----------------------------------------------------------------------
@dataclass(eq=False)
class TerminalElement[T](Element):
    """Element with a single value member, typically used with leaves in an abstract syntax tree."""

    # ----------------------------------------------------------------------
    value: T

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @override
    def _GetTerminalUniqueId(self) -> tuple[object, ...]:
        return (self.value,)
