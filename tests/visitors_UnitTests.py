"""Unit tests for visitors module."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import override

import pytest

from dbrownell_ParserLib.expression import Expression
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_expression import TerminalExpression
from dbrownell_ParserLib.visitors import ExpressionVisitor, ExpressionVisitorHelper, VisitResult


# ----------------------------------------------------------------------
def _CreateRegion() -> Region:
    return Region(
        filename=Path("test.txt"),
        begin=Location(line=1, column=1),
        end=Location(line=1, column=10),
    )


# ----------------------------------------------------------------------
class TestVisitResult:
    # ----------------------------------------------------------------------
    def test_ContinueIsZero(self):
        assert VisitResult.Continue.value == 0

    # ----------------------------------------------------------------------
    def test_SkipDetailsIsAutoValue(self):
        assert VisitResult.SkipDetails.value != 0

    # ----------------------------------------------------------------------
    def test_SkipChildrenIsAutoValue(self):
        assert VisitResult.SkipChildren.value != 0

    # ----------------------------------------------------------------------
    def test_TerminateIsAutoValue(self):
        assert VisitResult.Terminate.value != 0

    # ----------------------------------------------------------------------
    def test_SkipAllIsCombinationOfSkipDetailsAndSkipChildren(self):
        assert VisitResult.SkipAll == (VisitResult.SkipDetails | VisitResult.SkipChildren)

    # ----------------------------------------------------------------------
    def test_FlagValuesAreDistinct(self):
        values = [
            VisitResult.SkipDetails.value,
            VisitResult.SkipChildren.value,
            VisitResult.Terminate.value,
        ]
        assert len(values) == len(set(values))

    # ----------------------------------------------------------------------
    def test_FlagCanBeCombined(self):
        combined = VisitResult.SkipDetails | VisitResult.Terminate
        assert combined & VisitResult.SkipDetails
        assert combined & VisitResult.Terminate
        assert not (combined & VisitResult.SkipChildren)

    # ----------------------------------------------------------------------
    def test_ContinueDoesNotContainOtherFlags(self):
        assert not (VisitResult.Continue & VisitResult.SkipDetails)
        assert not (VisitResult.Continue & VisitResult.SkipChildren)
        assert not (VisitResult.Continue & VisitResult.Terminate)


# ----------------------------------------------------------------------
class TestExpressionVisitorHelper:
    # ----------------------------------------------------------------------
    def test_OnExpressionYieldsContinue(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        visitor = ExpressionVisitorHelper()

        with visitor.OnExpression(expr) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_OnExpressionDetailsYieldsContinue(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        visitor = ExpressionVisitorHelper()

        with visitor.OnExpressionDetails(expr) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_OnExpressionChildrenYieldsContinue(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        visitor = ExpressionVisitorHelper()

        with visitor.OnExpressionChildren(expr, "children", []) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_GetAttrReturnsDefaultMethodForExpressionSuffix(self):
        visitor = ExpressionVisitorHelper()

        method = getattr(visitor, "OnSomeExpression")

        with method(None) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_GetAttrReturnsDefaultMethodForDetailPattern(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        visitor = ExpressionVisitorHelper()

        method = getattr(visitor, "OnSomeExpression__some_detail")

        result = method([expr], include_disabled=False)
        assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_GetAttrRaisesAttributeErrorForUnknownAttribute(self):
        visitor = ExpressionVisitorHelper()

        with pytest.raises(AttributeError, match="unknown_method"):
            getattr(visitor, "unknown_method")

    # ----------------------------------------------------------------------
    def test_GetAttrRaisesAttributeErrorForPartialDetailPattern(self):
        visitor = ExpressionVisitorHelper()

        with pytest.raises(AttributeError, match="OnSomeExpression__"):
            getattr(visitor, "OnSomeExpression__")

    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodAcceptsListOfExpressions(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 1)
        expr2 = TerminalExpression[int](region, 2)
        visitor = ExpressionVisitorHelper()

        method = getattr(visitor, "OnSomeExpression__detail")

        result = method([expr1, expr2], include_disabled=False)
        assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodAcceptsSingleExpression(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        visitor = ExpressionVisitorHelper()

        method = getattr(visitor, "OnSomeExpression__detail")

        result = method(expr, include_disabled=False)
        assert result == VisitResult.Continue


# ----------------------------------------------------------------------
@dataclass
class _ParentExpression(Expression):
    """Expression with children for testing visitor traversal."""

    children: list[Expression]

    # ----------------------------------------------------------------------
    @override
    def _GetAcceptChildren(self) -> Expression._GetAcceptChildrenResultType:
        if not self.children:
            return None
        return ("children", self.children)


# ----------------------------------------------------------------------
class TestExpressionVisitorHelperDefaultDetailMethodTermination:
    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodTerminatesWhenChildReturnsTerminate(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)

        termination_count = 0

        class TerminatingVisitor(ExpressionVisitorHelper):
            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                nonlocal termination_count
                termination_count += 1
                yield VisitResult.Terminate

        visitor = TerminatingVisitor()
        method = getattr(visitor, "OnSomeExpression__detail")

        result = method([child1, child2], include_disabled=False)

        assert result & VisitResult.Terminate
        assert termination_count == 1

    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodContinuesThroughAllExpressionsWhenNoTerminate(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        child3 = TerminalExpression[int](region, 3)

        visited_count = 0

        class CountingVisitor(ExpressionVisitorHelper):
            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                nonlocal visited_count
                visited_count += 1
                yield VisitResult.Continue

        visitor = CountingVisitor()
        method = getattr(visitor, "OnSomeExpression__detail")

        result = method([child1, child2, child3], include_disabled=False)

        assert result == VisitResult.Continue
        assert visited_count == 3
