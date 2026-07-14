import hashlib
import tempfile
import unittest
from pathlib import Path

from golden_axe.profiles import DEFAULT_PROFILE, PROFILE_FILES, load_system_prompt
from lhco_domain.profile import load_oraclet_domain_prompt


class ProfileTests(unittest.TestCase):
    def test_oracle_is_default(self):
        self.assertEqual(DEFAULT_PROFILE, "oracle")
        self.assertEqual(
            load_system_prompt(),
            load_system_prompt("oracle"),
        )

    def test_oracle_is_release_name_for_split_v3(self):
        self.assertEqual(
            load_system_prompt("oracle", context="Domain: test domain."),
            load_system_prompt("oracle-split-v3", context="Domain: test domain."),
        )
        prompt = load_system_prompt("oracle", context="Domain: test domain.")
        self.assertNotIn("{{DOMAIN_CONTEXT}}", prompt)
        self.assertIn(
            "<<<BEGIN_PRIVATE_DOMAIN_CONTEXT>>>\nDomain: test domain.",
            prompt,
        )
        self.assertIn("POSSIBLE_CLARIFYING_REWRITES:", prompt)
        self.assertIn("Do not write SUMMARY_REWRITE.", prompt)
        self.assertNotIn("SUMMARY_REWRITE:\n", prompt)
        self.assertLess(
            prompt.index("Domain: test domain."),
            prompt.index("Output format:"),
        )

    def test_oracle_can_use_domain_owned_output_contract(self):
        prompt = load_system_prompt(
            "oracle",
            context="Domain rules with domain-owned output.",
            output_contract="domain",
        )
        self.assertIn("Domain rules with domain-owned output.", prompt)
        self.assertNotIn("POSSIBLE_CLARIFYING_REWRITES:", prompt)
        self.assertNotIn("Output format:", prompt)

    def test_oracle_lite_is_legacy_monolithic_prompt(self):
        prompt = load_system_prompt("oracle-lite")
        self.assertIn(
            "preflight ambiguity critic for physics-analysis user inputs",
            prompt,
        )
        self.assertIn("SUMMARY_REWRITE:", prompt)
        self.assertEqual(
            hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "77ae294e30867d07d58c8ca8bb20c18df9058b8badfc1d26a9797de256e3c8ce",
        )

    def test_oraclet_uses_domain_owned_output_contract_from_lhco_domain(self):
        prompt = load_system_prompt("oraclet", context=load_oraclet_domain_prompt())
        self.assertIn("You are Golden Axe Oracle", prompt)
        self.assertIn("ambiguity groups", prompt)
        self.assertIn("CATEGORY: COLLECTION_SCOPE", prompt)
        self.assertEqual(prompt.count("SUMMARY_REWRITE:"), 1)
        self.assertNotIn("POSSIBLE_CLARIFYING_REWRITES:", prompt)

    def test_oraclet_requires_domain_context(self):
        with self.assertRaisesRegex(ValueError, "requires a domain prompt/context"):
            load_system_prompt("oraclet")

    def test_system_output_contract_rejected_for_domain_owned_profiles(self):
        with self.assertRaisesRegex(ValueError, "complete/domain-owned prompt"):
            load_system_prompt(
                "oraclet",
                context=load_oraclet_domain_prompt(),
                output_contract="system",
            )
        with self.assertRaisesRegex(ValueError, "complete/domain-owned prompt"):
            load_system_prompt("oracle-lite", output_contract="system")

    def test_local_prompt_path_preserves_previous_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prompt.txt"
            path.write_text("LOCAL {{DOMAIN_CONTEXT}}", encoding="utf-8")
            self.assertEqual(
                load_system_prompt("oracle", path=path, context="CTX"),
                "LOCAL CTX",
            )

    def test_failed_grounded_profile_is_not_exposed(self):
        with self.assertRaisesRegex(ValueError, "Unknown profile"):
            load_system_prompt("oraclet-grounded")

    def test_profile_names_include_release_and_compatibility_names(self):
        self.assertIn("oracle", PROFILE_FILES)
        self.assertIn("oracle-lite", PROFILE_FILES)
        self.assertIn("oracle-split-v3", PROFILE_FILES)
        self.assertIn("oraclet", PROFILE_FILES)


if __name__ == "__main__":
    unittest.main()
