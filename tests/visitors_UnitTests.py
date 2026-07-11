"""Unit tests for visitors module."""

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import override

import pytest

from dbrownell_ParserLib.element import Element
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_element import TerminalElement
from dbrownell_ParserLib.visitors import ElementVisitor, ElementVisitorHelper, VisitResult


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
class TestElementVisitorHelper:
    # ----------------------------------------------------------------------
    def test_OnElementYieldsContinue(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        visitor = ElementVisitorHelper()

        with visitor.OnElement(element) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_OnElementDetailsYieldsContinue(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        visitor = ElementVisitorHelper()

        with visitor.OnElementDetails(element) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_OnElementChildrenYieldsContinue(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        visitor = ElementVisitorHelper()

        with visitor.OnElementChildren(element, "children", []) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_GetAttrReturnsDefaultMethodForElementSuffix(self):
        visitor = ElementVisitorHelper()

        method = getattr(visitor, "OnSomeElement")

        with method(None) as result:
            assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_GetAttrReturnsDefaultMethodForDetailPattern(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        visitor = ElementVisitorHelper()

        method = getattr(visitor, "OnSomeElement__some_detail")

        result = method([element], include_disabled=False)
        assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_GetAttrRaisesAttributeErrorForUnknownAttribute(self):
        visitor = ElementVisitorHelper()

        with pytest.raises(AttributeError, match="unknown_method"):
            getattr(visitor, "unknown_method")

    # ----------------------------------------------------------------------
    def test_GetAttrRaisesAttributeErrorForPartialDetailPattern(self):
        visitor = ElementVisitorHelper()

        with pytest.raises(AttributeError, match="OnSomeElement__"):
            getattr(visitor, "OnSomeElement__")

    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodAcceptsListOfElements(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 1)
        element2 = TerminalElement[int](region, 2)
        visitor = ElementVisitorHelper()

        method = getattr(visitor, "OnSomeElement__detail")

        result = method([element1, element2], include_disabled=False)
        assert result == VisitResult.Continue

    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodAcceptsSingleElement(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        visitor = ElementVisitorHelper()

        method = getattr(visitor, "OnSomeElement__detail")

        result = method(element, include_disabled=False)
        assert result == VisitResult.Continue


# ----------------------------------------------------------------------
@dataclass
class _ParentElement(Element):
    """Element with children for testing visitor traversal."""

    children: list[Element]

    # ----------------------------------------------------------------------
    @override
    def _GetAcceptChildren(self) -> Element._GetAcceptChildrenResultType:
        if not self.children:
            return None
        return ("children", self.children)


# ----------------------------------------------------------------------
class TestElementVisitorHelperDefaultDetailMethodTermination:
    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodTerminatesWhenChildReturnsTerminate(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)

        termination_count = 0

        class TerminatingVisitor(ElementVisitorHelper):
            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                nonlocal termination_count
                termination_count += 1
                yield VisitResult.Terminate

        visitor = TerminatingVisitor()
        method = getattr(visitor, "OnSomeElement__detail")

        result = method([child1, child2], include_disabled=False)

        assert result & VisitResult.Terminate
        assert termination_count == 1

    # ----------------------------------------------------------------------
    def test_DefaultDetailMethodContinuesThroughAllElementsWhenNoTerminate(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        child3 = TerminalElement[int](region, 3)

        visited_count = 0

        class CountingVisitor(ElementVisitorHelper):
            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                nonlocal visited_count
                visited_count += 1
                yield VisitResult.Continue

        visitor = CountingVisitor()
        method = getattr(visitor, "OnSomeElement__detail")

        result = method([child1, child2, child3], include_disabled=False)

        assert result == VisitResult.Continue
        assert visited_count == 3
