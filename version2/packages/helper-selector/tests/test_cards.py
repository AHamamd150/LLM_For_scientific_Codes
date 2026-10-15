import unittest

from helper_selector import SelectionItem, SelectionResult, update_card_with_helpers


class CardTests(unittest.TestCase):
    def test_adds_helpers_without_overwriting_original_text(self):
        selection = SelectionResult((SelectionItem("helper_a"),))
        revised = update_card_with_helpers("[TASK]\nDo work.\n", selection)
        self.assertEqual(
            revised,
            "[TASK]\nDo work.\n\n"
            "[ADDITIONAL_HELPERS]\n- helper_a\n",
        )

    def test_adds_explicit_default_helpers_first(self):
        selection = SelectionResult((SelectionItem("helper_a"),))
        revised = update_card_with_helpers(
            "[TASK]\nDo work.\n",
            selection,
            default_helpers=("read_lhco",),
        )
        self.assertEqual(
            revised,
            "[TASK]\nDo work.\n\n"
            "[ADDITIONAL_HELPERS]\n- read_lhco\n- helper_a\n",
        )

    def test_replaces_existing_section(self):
        selection = SelectionResult((SelectionItem("new_helper"),))
        revised = update_card_with_helpers(
            "[TASK]\nDo work.\n\n"
            "[ADDITIONAL_HELPERS]\n- old_helper\n\n"
            "[OUTPUT]\nCSV\n",
            selection,
        )
        self.assertNotIn("- old_helper", revised)
        self.assertIn("- new_helper", revised)
        self.assertIn("[OUTPUT]\nCSV", revised)


if __name__ == "__main__":
    unittest.main()
