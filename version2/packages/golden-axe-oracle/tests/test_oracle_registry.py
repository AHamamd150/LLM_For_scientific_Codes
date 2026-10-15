import unittest

from golden_axe.registry import render_registry


class RegistryTests(unittest.TestCase):
    def test_accepts_mapping_without_golden_axe_type_dependency(self):
        rendered = render_registry(
            [
                {
                    "name": "helper_a",
                    "section": "test",
                    "summary": "A helper.",
                    "keywords": ["alpha", "beta"],
                }
            ]
        )
        self.assertIn("- name: helper_a", rendered)
        self.assertIn("keywords: alpha, beta", rendered)


if __name__ == "__main__":
    unittest.main()

