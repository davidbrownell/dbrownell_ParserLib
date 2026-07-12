from dataclasses import dataclass
from typing import override

from dbrownell_ParserLib.element import Element
from dbrownell_ParserLib.terminal_element import TerminalElement


# ----------------------------------------------------------------------
@dataclass(eq=False)
class BinaryExpression(Element):
    # ----------------------------------------------------------------------
    left: Element
    operator: TerminalElement[str]
    right: Element

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Element._GenerateAcceptDetailsResultType:
        yield "left", self.left
        yield "operator", self.operator
        yield "right", self.right


# ----------------------------------------------------------------------
@dataclass(eq=False)
class UnaryExpression(Element):
    # ----------------------------------------------------------------------
    operator: TerminalElement[str]
    operand: Element

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Element._GenerateAcceptDetailsResultType:
        yield "operator", self.operator
        yield "operand", self.operand
