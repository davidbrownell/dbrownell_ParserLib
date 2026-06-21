from contextlib import contextmanager
from dataclasses import dataclass
from typing import override, TextIO, TYPE_CHECKING

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common.Streams.StreamDecorator import StreamDecorator

from dbrownell_ParserLib import Expression, ExpressionVisitorHelper, TerminalExpression, VisitResult

if TYPE_CHECKING:
    from collections.abc import Generator


# ----------------------------------------------------------------------
@dataclass(eq=False)
class BinaryExpression(Expression):
    # ----------------------------------------------------------------------
    left: Expression
    operator: TerminalExpression[str]
    right: Expression

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Expression._GenerateAcceptDetailsResultType:
        yield "left", self.left
        yield "operator", self.operator
        yield "right", self.right


# ----------------------------------------------------------------------
@dataclass(eq=False)
class UnaryExpression(Expression):
    # ----------------------------------------------------------------------
    operator: TerminalExpression[str]
    operand: Expression

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Expression._GenerateAcceptDetailsResultType:
        yield "operator", self.operator
        yield "operand", self.operand


# ----------------------------------------------------------------------
class OutputVisitor(ExpressionVisitorHelper):
    # ----------------------------------------------------------------------
    def __init__(self, output: TextIO):
        self._streams: list[StreamDecorator] = [
            StreamDecorator(output),
        ]

    # ----------------------------------------------------------------------
    @contextmanager
    def OnExpression(self, expression: Expression) -> Generator[VisitResult]:
        self._streams[-1].write(f"{expression.__class__.__name__}, {expression.region__.begin}")

        if expression.region__.begin != expression.region__.end:
            self._streams[-1].write(f" - {expression.region__.end}")

        self._streams[-1].write("\n")

        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @contextmanager
    def OnBinaryExpression(self, expression: BinaryExpression) -> Generator[VisitResult]:
        self._streams.append(StreamDecorator(self._streams[-1], line_prefix="  "))
        with ExitStack(lambda: self._streams.pop()):
            yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @contextmanager
    def OnTerminalExpression(self, expression: TerminalExpression) -> Generator[VisitResult]:
        self._streams[-1].write(f"{expression.value}\n")
        yield VisitResult.Continue
