"""Unit tests for TerminalExpression class."""

from pathlib import Path

import pytest

from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_expression import TerminalExpression


# ----------------------------------------------------------------------
def _CreateRegion() -> Region:
    return Region(
        filename=Path("test.txt"),
        begin=Location(line=1, column=1),
        end=Location(line=1, column=10),
    )


# ----------------------------------------------------------------------
class TestTerminalExpressionConstruction:
    # ----------------------------------------------------------------------
    def test_IntValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert expr.value == 42
        assert expr.region__ == region

    # ----------------------------------------------------------------------
    def test_StrValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[str](region, "hello")

        assert expr.value == "hello"
        assert expr.region__ == region

    # ----------------------------------------------------------------------
    def test_BoolValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[bool](region, True)

        assert expr.value is True

    # ----------------------------------------------------------------------
    def test_FloatValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[float](region, 3.14)

        assert expr.value == 3.14

    # ----------------------------------------------------------------------
    def test_NoneValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[None](region, None)

        assert expr.value is None

    # ----------------------------------------------------------------------
    def test_ListValue(self):
        region = _CreateRegion()
        value = [1, 2, 3]
        expr = TerminalExpression[list](region, value)

        assert expr.value == [1, 2, 3]


# ----------------------------------------------------------------------
class TestTerminalExpressionUniqueId:
    # ----------------------------------------------------------------------
    def test_UniqueIdStructure(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert expr.unique_id__ == ("TerminalExpression", 42)

    # ----------------------------------------------------------------------
    def test_UniqueIdWithStringValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[str](region, "hello")

        assert expr.unique_id__ == ("TerminalExpression", "hello")

    # ----------------------------------------------------------------------
    def test_SameValuesSameUniqueId(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 42)
        expr2 = TerminalExpression[int](region, 42)

        assert expr1.unique_id__ == expr2.unique_id__

    # ----------------------------------------------------------------------
    def test_DifferentValuesDifferentUniqueId(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 42)
        expr2 = TerminalExpression[int](region, 43)

        assert expr1.unique_id__ != expr2.unique_id__


# ----------------------------------------------------------------------
class TestTerminalExpressionEquality:
    # ----------------------------------------------------------------------
    def test_NotEqualNonExpression(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert expr != "not an expression"
        assert expr != 42
        assert expr != None


# ----------------------------------------------------------------------
class TestTerminalExpressionClone:
    # ----------------------------------------------------------------------
    def test_ClonePreservesValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        cloned = expr.Clone()

        assert cloned.value == 42
        assert cloned.region__ == region

    # ----------------------------------------------------------------------
    def test_CloneWithOverriddenValue(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        cloned = expr.Clone(value=100)

        assert cloned.value == 100
        assert expr.value == 42

    # ----------------------------------------------------------------------
    def test_CloneWithOverriddenRegion(self):
        region1 = _CreateRegion()
        region2 = Region(
            filename=Path("other.txt"),
            begin=Location(line=5, column=5),
            end=Location(line=5, column=15),
        )
        expr = TerminalExpression[int](region1, 42)

        cloned = expr.Clone(region__=region2)

        assert cloned.region__ == region2
        assert expr.region__ == region1

    # ----------------------------------------------------------------------
    def test_CloneCreatesNewInstance(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        cloned = expr.Clone()

        assert expr is not cloned
