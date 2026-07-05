"""Unit tests for Expression class."""

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast, override

from dbrownell_ParserLib.expression import Expression
from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region
from dbrownell_ParserLib.terminal_expression import TerminalExpression
from dbrownell_ParserLib.visitors import ExpressionVisitorHelper, VisitResult


# ----------------------------------------------------------------------
def _CreateRegion() -> Region:
    return Region(
        filename=Path("test.txt"),
        begin=Location(line=1, column=1),
        end=Location(line=1, column=10),
    )


# ----------------------------------------------------------------------
@dataclass
class _ParentExpressionList(Expression):
    """Expression with children for testing Accept with children as a list."""

    children: list[Expression] = field(default_factory=list)

    # ----------------------------------------------------------------------
    @override
    def _GetAcceptChildren(self) -> Expression._GetAcceptChildrenResultType:
        if not self.children:
            return None
        return ("children", self.children)


# ----------------------------------------------------------------------
@dataclass
class _ParentExpressionDetails(Expression):
    """Expression with children for testing Accept with children as details."""

    child1: Expression
    child2: Expression

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Expression._GenerateAcceptDetailsResultType:
        yield "child1", self.child1
        yield "child2", self.child2


# ----------------------------------------------------------------------
@dataclass
class _DetailExpression(Expression):
    """Expression with details for testing Accept with details."""

    detail_value: TerminalExpression | None = None

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Expression._GenerateAcceptDetailsResultType:
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
class _ListDetailExpression(Expression):
    """Expression with a list of expressions as details for testing Accept with list details."""

    detail_items: list[TerminalExpression] = field(default_factory=list)

    # ----------------------------------------------------------------------
    @override
    def _GenerateAcceptDetails(self) -> Expression._GenerateAcceptDetailsResultType:
        if self.detail_items:
            yield "detail_items", cast(list[Expression], self.detail_items)


# ----------------------------------------------------------------------
class TestExpressionParent:
    # ----------------------------------------------------------------------
    def test_ParentIsNoneByDefault(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert expr.parent__ is None

    # ----------------------------------------------------------------------
    def test_ParentSetForChildrenList(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionList(region, children=[child1, child2])

        assert child1.parent__ is not None and child1.parent__() is parent
        assert child2.parent__ is not None and child2.parent__() is parent
        assert parent.parent__ is None

    # ----------------------------------------------------------------------
    def test_ParentSetForChildrenDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        assert child1.parent__ is not None and child1.parent__() is parent
        assert child2.parent__ is not None and child2.parent__() is parent
        assert parent.parent__ is None


# ----------------------------------------------------------------------
class TestExpressionDisable:
    # ----------------------------------------------------------------------
    def test_NotDisabledByDefault(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert expr.is_disabled__ is False

    # ----------------------------------------------------------------------
    def test_DisableSetsFlag(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        expr.Disable()

        assert expr.is_disabled__ is True


# ----------------------------------------------------------------------
class TestExpressionHash:
    # ----------------------------------------------------------------------
    def test_HashReturnsHashOfUniqueId(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert hash(expr) == hash(expr.unique_id__)

    # ----------------------------------------------------------------------
    def test_HashIsCached(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        result1 = hash(expr)
        result2 = hash(expr)

        assert result1 == result2

    # ----------------------------------------------------------------------
    def test_SameUniqueIdProducesSameHash(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 42)
        expr2 = TerminalExpression[int](region, 42)

        assert hash(expr1) == hash(expr2)

    # ----------------------------------------------------------------------
    def test_DifferentUniqueIdProducesDifferentHash(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 42)
        expr2 = TerminalExpression[int](region, 43)

        assert hash(expr1) != hash(expr2)


# ----------------------------------------------------------------------
class TestExpressionEquality:
    # ----------------------------------------------------------------------
    def test_EqualMethodWithSameUniqueId(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 42)
        expr2 = TerminalExpression[int](region, 42)

        assert Expression.__eq__(expr1, expr2) is True

    # ----------------------------------------------------------------------
    def test_NotEqualWithDifferentUniqueId(self):
        region = _CreateRegion()
        expr1 = TerminalExpression[int](region, 42)
        expr2 = TerminalExpression[int](region, 43)

        assert expr1 != expr2

    # ----------------------------------------------------------------------
    def test_EqualReturnsFalseForNonExpression(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert (expr == "string") is False
        assert (expr == 42) is False
        assert (expr == None) is False

    # ----------------------------------------------------------------------
    def test_NotEqualReturnsTrueForNonExpression(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        assert (expr != "string") is True
        assert (expr != 42) is True
        assert (expr != None) is True


# ----------------------------------------------------------------------
class TestExpressionAccept:
    # ----------------------------------------------------------------------
    def test_AcceptCallsOnExpression(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is expr

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDisabledByDefault(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        expr.Disable()

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 0

    # ----------------------------------------------------------------------
    def test_AcceptIncludesDisabledWhenRequested(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)
        expr.Disable()

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor, include_disabled=True)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is expr

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesOnTerminate(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                yield VisitResult.Terminate

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Terminate

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnMethodNameReturnsTerminate(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                yield VisitResult.Terminate

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Terminate

    # ----------------------------------------------------------------------
    def test_AcceptWithChildren(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionList(region, children=[child1, child2])

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionList(self, expression: _ParentExpressionList):
                yield VisitResult.Continue

            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 3
        assert visited_expressions[0] is parent
        assert visited_expressions[1] is child1
        assert visited_expressions[2] is child2

    # ----------------------------------------------------------------------
    def test_AcceptSkipsChildrenOnSkipChildren(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionList(region, children=[child1, child2])

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionList(self, expression: _ParentExpressionList):
                yield VisitResult.SkipChildren

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptSkipsAllOnSkipAll(self):
        region = _CreateRegion()
        child = TerminalExpression[int](region, 1)
        parent = _ParentExpressionList(region, children=[child])

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.SkipAll

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptWithDetails(self):
        region = _CreateRegion()
        detail = TerminalExpression[int](region, 99)
        expr = _DetailExpression(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_DetailExpression(self, expression: _DetailExpression):
                yield VisitResult.Continue

            def On_DetailExpression__detail_value(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                expression.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == ["detail_value"]

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDetailsOnSkipDetails(self):
        region = _CreateRegion()
        detail = TerminalExpression[int](region, 99)
        expr = _DetailExpression(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_DetailExpression(self, expression: _DetailExpression):
                yield VisitResult.SkipDetails

            def On_DetailExpression__detail_value(
                self,
                expressions: list[TerminalExpression],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnExpressionDetailsReturnsTerminate(self):
        region = _CreateRegion()
        detail = TerminalExpression[int](region, 99)
        expr = _DetailExpression(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_DetailExpression(self, expression: _DetailExpression):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnExpressionDetails(self, expression: Expression):
                yield VisitResult.Terminate

            def On_DetailExpression__detail_value(
                self,
                expressions: list[TerminalExpression],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Terminate
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenDetailMethodReturnsTerminate(self):
        region = _CreateRegion()
        detail = TerminalExpression[int](region, 99)
        expr = _DetailExpression(region, detail_value=detail)

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_DetailExpression(self, expression: _DetailExpression):
                yield VisitResult.Continue

            def On_DetailExpression__detail_value(
                self,
                expressions: list[TerminalExpression],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                return VisitResult.Terminate

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Terminate

    # ----------------------------------------------------------------------
    def test_AcceptSkipsRemainingDetailsWhenDetailMethodReturnsSkipDetails(self):
        region = _CreateRegion()
        detail = TerminalExpression[int](region, 99)
        expr = _DetailExpression(region, detail_value=detail)

        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_DetailExpression(self, expression: _DetailExpression):
                yield VisitResult.Continue

            def On_DetailExpression__detail_value(
                self,
                expressions: list[TerminalExpression],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("detail_value")
                return VisitResult.SkipDetails

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_details == ["detail_value"]

    # ----------------------------------------------------------------------
    def test_AcceptWithListDetails(self):
        region = _CreateRegion()
        item1 = TerminalExpression[int](region, 1)
        item2 = TerminalExpression[int](region, 2)
        item3 = TerminalExpression[int](region, 3)
        expr = _ListDetailExpression(region, detail_items=[item1, item2, item3])

        visited_items: list[int] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_ListDetailExpression(self, expression: _ListDetailExpression):
                yield VisitResult.Continue

            def On_ListDetailExpression__detail_items(
                self,
                expressions: list[TerminalExpression],
                *,
                include_disabled: bool,
            ) -> VisitResult:
                for item in expressions:
                    visited_items.append(item.value)
                    item.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = expr.Accept(visitor)

        assert result == VisitResult.Continue
        assert visited_items == [1, 2, 3]

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnExpressionChildrenReturnsTerminate(self):
        region = _CreateRegion()
        child = TerminalExpression[int](region, 1)
        parent = _ParentExpressionList(region, children=[child])

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionList(self, expression: _ParentExpressionList):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnExpressionChildren(self, expression, children_name, children):
                yield VisitResult.Terminate

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptSkipsChildrenWhenOnExpressionChildrenReturnsSkipChildren(self):
        region = _CreateRegion()
        child = TerminalExpression[int](region, 1)
        parent = _ParentExpressionList(region, children=[child])

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionList(self, expression: _ParentExpressionList):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnExpressionChildren(self, expression, children_name, children):
                yield VisitResult.SkipChildren

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenChildVisitationReturnsTerminate(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionList(region, children=[child1, child2])

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                if expression is child1:
                    yield VisitResult.Terminate
                else:
                    yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionList(self, expression: _ParentExpressionList):
                yield VisitResult.Continue

            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert len(visited_expressions) == 2
        assert visited_expressions[0] is parent
        assert visited_expressions[1] is child1

    # ----------------------------------------------------------------------
    def test_AcceptWithChildrenDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_expressions: list[Expression] = []
        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionDetails(self, expression: _ParentExpressionDetails):
                yield VisitResult.Continue

            def On_ParentExpressionDetails__child1(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                expression.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            def On_ParentExpressionDetails__child2(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                expression.Accept(self, include_disabled=include_disabled)
                return VisitResult.Continue

            @contextmanager
            def OnTerminalExpression(self, expression: TerminalExpression):
                yield VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 3
        assert visited_expressions[0] is parent
        assert visited_expressions[1] is child1
        assert visited_expressions[2] is child2
        assert visited_details == ["child1", "child2"]

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDetailsOnSkipDetailsForParentExpressionDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_expressions: list[Expression] = []
        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionDetails(self, expression: _ParentExpressionDetails):
                yield VisitResult.SkipDetails

            def On_ParentExpressionDetails__child1(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Continue

            def On_ParentExpressionDetails__child2(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptSkipsAllOnSkipAllForParentExpressionDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_expressions: list[Expression] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.SkipAll

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenOnExpressionDetailsReturnsTerminateForParentExpressionDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_expressions: list[Expression] = []
        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionDetails(self, expression: _ParentExpressionDetails):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnExpressionDetails(self, expression: Expression):
                yield VisitResult.Terminate

            def On_ParentExpressionDetails__child1(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Continue

            def On_ParentExpressionDetails__child2(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Terminate
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptSkipsDetailsWhenOnExpressionDetailsReturnsSkipDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_expressions: list[Expression] = []
        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @override
            @contextmanager
            def OnExpression(self, expression: Expression):
                visited_expressions.append(expression)
                yield VisitResult.Continue

            @contextmanager
            def On_ParentExpressionDetails(self, expression: _ParentExpressionDetails):
                yield VisitResult.Continue

            @override
            @contextmanager
            def OnExpressionDetails(self, expression: Expression):
                yield VisitResult.SkipDetails

            def On_ParentExpressionDetails__child1(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Continue

            def On_ParentExpressionDetails__child2(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child2")
                return VisitResult.Continue

        visitor = TestVisitor()
        result = parent.Accept(visitor)

        assert result == VisitResult.Continue
        assert len(visited_expressions) == 1
        assert visited_expressions[0] is parent
        assert visited_details == []

    # ----------------------------------------------------------------------
    def test_AcceptTerminatesWhenDetailMethodReturnsTerminateForParentExpressionDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_ParentExpressionDetails(self, expression: _ParentExpressionDetails):
                yield VisitResult.Continue

            def On_ParentExpressionDetails__child1(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.Terminate

            def On_ParentExpressionDetails__child2(
                self,
                expression: TerminalExpression,
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
    def test_AcceptSkipsRemainingDetailsWhenDetailMethodReturnsSkipDetailsForParentExpressionDetails(self):
        region = _CreateRegion()
        child1 = TerminalExpression[int](region, 1)
        child2 = TerminalExpression[int](region, 2)
        parent = _ParentExpressionDetails(region, child1, child2)

        visited_details: list[str] = []

        class TestVisitor(ExpressionVisitorHelper):
            @contextmanager
            def On_ParentExpressionDetails(self, expression: _ParentExpressionDetails):
                yield VisitResult.Continue

            def On_ParentExpressionDetails__child1(
                self,
                expression: TerminalExpression,
                *,
                include_disabled: bool,
            ) -> VisitResult:
                visited_details.append("child1")
                return VisitResult.SkipDetails

            def On_ParentExpressionDetails__child2(
                self,
                expression: TerminalExpression,
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
class TestExpressionClone:
    # ----------------------------------------------------------------------
    def test_ClonePreservesRegion(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        cloned = expr.Clone()

        assert cloned.region__ == region

    # ----------------------------------------------------------------------
    def test_CloneCreatesIndependentInstance(self):
        region = _CreateRegion()
        expr = TerminalExpression[int](region, 42)

        cloned = expr.Clone()

        assert expr is not cloned
        assert expr.unique_id__ == cloned.unique_id__

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
