from helper_selector import HelperSpec


HELPER_REGISTRY = [
    HelperSpec(
        name="add_numbers",
        section="arithmetic",
        summary="Return the sum of two numbers.",
        keywords=("add", "sum", "addition"),
        aliases=("plus",),
    ),
]
