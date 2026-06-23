# noqa: D100
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field, fields, InitVar
from typing import Self, TYPE_CHECKING

from dbrownell_Common.Types import extension, override

from dbrownell_ParserLib.visitors import ExpressionVisitor, ExpressionVisitorHelper, VisitResult

if TYPE_CHECKING:
    from collections.abc import Callable

    from dbrownell_ParserLib.region import Region


# ----------------------------------------------------------------------
@dataclass(eq=False)
class Expression:
    """Abstract base class for all expressions encountered during the parsing process."""

    # ----------------------------------------------------------------------
    # |
    # |  Public Data
    # |
    # ----------------------------------------------------------------------
    region__: Region
    finalize: InitVar[bool] = field(kw_only=True, default=True)

    parent__: Expression | None = field(init=False)

    _unique_id: tuple[object, ...] | None = field(init=False)
    _disabled: bool = field(init=False)

    _finalize_func: Callable[[], None] = field(init=False)

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    def __post_init__(
        self,
        finalize: bool,
    ) -> None:
        self.parent__ = None

        self._unique_id = None
        self._disabled = False

        # ----------------------------------------------------------------------
        def Finalize() -> None:
            visitor = _UniqueIdVisitor(self)

            self.Accept(visitor)

            self._unique_id = visitor.unique_id

        # ----------------------------------------------------------------------

        self._finalize_func = Finalize

        if finalize:
            self._Finalize()

    # ----------------------------------------------------------------------
    @property
    def unique_id__(self) -> tuple[object, ...]:
        """A unique identifier for this expression, which can be used for caching and other purposes."""

        assert self._unique_id is not None
        return self._unique_id

    @property
    def is_disabled__(self) -> bool:
        """Whether this expression is disabled, which can be used for caching and other purposes."""

        return self._disabled

    # ----------------------------------------------------------------------
    def __hash__(self) -> int:
        return hash(self.unique_id__)

    # ----------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Expression):
            return False

        return self.unique_id__ == other.unique_id__

    # ----------------------------------------------------------------------
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Expression):
            return True

        return self.unique_id__ != other.unique_id__

    # ----------------------------------------------------------------------
    def Clone(self, **kwargs) -> Self:
        """Create a copy of this expression, optionally overriding some of its fields."""

        for field_value in fields(self.__class__):
            if field_value.init and field_value.name != "finalize" and field_value.name not in kwargs:
                kwargs[field_value.name] = getattr(self, field_value.name)

        return self.__class__(**kwargs)

    # ----------------------------------------------------------------------
    def Disable(self) -> None:
        """Disable this expression so that it doesn't participate in visitation."""

        assert self.is_disabled__ is False
        self._disabled = True

    # ----------------------------------------------------------------------
    def Accept(  # noqa: C901
        self,
        visitor: ExpressionVisitor,
        *,
        include_disabled: bool = False,
    ) -> VisitResult:
        """Accept a visitor for visitation of this expression and its children (if any)."""

        if self.is_disabled__ and not include_disabled:
            return VisitResult.Continue

        with visitor.OnExpression(self) as expression_visit_result:
            if expression_visit_result & VisitResult.Terminate:
                return expression_visit_result

            if expression_visit_result & VisitResult.SkipAll:
                return VisitResult.Continue

            method_name = f"On{self.__class__.__name__}"

            method = getattr(visitor, method_name, None)
            assert method is not None, method_name

            with method(self) as method_visit_result:
                if method_visit_result & VisitResult.Terminate:
                    return method_visit_result

                # Details
                if not method_visit_result & VisitResult.SkipDetails:
                    all_details = list(self._GenerateAcceptDetails())

                    if all_details:
                        with visitor.OnExpressionDetails(self) as details_visit_result:
                            if details_visit_result & VisitResult.Terminate:
                                return details_visit_result

                            if not details_visit_result & VisitResult.SkipDetails:
                                method_name_prefix = f"On{self.__class__.__name__}__"

                                for detail_name, detail_value in all_details:
                                    method_name = f"{method_name_prefix}{detail_name}"

                                    method = getattr(visitor, method_name, None)
                                    assert method is not None, method_name

                                    detail_visit_result = method(
                                        detail_value, include_disabled=include_disabled
                                    )

                                    if detail_visit_result & VisitResult.Terminate:
                                        return detail_visit_result

                                    if detail_visit_result & VisitResult.SkipDetails:
                                        break

                # Children
                if not method_visit_result & VisitResult.SkipChildren:
                    children_result = self._GetAcceptChildren()

                    if children_result:
                        children_name, children = children_result

                        with visitor.OnExpressionChildren(
                            self,
                            children_name,
                            children,
                        ) as children_visit_result:
                            if children_visit_result & VisitResult.Terminate:
                                return children_visit_result

                            if not children_visit_result & VisitResult.SkipChildren:
                                for child in children:
                                    child_accept_result = child.Accept(
                                        visitor, include_disabled=include_disabled
                                    )

                                    if child_accept_result & VisitResult.Terminate:
                                        return child_accept_result

                                    if child_accept_result & VisitResult.SkipChildren:
                                        break

        return VisitResult.Continue

    # ----------------------------------------------------------------------
    # |
    # |  Protected Types
    # |
    # ----------------------------------------------------------------------
    _GenerateAcceptDetailsResultType = Generator[tuple[str, Self]]
    _GetAcceptChildrenResultType = tuple[str, Iterable[Self]] | None

    # ----------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ----------------------------------------------------------------------
    def _Finalize(self) -> None:
        self._finalize_func()

    # ----------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ----------------------------------------------------------------------
    @extension
    def _GetTerminalUniqueId(self) -> tuple[object, ...]:
        """Get a unique identifier for this expression that doesn't include any of its children."""

        msg = "This functionality should be implemented by a terminal expression (i.e. an expression that doesn't have any children)."
        raise Exception(msg)

    # ----------------------------------------------------------------------
    @extension
    def _GenerateAcceptDetails(self) -> _GenerateAcceptDetailsResultType:
        # Nothing by default
        if False:
            yield

    # ----------------------------------------------------------------------
    @extension
    def _GetAcceptChildren(self) -> _GetAcceptChildrenResultType:
        # Nothing by default
        return None


# ----------------------------------------------------------------------
# |
# |  Private Types
# |
# ----------------------------------------------------------------------
class _UniqueIdVisitor(ExpressionVisitorHelper):
    # ----------------------------------------------------------------------
    def __init__(
        self,
        root_expression: Expression,
    ) -> None:
        self._target_expression = root_expression

        self._child_unique_ids: list[tuple[object, ...]] = []
        self._result: tuple[object, ...] | None = None

    # ----------------------------------------------------------------------
    @property
    def unique_id(self) -> tuple[object, ...]:
        assert self._result is not None
        return self._result

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnExpression(
        self,
        expression: Expression,
    ) -> Generator[VisitResult]:
        if expression is self._target_expression:
            yield VisitResult.Continue

            if not self._child_unique_ids:
                result = expression._GetTerminalUniqueId()  # noqa: SLF001
            else:
                result = tuple(self._child_unique_ids)

            assert self._result is None
            self._result = (type(expression).__name__, *result)

            return

        self._child_unique_ids.append(expression.unique_id__)

        # Do not parse the children of this expression as its unique id already takes that information
        # into account.
        yield VisitResult.SkipChildren
