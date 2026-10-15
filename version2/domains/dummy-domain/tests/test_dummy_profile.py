import unittest

from dummy_domain import (
    DUMMY_PROFILE,
    DOMAIN_ASSETS,
    HELPER_REGISTRY,
    load_critique_context,
    load_helper_policy,
    load_oracle_context,
)


class DummyProfileTests(unittest.TestCase):
    def test_build_messages_contains_card(self):
        card = "Write a function that returns the sum of two numbers."
        messages = DUMMY_PROFILE.build_messages(card)
        self.assertTrue(
            any(card in message["content"] for message in messages)
        )

    def test_system_prompt_has_no_collider_terms(self):
        messages = DUMMY_PROFILE.build_messages("test")
        system = next(
            message["content"]
            for message in messages
            if message["role"] == "system"
        )
        for term in ("LHCO", "collider", "leading jet"):
            self.assertNotIn(term, system)

    def test_domain_assets_load(self):
        self.assertTrue(load_oracle_context())
        self.assertTrue(load_critique_context())
        self.assertTrue(load_helper_policy())
        self.assertEqual(HELPER_REGISTRY[0].name, "add_numbers")


if __name__ == "__main__":
    unittest.main()


class DummyDomainAssetsTests(unittest.TestCase):
    def test_domain_assets_use_generic_keys(self):
        self.assertIn("generation_profile", DOMAIN_ASSETS)
        self.assertIn("helper_registry", DOMAIN_ASSETS)
        self.assertIn("load_helper_policy", DOMAIN_ASSETS)
        self.assertIn("load_critique_context", DOMAIN_ASSETS)

