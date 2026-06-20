# noqa: D104

from importlib.metadata import version

from dbrownell_ParserLib.location import Location


# ----------------------------------------------------------------------
__all__ = [
    "Location",
    "__version__",
]


__version__ = version("dbrownell_ParserLib")
