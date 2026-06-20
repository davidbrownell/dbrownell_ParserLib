# noqa: D100
from dataclasses import dataclass
from functools import cached_property


# ----------------------------------------------------------------------
@dataclass(frozen=True)
class Location:
    """Location within a source file."""

    # ----------------------------------------------------------------------
    line: int
    column: int

    # ----------------------------------------------------------------------
    def __post_init__(self) -> None:
        if self.line < 1:
            msg = "Invalid line"
            raise ValueError(msg)

        if self.column < 1:
            msg = "Invalid column"
            raise ValueError(msg)

    # ----------------------------------------------------------------------
    def __str__(self) -> str:
        return self._string

    # ----------------------------------------------------------------------
    @staticmethod
    def Compare(
        this: Location,
        that: Location,
    ) -> int:
        """Compare two `Location` objects."""

        result = this.line - that.line
        if result != 0:
            return result

        result = this.column - that.column
        if result != 0:
            return result

        return 0

    # ----------------------------------------------------------------------
    def __hash__(self) -> int:
        return hash((self.line, self.column))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Location) and self.__class__.Compare(self, other) == 0

    def __ne__(self, other: object) -> bool:
        return not isinstance(other, Location) or self.__class__.Compare(self, other) != 0

    def __lt__(self, other: object) -> bool:
        return isinstance(other, Location) and self.__class__.Compare(self, other) < 0

    def __le__(self, other: object) -> bool:
        return isinstance(other, Location) and self.__class__.Compare(self, other) <= 0

    def __gt__(self, other: object) -> bool:
        return isinstance(other, Location) and self.__class__.Compare(self, other) > 0

    def __ge__(self, other: object) -> bool:
        return isinstance(other, Location) and self.__class__.Compare(self, other) >= 0

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @cached_property
    def _string(self) -> str:
        return f"Ln {self.line} Col {self.column}"
