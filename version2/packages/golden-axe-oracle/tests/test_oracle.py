import unittest

from golden_axe import OracleRequest, build_user_message, run_oracle


class FakeProvider:
    def __init__(self, response: str = "Oracle speaks freely.") -> None:
        self.response = response
        self.system_prompt = ""
        self.user_prompt = ""

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return self.response


class OracleTests(unittest.TestCase):
    def test_builds_optional_sections(self):
        message = build_user_message(
            "card",
            registry_text="registry",
            codegen_system_prompt="codegen",
        )
        self.assertIn("<<<BEGIN_USER_INPUT\ncard\nEND_USER_INPUT>>>", message)
        self.assertIn(
            "<<<BEGIN_HELPER_REGISTRY\nregistry\nEND_HELPER_REGISTRY>>>",
            message,
        )
        self.assertIn(
            "<<<BEGIN_CODEGEN_SYSTEM_PROMPT\ncodegen\n"
            "END_CODEGEN_SYSTEM_PROMPT>>>",
            message,
        )

    def test_registry_and_codegen_context_are_optional(self):
        message = build_user_message("card")
        self.assertNotIn("HELPER_REGISTRY", message)
        self.assertNotIn("CODEGEN_SYSTEM_PROMPT", message)

    def test_preserves_free_form_response(self):
        provider = FakeProvider("[AMBIGUITY 1]\nAnything.")
        response = run_oracle(
            OracleRequest(card_text="card", profile="oraclet"),
            provider,
            system_prompt="Oracle system prompt.",
        )
        self.assertEqual(response.text, "[AMBIGUITY 1]\nAnything.")
        self.assertEqual(response.profile, "oraclet")
        self.assertEqual(provider.system_prompt, "Oracle system prompt.")


if __name__ == "__main__":
    unittest.main()
