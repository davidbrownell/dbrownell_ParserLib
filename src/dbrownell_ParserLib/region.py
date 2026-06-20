# noqa: D100
import inspect

from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Self

from dbrownell_ParserLib.location import Location


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Region:
    """A region within a source file."""

    # ----------------------------------------------------------------------
    filename: Path
    begin: Location
    end: Location

    # ----------------------------------------------------------------------
    @classmethod
    def CreateFromCode(
        cls,
        *,
        callstack_offset: int = 0,
    ) -> Self:
        """Create a `Region` from the current code location."""

        frame = inspect.stack()[callstack_offset + 1][0]
        location = Location(frame.f_lineno, frame.f_lineno)

        return cls(Path(frame.f_code.co_filename), location, location)

    # ----------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.end < self.begin:
            msg = "Invalid region"
            raise ValueError(msg)

    # ----------------------------------------------------------------------
    def __str__(self) -> str:
        return self._string

    # ----------------------------------------------------------------------
    @staticmethod
    def Compare(
        this: Region,
        that: Region,
    ) -> int:
        """Compare two `Region` instances."""

        if this.filename != that.filename:
            return -1 if this.filename < that.filename else 1

        result = Location.Compare(this.begin, that.begin)
        if result != 0:
            return result

        result = Location.Compare(this.end, that.end)
        if result != 0:
            return result

        return 0

    # ----------------------------------------------------------------------
    def __hash__(self) -> int:
        return hash((self.filename, self.begin, self.end))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Region) and self.__class__.Compare(self, other) == 0

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Region) or self.__class__.Compare(self, other) != 0

    def __lt__(self, other: object) -> bool:
        return isinstance(other, Region) and self.__class__.Compare(self, other) < 0

    def __le__(self, other: object) -> bool:
        return isinstance(other, Region) and self.__class__.Compare(self, other) <= 0

    def __gt__(self, other: object) -> bool:
        return isinstance(other, Region) and self.__class__.Compare(self, other) > 0

    def __ge__(self, other: object) -> bool:
        return isinstance(other, Region) and self.__class__.Compare(self, other) >= 0

    # ----------------------------------------------------------------------
    def __contains__(
        self,
        location_or_region: Location | Region,
    ) -> bool:
        if isinstance(location_or_region, Location):
            return self.begin <= location_or_region <= self.end

        region = location_or_region

        if self.filename != region.filename:
            return False

        return self.begin <= region.begin and region.end <= self.end

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @cached_property
    def _string(self) -> str:
        if self.end == self.begin:
            return f"{self.filename.as_posix()}, {self.begin}"

        return f"{self.filename.as_posix()}, {self.begin} - {self.end}"
