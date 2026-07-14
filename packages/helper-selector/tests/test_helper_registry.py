import unittest

from helper_selector.models import HelperSpec
from helper_selector.registry import normalize_registry


class RegistryTests(unittest.TestCase):
    def test_registry_rejects_missing_dependency(self):
        with self.assertRaisesRegex(ValueError, "unknown dependencies"):
            normalize_registry(
                [
                    HelperSpec(
                        "derived",
                        "test",
                        "Derived.",
                        ("derived",),
                        dependencies=("missing",),
                    )
                ]
            )


if __name__ == "__main__":
    unittest.main()
