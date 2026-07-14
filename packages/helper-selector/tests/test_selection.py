import unittest

from helper_selector import HelperSpec, resolve_model_output


REGISTRY = [
    HelperSpec("base", "core", "Base helper.", ("base",)),
    HelperSpec(
        "derived",
        "calculation",
        "Derived helper.",
        ("derived",),
        dependencies=("base",),
    ),
    HelperSpec("nearby", "calculation", "Nearby helper.", ("nearby",)),
]


class SelectionTests(unittest.TestCase):
    def test_validates_and_expands_dependencies(self):
        result = resolve_model_output(
            {
                "selected_helpers": ["derived", "derived"],
                "rejected_but_close": ["nearby", "derived"],
            },
            REGISTRY,
        )
        self.assertEqual(
            [item.name for item in result.selected_helpers],
            ["base", "derived"],
        )
        self.assertEqual(
            result.selected_helpers[0].reason,
            "dependency of derived",
        )
        self.assertEqual(
            [item.name for item in result.rejected_but_close],
            ["nearby"],
        )

    def test_rejects_unknown_helper(self):
        with self.assertRaisesRegex(ValueError, "unknown helper"):
            resolve_model_output({"selected_helpers": ["invented"]}, REGISTRY)

    def test_extracts_json_from_wrapping_text(self):
        result = resolve_model_output(
            'answer: {"selected_helpers": ["base"], "rejected_but_close": []}',
            REGISTRY,
        )
        self.assertEqual(
            [item.name for item in result.selected_helpers],
            ["base"],
        )


if __name__ == "__main__":
    unittest.main()
