"""Functionality used when parsing multiline strings."""

from dataclasses import dataclass

from dbrownell_ParserLib.errors import CreateErrorType
from dbrownell_ParserLib.region import Location, Region


# ----------------------------------------------------------------------
MisalignedMultilineStringError = CreateErrorType(
    "All lines in a multiline string must be vertically aligned with the opening token."
)


# ----------------------------------------------------------------------
def ExtractMultilineString(
    content: str,
    opening_token_region: Region,
    opening_token: str = '"""',  # noqa: S107
    closing_token: str = '"""',  # noqa: S107
    tab_size: int = 4,
) -> str:
    """Extract a multiline string from the given content, ensuring that all lines are vertically aligned with the opening token."""

    assert content.startswith(opening_token), content
    content = content[len(opening_token) :]

    assert content.endswith(closing_token), content
    content = content[: -len(closing_token)]

    lines = content.splitlines()

    # Handle the special case where the multiline string begins at column 1. In this case, the content
    # should end with a newline.
    if content.endswith("\n") and opening_token_region.begin.column == 1:
        lines.append("")

    # Ensure that there is a newline immediately following the opening token
    if lines[0]:
        # This means that there was content immediately following the opening token when a newline was expected.
        location = Location(
            opening_token_region.begin.line,
            opening_token_region.begin.column + len(opening_token),
        )

        raise MisalignedMultilineStringError.CreateAsException(
            Region(opening_token_region.filename, location, location)
        )

    lines = lines[1:]
    assert lines

    # Ensure that the closing token is on its own line
    result = _CalcPrefixColumn(lines[-1], tab_size, None)

    if result.column != opening_token_region.begin.column:
        location = Location(opening_token_region.begin.line + len(lines) + 1, result.column)

        raise MisalignedMultilineStringError.CreateAsException(
            Region(opening_token_region.filename, location, location)
        )

    lines = lines[:-1]

    # Process the content
    acceptable_prefix_column_values = {1, opening_token_region.begin.column}
    escaped_closing_token = "".join(f"\\{c}" for c in closing_token)

    # Ensure that all lines are vertically aligned with the opening token
    for line_index, line in enumerate(lines):
        result = _CalcPrefixColumn(line, tab_size, opening_token_region.begin.column)

        if result.column not in acceptable_prefix_column_values:
            location = Location(opening_token_region.begin.line + line_index + 1, result.column)

            raise MisalignedMultilineStringError.CreateAsException(
                Region(opening_token_region.filename, location, location)
            )

        normalized_line = line[result.num_chars :]

        if normalized_line.isspace():
            normalized_line = ""
        else:
            normalized_line = normalized_line.replace(escaped_closing_token, closing_token)

        lines[line_index] = normalized_line

    # Handle the special case where the multiline string consists of all newlines
    if lines and all(not line for line in lines):
        return "".join("\n" * len(lines))

    return "\n".join(lines)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@dataclass(frozen=True)
class _CalcPrefixColumnResult:
    column: int
    num_chars: int


def _CalcPrefixColumn(line: str, tab_size: int, max_column: int | None) -> _CalcPrefixColumnResult:
    max_column = max_column or 99999999

    column = 1
    num_chars = 0

    for char in line:
        if column >= max_column:
            break

        if char == " ":
            column += 1
        elif char == "\t":
            column += tab_size
        else:
            break

        num_chars += 1

    return _CalcPrefixColumnResult(column, num_chars)
