"""Contains types related to Expression visitation."""

import types

from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import auto, Flag
from typing import override, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from dbrownell_ParserLib.expression import Expression


# ----------------------------------------------------------------------
class VisitResult(Flag):
    """Result returned during visitation that controls the flow of the visitation process."""

    Continue = 0
    """Continue visiting the rest of the expressions as normal."""

    SkipDetails = auto()
    """Skip visiting the details of this expression, but continue visiting the rest of the expressions as normal."""

    SkipChildren = auto()
    """Skip visiting the children of this expression, but continue visiting the rest of the expressions as normal."""

    Terminate = auto()
    """Terminate the visitation process immediately."""

    # Amalgamations
    SkipAll = SkipDetails | SkipChildren


# ----------------------------------------------------------------------
class ExpressionVisitor(ABC):
    """Abstract base class for a visitor that accepts Expressions."""

    # ----------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def OnExpression(
        self,
        expression: Expression,
    ) -> Generator[VisitResult]:
        """Call for every expression."""

        raise NotImplementedError("Abstract method")  # noqa: EM101  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def OnExpressionDetails(
        self,
        expression: Expression,
    ) -> Generator[VisitResult]:
        """Call when visiting the details of an expression."""

        raise NotImplementedError("Abstract method")  # noqa: EM101  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def OnExpressionChildren(
        self,
        expression: Expression,
        children_name: str,
        children: Iterable[Expression],
    ) -> Generator[VisitResult]:
        """Call when visiting the children of an expression."""

        raise NotImplementedError("Abstract method")  # noqa: EM101  # pragma: no cover

    # ----------------------------------------------------------------------
    # Derived classes should implement the following methods:
    #
    #   @contextmanager
    #   def On<Expression Name>(self, expression: <Expression Name>) -> Generator[VisitResult]:
    #       ...
    #
    #   def On<Expression Name>__<Detail Name>(self, expression_or_expressions: <Expression Name> | list[<Expression Name>], include_disabled: bool) -> VisitResult:
    #       ...
    #


# ----------------------------------------------------------------------
class ExpressionVisitorHelper(ExpressionVisitor):
    """Base class that makes writing custom visitors easier by providing default behavior for visitation methods."""

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnExpression(
        self,
        expression: Expression,
    ) -> Generator[VisitResult]:
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnExpressionDetails(
        self,
        expression: Expression,
    ) -> Generator[VisitResult]:
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnExpressionChildren(
        self,
        expression: Expression,
        children_name: str,
        children: Iterable[Expression],
    ) -> Generator[VisitResult]:
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    def __getattr__(
        self,
        method_name: str,
    ) -> object:
        if method_name.startswith("On"):
            index = method_name.find("__")
            if index != -1 and not method_name.endswith("__"):
                return types.MethodType(self.__class__._DefaultDetailMethod, self)  # noqa: SLF001

            if index == -1:
                return self.__class__._DefaultExpressionMethod  # noqa: SLF001

        raise AttributeError(method_name)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @contextmanager
    def _DefaultExpressionMethod(*args, **kwargs) -> Generator[VisitResult]:  # noqa: ARG004
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    def _DefaultDetailMethod(
        self,
        expression_or_expressions: Expression | list[Expression],
        *,
        include_disabled: bool,
    ) -> VisitResult:
        expressions: list[Expression] = (  # ty: ignore[invalid-assignment]
            expression_or_expressions
            if isinstance(expression_or_expressions, list)
            else [expression_or_expressions]
        )

        for expression in expressions:
            result = expression.Accept(self, include_disabled=include_disabled)
            if result & VisitResult.Terminate:
                return result

        return VisitResult.Continue
