import hashlib
import unittest

from lhco_domain.cards import parse_card
from lhco_domain import DOMAIN_ASSETS
from lhco_domain.profile import LHCO_PROFILE, load_codegen_system_prompt
from lhco_domain.registry import HELPER_REGISTRY


class LHCOProfileTests(unittest.TestCase):
    def test_parses_lhco_card_sections(self):
        sections = parse_card(
            "[SELECTION_CUTS]\n- pT > 20\n\n"
            "[PLOTS_FOR_VALIDATION]\n- mass\n\n"
            "[OUTPUT_STRUCTURE]\n- CSV\n\n"
            "[ADDITIONAL_HELPERS]\n- read_lhco\n"
        )
        self.assertEqual(sections.selection_cuts, "- pT > 20")
        self.assertEqual(sections.additional_helpers, "- read_lhco")

    def test_builds_lhco_generation_messages(self):
        messages = LHCO_PROFILE.build_messages(
            "[SELECTION_CUTS]\n- pT > 20"
        )
        self.assertTrue(messages[0]["content"].startswith("/no_think\n\n"))
        self.assertIn("analyze LHCO files", messages[1]["content"])
        self.assertIn("- pT > 20", messages[1]["content"])

    def test_codegen_prompt_is_preserved_byte_for_byte(self):
        digest = hashlib.sha256(
            load_codegen_system_prompt().encode("utf-8")
        ).hexdigest()
        self.assertEqual(
            digest,
            "e889f585a3e04d9656c45486e430e542efbdfbbc367aecd3c4c6640e8eb32f30",
        )

    def test_registry_helpers_exist_in_codegen_prompt(self):
        prompt = load_codegen_system_prompt()
        missing = [
            helper.name
            for helper in HELPER_REGISTRY
            if f"def {helper.name}(" not in prompt
        ]
        self.assertEqual(missing, [])


class LHCOGenericDomainAssetsTests(unittest.TestCase):
    def test_domain_assets_use_generic_keys(self):
        self.assertIs(DOMAIN_ASSETS["generation_profile"], LHCO_PROFILE)
        self.assertIs(DOMAIN_ASSETS["helper_registry"], HELPER_REGISTRY)
        self.assertTrue(DOMAIN_ASSETS["load_helper_policy"]())
        self.assertTrue(DOMAIN_ASSETS["load_critique_context"]())
        self.assertEqual(DOMAIN_ASSETS["default_helpers"], ("read_lhco",))

