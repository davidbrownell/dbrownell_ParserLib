# noqa: D100
import weakref

from collections.abc import Generator, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field, fields, InitVar
from typing import Self, TYPE_CHECKING

from dbrownell_Common.Types import extension, override

from dbrownell_ParserLib.visitors import ElementVisitor, ElementVisitorHelper, VisitResult

if TYPE_CHECKING:
    from dbrownell_ParserLib.region import Region


# ----------------------------------------------------------------------
@dataclass(eq=False)
class Element:
    """Abstract base class for all elements encountered during the parsing process."""

    # ----------------------------------------------------------------------
    # |
    # |  Public Data
    # |
    # ----------------------------------------------------------------------
    region__: Region
    finalize: InitVar[bool] = field(kw_only=True, default=True)

    parent__: weakref.ref[Element] | None = field(init=False)

    _unique_id: tuple[object, ...] | None = field(init=False)
    _disabled: bool = field(init=False)

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

        if finalize:
            self._Finalize()

    # ----------------------------------------------------------------------
    @property
    def unique_id__(self) -> tuple[object, ...]:
        """A unique identifier for this element, which can be used for caching and other purposes."""

        assert self._unique_id is not None
        return self._unique_id

    @property
    def is_disabled__(self) -> bool:
        """Whether this element is disabled, which can be used for caching and other purposes."""

        return self._disabled

    # ----------------------------------------------------------------------
    def __hash__(self) -> int:
        return hash(self.unique_id__)

    # ----------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Element):
            return False

        return self.unique_id__ == other.unique_id__

    # ----------------------------------------------------------------------
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Element):
            return True

        return self.unique_id__ != other.unique_id__

    # ----------------------------------------------------------------------
    def Clone(self, **kwargs) -> Self:
        """Create a copy of this element, optionally overriding some of its fields."""

        for field_value in fields(self.__class__):
            if field_value.init and field_value.name != "finalize" and field_value.name not in kwargs:
                kwargs[field_value.name] = getattr(self, field_value.name)

        return self.__class__(**kwargs)

    # ----------------------------------------------------------------------
    def Disable(self) -> None:
        """Disable this element so that it doesn't participate in visitation."""

        assert self.is_disabled__ is False
        self._disabled = True

    # ----------------------------------------------------------------------
    def Accept(  # noqa: C901
        self,
        visitor: ElementVisitor,
        *,
        include_disabled: bool = False,
    ) -> VisitResult:
        """Accept a visitor for visitation of this element and its children (if any)."""

        if self.is_disabled__ and not include_disabled:
            return VisitResult.Continue

        with visitor.OnElement(self) as element_visit_result:
            if element_visit_result & VisitResult.Terminate:
                return element_visit_result

            if element_visit_result & VisitResult.SkipAll:
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
                        with visitor.OnElementDetails(self) as details_visit_result:
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

                        with visitor.OnElementChildren(
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
    _GenerateAcceptDetailsResultType = Generator[tuple[str, Self | list[Self]]]
    _GetAcceptChildrenResultType = tuple[str, Iterable[Self]] | None

    # ----------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ----------------------------------------------------------------------
    def _Finalize(self) -> None:
        visitor = _FinalizeVisitor(self)

        self.Accept(visitor)

        self._unique_id = visitor.unique_id

    # ----------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ----------------------------------------------------------------------
    @extension
    def _GetTerminalUniqueId(self) -> tuple[object, ...]:
        """Get a unique identifier for this element that doesn't include any of its children."""

        msg = f"This functionality should be implemented by a terminal element (i.e. an element that doesn't have any children or element details) [{self.__class__.__name__}]"
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
class _FinalizeVisitor(ElementVisitorHelper):
    """Visitor that visits the children of an element, but not anything below that; it sets the unique_id__ of the target element and sets its children's parent attribute to the correct value."""

    # ----------------------------------------------------------------------
    def __init__(
        self,
        root_element: Element,
    ) -> None:
        self._target_element = root_element

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
    def OnElement(
        self,
        element: Element,
    ) -> Generator[VisitResult]:
        # This code will visit the children of the target element, but not anything below that.
        if element is self._target_element:
            yield VisitResult.Continue

            if not self._child_unique_ids:
                result = element._GetTerminalUniqueId()  # noqa: SLF001
            else:
                result = tuple(self._child_unique_ids)

            assert self._result is None
            self._result = (type(element).__name__, *result)

            return

        element.parent__ = weakref.ref(self._target_element)

        self._child_unique_ids.append(element.unique_id__)

        # Do not parse the grandchildren of the original target element
        yield VisitResult.SkipChildren
