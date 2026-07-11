"""Contains types related to Element visitation."""

import types

from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import auto, Flag
from typing import override, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from dbrownell_ParserLib.element import Element


# ----------------------------------------------------------------------
class VisitResult(Flag):
    """Result returned during visitation that controls the flow of the visitation process."""

    Continue = 0
    """Continue visiting the rest of the elements as normal."""

    SkipDetails = auto()
    """Skip visiting the details of this element, but continue visiting the rest of the elements as normal."""

    SkipChildren = auto()
    """Skip visiting the children of this element, but continue visiting the rest of the elements as normal."""

    Terminate = auto()
    """Terminate the visitation process immediately."""

    # Amalgamations
    SkipAll = SkipDetails | SkipChildren


# ----------------------------------------------------------------------
class ElementVisitor(ABC):
    """Abstract base class for a visitor that accepts Elements."""

    # ----------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def OnElement(
        self,
        element: Element,
    ) -> Generator[VisitResult]:
        """Call for every element."""

        raise NotImplementedError("Abstract method")  # noqa: EM101  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def OnElementDetails(
        self,
        element: Element,
    ) -> Generator[VisitResult]:
        """Call when visiting the details of an element."""

        raise NotImplementedError("Abstract method")  # noqa: EM101  # pragma: no cover

    # ----------------------------------------------------------------------
    @abstractmethod
    @contextmanager
    def OnElementChildren(
        self,
        element: Element,
        children_name: str,
        children: Iterable[Element],
    ) -> Generator[VisitResult]:
        """Call when visiting the children of an element."""

        raise NotImplementedError("Abstract method")  # noqa: EM101  # pragma: no cover

    # ----------------------------------------------------------------------
    # Derived classes should implement the following methods:
    #
    #   @contextmanager
    #   def On<Element Name>(self, element: <Element Name>) -> Generator[VisitResult]:
    #       ...
    #
    #   def On<Element Name>__<Detail Name>(self, element_or_elements: <Element Name> | list[<Element Name>], include_disabled: bool) -> VisitResult:
    #       ...
    #


# ----------------------------------------------------------------------
class ElementVisitorHelper(ElementVisitor):
    """Base class that makes writing custom visitors easier by providing default behavior for visitation methods."""

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnElement(
        self,
        element: Element,
    ) -> Generator[VisitResult]:
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnElementDetails(
        self,
        element: Element,
    ) -> Generator[VisitResult]:
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @override
    @contextmanager
    def OnElementChildren(
        self,
        element: Element,
        children_name: str,
        children: Iterable[Element],
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
                return self.__class__._DefaultElementMethod  # noqa: SLF001

        raise AttributeError(method_name)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @contextmanager
    def _DefaultElementMethod(*args, **kwargs) -> Generator[VisitResult]:  # noqa: ARG004
        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    def _DefaultDetailMethod(
        self,
        element_or_elements: Element | list[Element],
        *,
        include_disabled: bool,
    ) -> VisitResult:
        elements: list[Element] = (  # ty: ignore[invalid-assignment]
            element_or_elements if isinstance(element_or_elements, list) else [element_or_elements]
        )

        for element in elements:
            result = element.Accept(self, include_disabled=include_disabled)
            if result & VisitResult.Terminate:
                return result

        return VisitResult.Continue
