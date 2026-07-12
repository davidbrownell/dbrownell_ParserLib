# noqa: D100
from contextlib import contextmanager
from typing import override, TYPE_CHECKING

from dbrownell_Common.ContextlibEx import ExitStack
from dbrownell_Common.Streams.StreamDecorator import StreamDecorator

from dbrownell_ParserLib.terminal_element import TerminalElement
from dbrownell_ParserLib.visitors import ElementVisitorHelper, VisitResult

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable
    from typing import TextIO

    from dbrownell_ParserLib.element import Element


# ----------------------------------------------------------------------
class TestVisitor(ElementVisitorHelper):
    """Visitor that writes the element names and region information to the provided stream."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    # ----------------------------------------------------------------------
    def __init__(self, output: TextIO) -> None:
        self._streams: list[StreamDecorator] = [
            StreamDecorator(output),
        ]

    # ----------------------------------------------------------------------
    @contextmanager
    @override
    def OnElement(self, element: Element) -> Generator[VisitResult]:
        self._streams[-1].write(f"{element.__class__.__name__}, {element.region__.begin}")

        if element.region__.end != element.region__.begin:
            self._streams[-1].write(f" - {element.region__.end}")

        if isinstance(element, TerminalElement):
            self._streams[-1].write(f" -> '{element.value}' [{type(element.value).__name__}]")

        self._streams[-1].write("\n")

        yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @contextmanager
    @override
    def OnElementDetails(self, element: Element) -> Generator[VisitResult]:
        self._streams[-1].write("  <<details>>\n")

        self._streams.append(StreamDecorator(self._streams[-1], "    "))
        with ExitStack(self._streams.pop):
            yield VisitResult.Continue

    # ----------------------------------------------------------------------
    @contextmanager
    @override
    def OnElementChildren(
        self,
        element: Element,
        children_name: str,
        children: Iterable[Element],
    ) -> Generator[VisitResult]:
        self._streams[-1].write(f"  <<children: {children_name}>>\n")

        self._streams.append(StreamDecorator(self._streams[-1], "    "))
        with ExitStack(self._streams.pop):
            yield VisitResult.Continue
