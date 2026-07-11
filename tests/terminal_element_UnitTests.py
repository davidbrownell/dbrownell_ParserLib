"""Unit tests for TerminalElement class."""

from pathlib import Path

import pytest

from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_element import TerminalElement


# ----------------------------------------------------------------------
def _CreateRegion() -> Region:
    return Region(
        filename=Path("test.txt"),
        begin=Location(line=1, column=1),
        end=Location(line=1, column=10),
    )


# ----------------------------------------------------------------------
class TestTerminalElementConstruction:
    # ----------------------------------------------------------------------
    def test_IntValue(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert element.value == 42
        assert element.region__ == region

    # ----------------------------------------------------------------------
    def test_StrValue(self):
        region = _CreateRegion()
        element = TerminalElement[str](region, "hello")

        assert element.value == "hello"
        assert element.region__ == region

    # ----------------------------------------------------------------------
    def test_BoolValue(self):
        region = _CreateRegion()
        element = TerminalElement[bool](region, True)

        assert element.value is True

    # ----------------------------------------------------------------------
    def test_FloatValue(self):
        region = _CreateRegion()
        element = TerminalElement[float](region, 3.14)

        assert element.value == 3.14

    # ----------------------------------------------------------------------
    def test_NoneValue(self):
        region = _CreateRegion()
        element = TerminalElement[None](region, None)

        assert element.value is None

    # ----------------------------------------------------------------------
    def test_ListValue(self):
        region = _CreateRegion()
        value = [1, 2, 3]
        element = TerminalElement[list](region, value)

        assert element.value == [1, 2, 3]


# ----------------------------------------------------------------------
class TestTerminalElementUniqueId:
    # ----------------------------------------------------------------------
    def test_UniqueIdStructure(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert element.unique_id__ == ("TerminalElement", 42)

    # ----------------------------------------------------------------------
    def test_UniqueIdWithStringValue(self):
        region = _CreateRegion()
        element = TerminalElement[str](region, "hello")

        assert element.unique_id__ == ("TerminalElement", "hello")

    # ----------------------------------------------------------------------
    def test_SameValuesSameUniqueId(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 42)
        element2 = TerminalElement[int](region, 42)

        assert element1.unique_id__ == element2.unique_id__

    # ----------------------------------------------------------------------
    def test_DifferentValuesDifferentUniqueId(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 42)
        element2 = TerminalElement[int](region, 43)

        assert element1.unique_id__ != element2.unique_id__


# ----------------------------------------------------------------------
class TestTerminalElementEquality:
    # ----------------------------------------------------------------------
    def test_NotEqualNonElement(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert element != "not an element"
        assert element != 42
        assert element != None


# ----------------------------------------------------------------------
class TestTerminalElementClone:
    # ----------------------------------------------------------------------
    def test_ClonePreservesValue(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        cloned = element.Clone()

        assert cloned.value == 42
        assert cloned.region__ == region

    # ----------------------------------------------------------------------
    def test_CloneWithOverriddenValue(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        cloned = element.Clone(value=100)

        assert cloned.value == 100
        assert element.value == 42

    # ----------------------------------------------------------------------
    def test_CloneWithOverriddenRegion(self):
        region1 = _CreateRegion()
        region2 = Region(
            filename=Path("other.txt"),
            begin=Location(line=5, column=5),
            end=Location(line=5, column=15),
        )
        element = TerminalElement[int](region1, 42)

        cloned = element.Clone(region__=region2)

        assert cloned.region__ == region2
        assert element.region__ == region1

    # ----------------------------------------------------------------------
    def test_CloneCreatesNewInstance(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        cloned = element.Clone()

        assert element is not cloned
