from contextlib import contextmanager
from dataclasses import dataclass
from typing import override, TextIO, TYPE_CHECKING

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common.Streams.StreamDecorator import StreamDecorator

from dbrownell_ParserLib.element import Element, ElementVisitorHelper, VisitResult
from dbrownell_ParserLib.terminal_element import TerminalElement

if TYPE_CHECKING:
    from collections.abc import Generator


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


# ----------------------------------------------------------------------
class OutputVisitor(ElementVisitorHelper):
    # ----------------------------------------------------------------------
    def __init__(self, output: TextIO):
        self._streams: list[StreamDecorator] = [
            StreamDecorator(output),
        ]

    # ----------------------------------------------------------------------
    @contextmanager
    def OnElement(self, element: Element) -> Generator[VisitResult]:
        self._streams[-1].write(f"{element.__class__.__name__}, {element.region__.begin}")

        if element.region__.begin != element.region__.end:
            self._streams[-1].write(f" - {element.region__.end}")

        self._streams[-1].write("\n")

        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @contextmanager
    def OnBinaryExpression(self, element: BinaryExpression) -> Generator[VisitResult]:
        self._streams.append(StreamDecorator(self._streams[-1], line_prefix="  "))
        with ExitStack(lambda: self._streams.pop()):
            yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @contextmanager
    def OnTerminalElement(self, element: TerminalElement) -> Generator[VisitResult]:
        self._streams[-1].write(f"{element.value}\n")
        yield VisitResult.Continue
