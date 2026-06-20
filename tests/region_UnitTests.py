"""Unit tests for Region class."""

from pathlib import Path

import pytest

from dbrownell_ParserLib.location import Location
from dbrownell_ParserLib.region import Region


# ----------------------------------------------------------------------
class TestRegionConstruction:
    # ----------------------------------------------------------------------
    def test_ValidRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert region.filename == filename
        assert region.begin == begin
        assert region.end == end

    # ----------------------------------------------------------------------
    def test_SameBeginAndEnd(self):
        filename = Path("test.txt")
        loc = Location(line=3, column=5)

        region = Region(filename=filename, begin=loc, end=loc)

        assert region.begin == region.end

    # ----------------------------------------------------------------------
    def test_InvalidRegionEndBeforeBegin(self):
        filename = Path("test.txt")
        begin = Location(line=10, column=5)
        end = Location(line=5, column=1)

        with pytest.raises(ValueError, match="Invalid region"):
            Region(filename=filename, begin=begin, end=end)


# ----------------------------------------------------------------------
class TestRegionCreateFromCode:
    # ----------------------------------------------------------------------
    def test_CreateFromCode(self):
        region = Region.CreateFromCode()

        assert region.filename == Path(__file__)
        assert region.begin.line == region.end.line
        assert region.begin.column == region.end.column

    # ----------------------------------------------------------------------
    def test_CreateFromCodeWithOffset(self):
        def HelperFunction() -> Region:
            return Region.CreateFromCode(callstack_offset=0)

        region = HelperFunction()

        assert region.filename == Path(__file__)


# ----------------------------------------------------------------------
class TestRegionStr:
    # ----------------------------------------------------------------------
    def test_StrSameBeginEnd(self):
        filename = Path("src/file.py")
        loc = Location(line=10, column=25)

        region = Region(filename=filename, begin=loc, end=loc)

        assert str(region) == "src/file.py, Ln 10 Col 25"

    # ----------------------------------------------------------------------
    def test_StrDifferentBeginEnd(self):
        filename = Path("src/file.py")
        begin = Location(line=10, column=5)
        end = Location(line=15, column=20)

        region = Region(filename=filename, begin=begin, end=end)

        assert str(region) == "src/file.py, Ln 10 Col 5 - Ln 15 Col 20"


# ----------------------------------------------------------------------
class TestRegionCompare:
    # ----------------------------------------------------------------------
    def test_EqualRegions(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert Region.Compare(region1, region2) == 0

    # ----------------------------------------------------------------------
    def test_DifferentFilenameFirstLess(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("aaa.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("zzz.txt"), begin=begin, end=end)

        assert Region.Compare(region1, region2) < 0

    # ----------------------------------------------------------------------
    def test_DifferentFilenameFirstGreater(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("zzz.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("aaa.txt"), begin=begin, end=end)

        assert Region.Compare(region1, region2) > 0

    # ----------------------------------------------------------------------
    def test_SameFilenameFirstBeginLess(self):
        filename = Path("test.txt")
        end = Location(line=10, column=10)

        region1 = Region(filename=filename, begin=Location(line=1, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=5, column=1), end=end)

        assert Region.Compare(region1, region2) < 0

    # ----------------------------------------------------------------------
    def test_SameFilenameFirstBeginGreater(self):
        filename = Path("test.txt")
        end = Location(line=10, column=10)

        region1 = Region(filename=filename, begin=Location(line=5, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=1, column=1), end=end)

        assert Region.Compare(region1, region2) > 0

    # ----------------------------------------------------------------------
    def test_SameFilenameAndBeginFirstEndLess(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)

        region1 = Region(filename=filename, begin=begin, end=Location(line=5, column=1))
        region2 = Region(filename=filename, begin=begin, end=Location(line=10, column=1))

        assert Region.Compare(region1, region2) < 0

    # ----------------------------------------------------------------------
    def test_SameFilenameAndBeginFirstEndGreater(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)

        region1 = Region(filename=filename, begin=begin, end=Location(line=10, column=1))
        region2 = Region(filename=filename, begin=begin, end=Location(line=5, column=1))

        assert Region.Compare(region1, region2) > 0


# ----------------------------------------------------------------------
class TestRegionHash:
    # ----------------------------------------------------------------------
    def test_EqualRegionsHaveSameHash(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert hash(region1) == hash(region2)

    # ----------------------------------------------------------------------
    def test_DifferentRegionsCanHaveDifferentHash(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)

        region1 = Region(filename=filename, begin=begin, end=Location(line=5, column=10))
        region2 = Region(filename=filename, begin=begin, end=Location(line=5, column=11))

        assert hash(region1) != hash(region2)

    # ----------------------------------------------------------------------
    def test_UsableInSet(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)
        region3 = Region(filename=filename, begin=begin, end=Location(line=6, column=1))

        s = {region1, region2, region3}

        assert len(s) == 2


# ----------------------------------------------------------------------
class TestRegionEquality:
    # ----------------------------------------------------------------------
    def test_Equal(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert region1 == region2

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("file1.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("file2.txt"), begin=begin, end=end)

        assert not (region1 == region2)

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentBegin(self):
        filename = Path("test.txt")
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=Location(line=1, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=2, column=1), end=end)

        assert not (region1 == region2)

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentEnd(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)

        region1 = Region(filename=filename, begin=begin, end=Location(line=5, column=10))
        region2 = Region(filename=filename, begin=begin, end=Location(line=6, column=10))

        assert not (region1 == region2)

    # ----------------------------------------------------------------------
    def test_NotEqualNonRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert not (region == "not a region")
        assert not (region == None)
        assert not (region == 5)


# ----------------------------------------------------------------------
class TestRegionInequality:
    # ----------------------------------------------------------------------
    def test_NotEqualDifferentFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("file1.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("file2.txt"), begin=begin, end=end)

        assert region1 != region2

    # ----------------------------------------------------------------------
    def test_NotEqualDifferentBegin(self):
        filename = Path("test.txt")
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=Location(line=1, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=2, column=1), end=end)

        assert region1 != region2

    # ----------------------------------------------------------------------
    def test_EqualRegionsNotUnequal(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert not (region1 != region2)

    # ----------------------------------------------------------------------
    def test_NotEqualNonRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert region != "not a region"
        assert region != None
        assert region != 5


# ----------------------------------------------------------------------
class TestRegionLessThan:
    # ----------------------------------------------------------------------
    def test_LessThanByFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("aaa.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("zzz.txt"), begin=begin, end=end)

        assert region1 < region2

    # ----------------------------------------------------------------------
    def test_LessThanByBegin(self):
        filename = Path("test.txt")
        end = Location(line=10, column=10)

        region1 = Region(filename=filename, begin=Location(line=1, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=5, column=1), end=end)

        assert region1 < region2

    # ----------------------------------------------------------------------
    def test_LessThanByEnd(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)

        region1 = Region(filename=filename, begin=begin, end=Location(line=5, column=1))
        region2 = Region(filename=filename, begin=begin, end=Location(line=10, column=1))

        assert region1 < region2

    # ----------------------------------------------------------------------
    def test_NotLessThanWhenEqual(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert not (region1 < region2)

    # ----------------------------------------------------------------------
    def test_NotLessThanWhenGreater(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("zzz.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("aaa.txt"), begin=begin, end=end)

        assert not (region1 < region2)

    # ----------------------------------------------------------------------
    def test_NotLessThanNonRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert not (region < "not a region")


# ----------------------------------------------------------------------
class TestRegionLessThanOrEqual:
    # ----------------------------------------------------------------------
    def test_LessThanOrEqualByFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("aaa.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("zzz.txt"), begin=begin, end=end)

        assert region1 <= region2

    # ----------------------------------------------------------------------
    def test_LessThanOrEqualByBegin(self):
        filename = Path("test.txt")
        end = Location(line=10, column=10)

        region1 = Region(filename=filename, begin=Location(line=1, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=5, column=1), end=end)

        assert region1 <= region2

    # ----------------------------------------------------------------------
    def test_LessThanOrEqualWhenEqual(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert region1 <= region2

    # ----------------------------------------------------------------------
    def test_NotLessThanOrEqualWhenGreater(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("zzz.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("aaa.txt"), begin=begin, end=end)

        assert not (region1 <= region2)

    # ----------------------------------------------------------------------
    def test_NotLessThanOrEqualNonRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert not (region <= "not a region")


# ----------------------------------------------------------------------
class TestRegionGreaterThan:
    # ----------------------------------------------------------------------
    def test_GreaterThanByFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("zzz.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("aaa.txt"), begin=begin, end=end)

        assert region1 > region2

    # ----------------------------------------------------------------------
    def test_GreaterThanByBegin(self):
        filename = Path("test.txt")
        end = Location(line=10, column=10)

        region1 = Region(filename=filename, begin=Location(line=5, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=1, column=1), end=end)

        assert region1 > region2

    # ----------------------------------------------------------------------
    def test_GreaterThanByEnd(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)

        region1 = Region(filename=filename, begin=begin, end=Location(line=10, column=1))
        region2 = Region(filename=filename, begin=begin, end=Location(line=5, column=1))

        assert region1 > region2

    # ----------------------------------------------------------------------
    def test_NotGreaterThanWhenEqual(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert not (region1 > region2)

    # ----------------------------------------------------------------------
    def test_NotGreaterThanWhenLess(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("aaa.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("zzz.txt"), begin=begin, end=end)

        assert not (region1 > region2)

    # ----------------------------------------------------------------------
    def test_NotGreaterThanNonRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert not (region > "not a region")


# ----------------------------------------------------------------------
class TestRegionGreaterThanOrEqual:
    # ----------------------------------------------------------------------
    def test_GreaterThanOrEqualByFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("zzz.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("aaa.txt"), begin=begin, end=end)

        assert region1 >= region2

    # ----------------------------------------------------------------------
    def test_GreaterThanOrEqualByBegin(self):
        filename = Path("test.txt")
        end = Location(line=10, column=10)

        region1 = Region(filename=filename, begin=Location(line=5, column=1), end=end)
        region2 = Region(filename=filename, begin=Location(line=1, column=1), end=end)

        assert region1 >= region2

    # ----------------------------------------------------------------------
    def test_GreaterThanOrEqualWhenEqual(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=filename, begin=begin, end=end)
        region2 = Region(filename=filename, begin=begin, end=end)

        assert region1 >= region2

    # ----------------------------------------------------------------------
    def test_NotGreaterThanOrEqualWhenLess(self):
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region1 = Region(filename=Path("aaa.txt"), begin=begin, end=end)
        region2 = Region(filename=Path("zzz.txt"), begin=begin, end=end)

        assert not (region1 >= region2)

    # ----------------------------------------------------------------------
    def test_NotGreaterThanOrEqualNonRegion(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=5, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert not (region >= "not a region")


# ----------------------------------------------------------------------
class TestRegionContains:
    # ----------------------------------------------------------------------
    def test_ContainsLocationAtBegin(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=10, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert begin in region

    # ----------------------------------------------------------------------
    def test_ContainsLocationAtEnd(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=10, column=10)

        region = Region(filename=filename, begin=begin, end=end)

        assert end in region

    # ----------------------------------------------------------------------
    def test_ContainsLocationInMiddle(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=10, column=10)

        region = Region(filename=filename, begin=begin, end=end)
        middle = Location(line=5, column=5)

        assert middle in region

    # ----------------------------------------------------------------------
    def test_DoesNotContainLocationBefore(self):
        filename = Path("test.txt")
        begin = Location(line=5, column=5)
        end = Location(line=10, column=10)

        region = Region(filename=filename, begin=begin, end=end)
        before = Location(line=3, column=1)

        assert before not in region

    # ----------------------------------------------------------------------
    def test_DoesNotContainLocationAfter(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=10, column=10)

        region = Region(filename=filename, begin=begin, end=end)
        after = Location(line=15, column=1)

        assert after not in region

    # ----------------------------------------------------------------------
    def test_ContainsRegionExactMatch(self):
        filename = Path("test.txt")
        begin = Location(line=1, column=1)
        end = Location(line=10, column=10)

        outer = Region(filename=filename, begin=begin, end=end)
        inner = Region(filename=filename, begin=begin, end=end)

        assert inner in outer

    # ----------------------------------------------------------------------
    def test_ContainsRegionInside(self):
        filename = Path("test.txt")

        outer = Region(
            filename=filename,
            begin=Location(line=1, column=1),
            end=Location(line=20, column=20),
        )
        inner = Region(
            filename=filename,
            begin=Location(line=5, column=5),
            end=Location(line=15, column=15),
        )

        assert inner in outer

    # ----------------------------------------------------------------------
    def test_DoesNotContainRegionDifferentFilename(self):
        begin = Location(line=1, column=1)
        end = Location(line=10, column=10)

        outer = Region(filename=Path("file1.txt"), begin=begin, end=end)
        inner = Region(filename=Path("file2.txt"), begin=begin, end=end)

        assert inner not in outer

    # ----------------------------------------------------------------------
    def test_DoesNotContainRegionBeginsBefore(self):
        filename = Path("test.txt")

        outer = Region(
            filename=filename,
            begin=Location(line=5, column=5),
            end=Location(line=20, column=20),
        )
        inner = Region(
            filename=filename,
            begin=Location(line=1, column=1),
            end=Location(line=10, column=10),
        )

        assert inner not in outer

    # ----------------------------------------------------------------------
    def test_DoesNotContainRegionEndsAfter(self):
        filename = Path("test.txt")

        outer = Region(
            filename=filename,
            begin=Location(line=1, column=1),
            end=Location(line=15, column=15),
        )
        inner = Region(
            filename=filename,
            begin=Location(line=5, column=5),
            end=Location(line=20, column=20),
        )

        assert inner not in outer
