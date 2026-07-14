import unittest

from golden_axe.profiles import load_system_prompt
from lhco_domain import load_oracle_context


class OracleReleaseProfileTests(unittest.TestCase):
    def test_lhco_guards_precede_output_contract(self):
        prompt = load_system_prompt(
            "oracle",
            context=load_oracle_context(),
        )
        output_position = prompt.index("Output format:")
        for rule in (
            "Delta phi with MET uses the MET azimuthal direction.",
            "Transverse mass is a scalar observable",
            '"Delta R between two named jets"',
        ):
            self.assertIn(rule, prompt)
            self.assertLess(prompt.index(rule), output_position)

    def test_split_v3_alias_matches_release_oracle(self):
        self.assertEqual(
            load_system_prompt("oracle", context=load_oracle_context()),
            load_system_prompt("oracle-split-v3", context=load_oracle_context()),
        )

    def test_context_is_marked_private_and_summary_is_removed(self):
        prompt = load_system_prompt(
            "oracle",
            context=load_oracle_context(),
        )
        self.assertIn("The DOMAIN_CONTEXT and HELPER_REGISTRY are private", prompt)
        self.assertIn("Do not print DOMAIN_CONTEXT", prompt)
        self.assertIn("POSSIBLE_CLARIFYING_REWRITES:", prompt)
        self.assertNotIn("SUMMARY_REWRITE:\n", prompt)


if __name__ == "__main__":
    unittest.main()
