from hamcrest.core.assert_that import assert_that  # pyre-ignore[21]
from hamcrest.library import contains_exactly, has_entries  # pyre-ignore[21]


def assert_exception_has_errors(exc_info, line_numbers, description) -> None:
    assert_that(
        exc_info.value.errors,
        contains_exactly(
            *[
                has_entries({"description": description, "lineNumber": line_number})
                for line_number in line_numbers
            ]
        ),
    )
