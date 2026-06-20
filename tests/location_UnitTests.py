"""Unit tests for Location class."""

import pytest

from dbrownell_ParserLib.location import Location


# ----------------------------------------------------------------------
class TestLocationConstruction:
    # ----------------------------------------------------------------------
    def test_ValidLocation(self):
        loc = Location(line=1, column=1)

        assert loc.line == 1
        assert loc.column == 1

    # ----------------------------------------------------------------------
    def test_InvalidLineZero(self):
        with pytest.raises(ValueError, match="Invalid line"):
            Location(line=0, column=1)

    # ----------------------------------------------------------------------
    def test_InvalidLineNegative(self):
        with pytest.raises(ValueError, match="Invalid line"):
            Location(line=-5, column=1)

    # ----------------------------------------------------------------------
    def test_InvalidColumnZero(self):
        with pytest.raises(ValueError, match="Invalid column"):
            Location(line=1, column=0)

    # ----------------------------------------------------------------------
    def test_InvalidColumnNegative(self):
        with pytest.raises(ValueError, match="Invalid column"):
            Location(line=1, column=-3)


# ----------------------------------------------------------------------
class TestLocationStr:
    # ----------------------------------------------------------------------
    def test_Str(self):
        loc = Location(line=10, column=25)

        assert str(loc) == "Ln 10 Col 25"

    # ----------------------------------------------------------------------
    def test_StrSingleDigits(self):
        loc = Location(line=1, column=1)

        assert str(loc) == "Ln 1 Col 1"


# ----------------------------------------------------------------------
class TestLocationCompare:
    # ----------------------------------------------------------------------
    def test_EqualLocations(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert Location.Compare(loc1, loc2) == 0

    # ----------------------------------------------------------------------
    def test_FirstLineLess(self):
        loc1 = Location(line=3, column=10)
        loc2 = Location(line=5, column=10)

        assert Location.Compare(loc1, loc2) < 0

    # ----------------------------------------------------------------------
    def test_FirstLineGreater(self):
        loc1 = Location(line=7, column=10)
        loc2 = Location(line=5, column=10)

        assert Location.Compare(loc1, loc2) > 0

    # ----------------------------------------------------------------------
    def test_SameLineFirstColumnLess(self):
        loc1 = Location(line=5, column=3)
        loc2 = Location(line=5, column=10)

        assert Location.Compare(loc1, loc2) < 0

    # ----------------------------------------------------------------------
    def test_SameLineFirstColumnGreater(self):
        loc1 = Location(line=5, column=15)
        loc2 = Location(line=5, column=10)

        assert Location.Compare(loc1, loc2) > 0


# ----------------------------------------------------------------------
class TestLocationHash:
    # ----------------------------------------------------------------------
    def test_EqualLocationsHaveSameHash(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert hash(loc1) == hash(loc2)

    # ----------------------------------------------------------------------
    def test_DifferentLocationsCanHaveDifferentHash(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=11)

        assert hash(loc1) != hash(loc2)

    # ----------------------------------------------------------------------
    def test_UsableInSet(self):
        loc1 = Location(line=1, column=1)
        loc2 = Location(line=1, column=1)
        loc3 = Location(line=2, column=1)

        s = {loc1, loc2, loc3}

        assert len(s) == 2


# ----------------------------------------------------------------------
class TestLocationEquality:
    # ----------------------------------------------------------------------
    def test_Equal(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 == loc2

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentLine(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=6, column=10)

        assert not (loc1 == loc2)

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentColumn(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=11)

        assert not (loc1 == loc2)

    # ----------------------------------------------------------------------
    def test_NotEqualNonLocation(self):
        loc = Location(line=5, column=10)

        assert not (loc == "not a location")
        assert not (loc == None)
        assert not (loc == 5)


# ----------------------------------------------------------------------
class TestLocationInequality:
    # ----------------------------------------------------------------------
    def test_NotEqualDifferentLine(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=6, column=10)

        assert loc1 != loc2

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentColumn(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=11)

        assert loc1 != loc2

    # ----------------------------------------------------------------------
    def test_EqualLocationsNotUnequal(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert not (loc1 != loc2)

    # ----------------------------------------------------------------------
    def test_NotEqualNonLocation(self):
        loc = Location(line=5, column=10)

        assert loc != "not a location"
        assert loc != None
        assert loc != 5


# ----------------------------------------------------------------------
class TestLocationLessThan:
    # ----------------------------------------------------------------------
    def test_LessThanByLine(self):
        loc1 = Location(line=3, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 < loc2

    # ----------------------------------------------------------------------
    def test_LessThanByColumn(self):
        loc1 = Location(line=5, column=3)
        loc2 = Location(line=5, column=10)

        assert loc1 < loc2

    # ----------------------------------------------------------------------
    def test_NotLessThanWhenEqual(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert not (loc1 < loc2)

    # ----------------------------------------------------------------------
    def test_NotLessThanWhenGreater(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=3, column=10)

        assert not (loc1 < loc2)

    # ----------------------------------------------------------------------
    def test_NotLessThanNonLocation(self):
        loc = Location(line=5, column=10)

        assert not (loc < "not a location")


# ----------------------------------------------------------------------
class TestLocationLessThanOrEqual:
    # ----------------------------------------------------------------------
    def test_LessThanOrEqualByLine(self):
        loc1 = Location(line=3, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 <= loc2

    # ----------------------------------------------------------------------
    def test_LessThanOrEqualByColumn(self):
        loc1 = Location(line=5, column=3)
        loc2 = Location(line=5, column=10)

        assert loc1 <= loc2

    # ----------------------------------------------------------------------
    def test_LessThanOrEqualWhenEqual(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 <= loc2

    # ----------------------------------------------------------------------
    def test_NotLessThanOrEqualWhenGreater(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=3, column=10)

        assert not (loc1 <= loc2)

    # ----------------------------------------------------------------------
    def test_NotLessThanOrEqualNonLocation(self):
        loc = Location(line=5, column=10)

        assert not (loc <= "not a location")


# ----------------------------------------------------------------------
class TestLocationGreaterThan:
    # ----------------------------------------------------------------------
    def test_GreaterThanByLine(self):
        loc1 = Location(line=7, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 > loc2

    # ----------------------------------------------------------------------
    def test_GreaterThanByColumn(self):
        loc1 = Location(line=5, column=15)
        loc2 = Location(line=5, column=10)

        assert loc1 > loc2

    # ----------------------------------------------------------------------
    def test_NotGreaterThanWhenEqual(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert not (loc1 > loc2)

    # ----------------------------------------------------------------------
    def test_NotGreaterThanWhenLess(self):
        loc1 = Location(line=3, column=10)
        loc2 = Location(line=5, column=10)

        assert not (loc1 > loc2)

    # ----------------------------------------------------------------------
    def test_NotGreaterThanNonLocation(self):
        loc = Location(line=5, column=10)

        assert not (loc > "not a location")


# ----------------------------------------------------------------------
class TestLocationGreaterThanOrEqual:
    # ----------------------------------------------------------------------
    def test_GreaterThanOrEqualByLine(self):
        loc1 = Location(line=7, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 >= loc2

    # ----------------------------------------------------------------------
    def test_GreaterThanOrEqualByColumn(self):
        loc1 = Location(line=5, column=15)
        loc2 = Location(line=5, column=10)

        assert loc1 >= loc2

    # ----------------------------------------------------------------------
    def test_GreaterThanOrEqualWhenEqual(self):
        loc1 = Location(line=5, column=10)
        loc2 = Location(line=5, column=10)

        assert loc1 >= loc2

    # ----------------------------------------------------------------------
    def test_NotGreaterThanOrEqualWhenLess(self):
        loc1 = Location(line=3, column=10)
        loc2 = Location(line=5, column=10)

        assert not (loc1 >= loc2)

    # ----------------------------------------------------------------------
    def test_NotGreaterThanOrEqualNonLocation(self):
        loc = Location(line=5, column=10)

        assert not (loc >= "not a location")
