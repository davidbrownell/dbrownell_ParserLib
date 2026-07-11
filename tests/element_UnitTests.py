"""Unit tests for Element class."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast, override

from dbrownell_ParserLib.element import Element
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_element import TerminalElement
from dbrownell_ParserLib.visitors import ElementVisitorHelper, VisitResult


# ----------------------------------------------------------------------
def _CreateRegion() -> Region:
    return Region(
        filename=Path("test.txt"),
        begin=Location(line=1, column=1),
        end=Location(line=1, column=10),
    )


# ----------------------------------------------------------------------
@dataclass
class _ParentElementList(Element):
    """Element with children for testing Accept with children as a list."""

    children: list[Element] = field(default_factory=list)

    # ----------------------------------------------------------------------
    @override
    def _GetAcceptChildren(self) -> Element._GetAcceptChildrenResultType:
        if not self.children:
            return None
        return ("children", self.children)


# ----------------------------------------------------------------------
@dataclass
class _ParentElementDetails(Element):
    """Element with children for testing Accept with children as details."""

    child1: Element
    child2: Element

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Element._GenerateAcceptDetailsResultType:
        yield "child1", self.child1
        yield "child2", self.child2


# ----------------------------------------------------------------------
@dataclass
class _DetailElement(Element):
    """Element with details for testing Accept with details."""

    detail_value: TerminalElement | None = None

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Element._GenerateAcceptDetailsResultType:
        if self.detail_value is not None:
            yield "detail_value", self.detail_value

    # ----------------------------------------------------------------------
    @override
    def _GetTerminalUniqueId(self) -> tuple[object, ...]:
        if self.detail_value is None:
            return ("no_detail",)
        return ("with_detail",)


# ----------------------------------------------------------------------
@dataclass
class _ListDetailElement(Element):
    """Element with a list of elements as details for testing Accept with list details."""

    detail_items: list[TerminalElement] = field(default_factory=list)

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Element._GenerateAcceptDetailsResultType:
        if self.detail_items:
            yield "detail_items", cast(list[Element], self.detail_items)


# ----------------------------------------------------------------------
class TestElementParent:
    # ----------------------------------------------------------------------
    def test_ParentIsNoneByDefault(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert element.parent__ is None

    # ----------------------------------------------------------------------
    def test_ParentSetForChildrenList(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementList(region, children=[child1, child2])

        assert child1.parent__ is not None and child1.parent__() is parent
        assert child2.parent__ is not None and child2.parent__() is parent
        assert parent.parent__ is None

    # ----------------------------------------------------------------------
    def test_ParentSetForChildrenDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        assert child1.parent__ is not None and child1.parent__() is parent
        assert child2.parent__ is not None and child2.parent__() is parent
        assert parent.parent__ is None


# ----------------------------------------------------------------------
class TestElementDisable:
    # ----------------------------------------------------------------------
    def test_NotDisabledByDefault(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert element.is_disabled__ is False

    # ----------------------------------------------------------------------
    def test_DisableSetsFlag(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        element.Disable()

        assert element.is_disabled__ is True


# ----------------------------------------------------------------------
class TestElementHash:
    # ----------------------------------------------------------------------
    def test_HashReturnsHashOfUniqueId(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert hash(element) == hash(element.unique_id__)

    # ----------------------------------------------------------------------
    def test_HashIsCached(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        result1 = hash(element)
        result2 = hash(element)

        assert result1 == result2

    # ----------------------------------------------------------------------
    def test_SameUniqueIdProducesSameHash(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 42)
        element2 = TerminalElement[int](region, 42)

        assert hash(element1) == hash(element2)

    # ----------------------------------------------------------------------
    def test_DifferentUniqueIdProducesDifferentHash(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 42)
        element2 = TerminalElement[int](region, 43)

        assert hash(element1) != hash(element2)


# ----------------------------------------------------------------------
class TestElementEquality:
    # ----------------------------------------------------------------------
    def test_EqualMethodWithSameUniqueId(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 42)
        element2 = TerminalElement[int](region, 42)

        assert Element.__eq__(element1, element2) is True

    # ----------------------------------------------------------------------
    def test_NotEqualWithDifferentUniqueId(self):
        region = _CreateRegion()
        element1 = TerminalElement[int](region, 42)
        element2 = TerminalElement[int](region, 43)

        assert element1 != element2

    # ----------------------------------------------------------------------
    def test_EqualReturnsFalseForNonElement(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert (element == "string") is False
        assert (element == 42) is False
        assert (element == None) is False

    # ----------------------------------------------------------------------
    def test_NotEqualReturnsTrueForNonElement(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        assert (element != "string") is True
        assert (element != 42) is True
        assert (element != None) is True


# ----------------------------------------------------------------------
class TestElementAccept:
    # ----------------------------------------------------------------------
    def test_AcceptCallsOnElement(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is element

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDisabledByDefault(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        element.Disable()

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 0

    # ----------------------------------------------------------------------
    def test_AcceptIncludesDisabledWhenRequested(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)
        element.Disable()

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor, include_disabled=True)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is element

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesOnTerminate(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                yield VisitResult.Terminate

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Terminate

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnMethodNameReturnsTerminate(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                yield VisitResult.Terminate

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Terminate

    # ----------------------------------------------------------------------
    def test_AcceptWithChildren(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementList(region, children=[child1, child2])

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementList(self, element: _ParentElementList):
                yield VisitResult.Continue

            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 3
        assert visited_elements[0] is parent
        assert visited_elements[1] is child1
        assert visited_elements[2] is child2

    # ----------------------------------------------------------------------
    def test_AcceptSkipsChildrenOnSkipChildren(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementList(region, children=[child1, child2])

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementList(self, element: _ParentElementList):
                yield VisitResult.SkipChildren

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptSkipsAllOnSkipAll(self):
        region = _CreateRegion()
        child = TerminalElement[int](region, 1)
        parent = _ParentElementList(region, children=[child])

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.SkipAll

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptWithDetails(self):
        region = _CreateRegion()
        detail = TerminalElement[int](region, 99)
        element = _DetailElement(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_DetailElement(self, element: _DetailElement):
                yield VisitResult.Continue

            def On_DetailElement__detail_value(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                element.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == ["detail_value"]

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDetailsOnSkipDetails(self):
        region = _CreateRegion()
        detail = TerminalElement[int](region, 99)
        element = _DetailElement(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_DetailElement(self, element: _DetailElement):
                yield VisitResult.SkipDetails

            def On_DetailElement__detail_value(
                self,
                elements: list[TerminalElement],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnElementDetailsReturnsTerminate(self):
        region = _CreateRegion()
        detail = TerminalElement[int](region, 99)
        element = _DetailElement(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_DetailElement(self, element: _DetailElement):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnElementDetails(self, element: Element):
                yield VisitResult.Terminate

            def On_DetailElement__detail_value(
                self,
                elements: list[TerminalElement],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Terminate
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenDetailMethodReturnsTerminate(self):
        region = _CreateRegion()
        detail = TerminalElement[int](region, 99)
        element = _DetailElement(region, detail_value=detail)

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_DetailElement(self, element: _DetailElement):
                yield VisitResult.Continue

            def On_DetailElement__detail_value(
                self,
                elements: list[TerminalElement],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                return VisitResult.Terminate

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Terminate

    # ----------------------------------------------------------------------
    def test_AcceptSkipsRemainingDetailsWhenDetailMethodReturnsSkipDetails(self):
        region = _CreateRegion()
        detail = TerminalElement[int](region, 99)
        element = _DetailElement(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_DetailElement(self, element: _DetailElement):
                yield VisitResult.Continue

            def On_DetailElement__detail_value(
                self,
                elements: list[TerminalElement],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                return VisitResult.SkipDetails

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == ["detail_value"]

    # ----------------------------------------------------------------------
    def test_AcceptWithListDetails(self):
        region = _CreateRegion()
        item1 = TerminalElement[int](region, 1)
        item2 = TerminalElement[int](region, 2)
        item3 = TerminalElement[int](region, 3)
        element = _ListDetailElement(region, detail_items=[item1, item2, item3])

        visited_items: list[int] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_ListDetailElement(self, element: _ListDetailElement):
                yield VisitResult.Continue

            def On_ListDetailElement__detail_items(
                self,
                elements: list[TerminalElement],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                for item in elements:
                    visited_items.append(item.value)
                    item.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = element.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_items == [1, 2, 3]

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnElementChildrenReturnsTerminate(self):
        region = _CreateRegion()
        child = TerminalElement[int](region, 1)
        parent = _ParentElementList(region, children=[child])

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementList(self, element: _ParentElementList):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnElementChildren(self, element, children_name, children):
                yield VisitResult.Terminate

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptSkipsChildrenWhenOnElementChildrenReturnsSkipChildren(self):
        region = _CreateRegion()
        child = TerminalElement[int](region, 1)
        parent = _ParentElementList(region, children=[child])

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementList(self, element: _ParentElementList):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnElementChildren(self, element, children_name, children):
                yield VisitResult.SkipChildren

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenChildVisitationReturnsTerminate(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementList(region, children=[child1, child2])

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                if element is child1:
                    yield VisitResult.Terminate
                else:
                    yield VisitResult.Continue

            @contextmanager
            def On_ParentElementList(self, element: _ParentElementList):
                yield VisitResult.Continue

            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert len(visited_elements) == 2
        assert visited_elements[0] is parent
        assert visited_elements[1] is child1

    # ----------------------------------------------------------------------
    def test_AcceptWithChildrenDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_elements: list[Element] = []
        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementDetails(self, element: _ParentElementDetails):
                yield VisitResult.Continue

            def On_ParentElementDetails__child1(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                element.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            def On_ParentElementDetails__child2(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                element.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            @contextmanager
            def OnTerminalElement(self, element: TerminalElement):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 3
        assert visited_elements[0] is parent
        assert visited_elements[1] is child1
        assert visited_elements[2] is child2
        assert visited_details == ["child1", "child2"]

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDetailsOnSkipDetailsForParentElementDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_elements: list[Element] = []
        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementDetails(self, element: _ParentElementDetails):
                yield VisitResult.SkipDetails

            def On_ParentElementDetails__child1(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Continue

            def On_ParentElementDetails__child2(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptSkipsAllOnSkipAllForParentElementDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_elements: list[Element] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.SkipAll

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnElementDetailsReturnsTerminateForParentElementDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_elements: list[Element] = []
        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementDetails(self, element: _ParentElementDetails):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnElementDetails(self, element: Element):
                yield VisitResult.Terminate

            def On_ParentElementDetails__child1(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Continue

            def On_ParentElementDetails__child2(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDetailsWhenOnElementDetailsReturnsSkipDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_elements: list[Element] = []
        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @override
            @contextmanager
            def OnElement(self, element: Element):
                visited_elements.append(element)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentElementDetails(self, element: _ParentElementDetails):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnElementDetails(self, element: Element):
                yield VisitResult.SkipDetails

            def On_ParentElementDetails__child1(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Continue

            def On_ParentElementDetails__child2(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_elements) == 1
        assert visited_elements[0] is parent
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenDetailMethodReturnsTerminateForParentElementDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_ParentElementDetails(self, element: _ParentElementDetails):
                yield VisitResult.Continue

            def On_ParentElementDetails__child1(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Terminate

            def On_ParentElementDetails__child2(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert visited_details == ["child1"]

    # ----------------------------------------------------------------------
    def test_AcceptSkipsRemainingDetailsWhenDetailMethodReturnsSkipDetailsForParentElementDetails(self):
        region = _CreateRegion()
        child1 = TerminalElement[int](region, 1)
        child2 = TerminalElement[int](region, 2)
        parent = _ParentElementDetails(region, child1, child2)

        visited_details: list[str] = []

        class TestVisitor(ElementVisitorHelper):
            @contextmanager
            def On_ParentElementDetails(self, element: _ParentElementDetails):
                yield VisitResult.Continue

            def On_ParentElementDetails__child1(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.SkipDetails

            def On_ParentElementDetails__child2(
                self,
                element: TerminalElement,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == ["child1"]


# ----------------------------------------------------------------------
class TestElementClone:
    # ----------------------------------------------------------------------
    def test_ClonePreservesRegion(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        cloned = element.Clone()

        assert cloned.region__ == region

    # ----------------------------------------------------------------------
    def test_CloneCreatesIndependentInstance(self):
        region = _CreateRegion()
        element = TerminalElement[int](region, 42)

        cloned = element.Clone()

        assert element is not cloned
        assert element.unique_id__ == cloned.unique_id__

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
