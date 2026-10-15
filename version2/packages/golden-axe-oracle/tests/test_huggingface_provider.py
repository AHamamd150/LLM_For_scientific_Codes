import unittest
from types import SimpleNamespace

from golden_axe.providers.huggingface import HuggingFaceChatProvider


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.content)
                )
            ]
        )


def make_provider(content):
    provider = HuggingFaceChatProvider.__new__(HuggingFaceChatProvider)
    completions = FakeCompletions(content)
    provider._client = SimpleNamespace(
        chat=SimpleNamespace(completions=completions)
    )
    provider._max_tokens = 1800
    provider._temperature = 0.2
    return provider, completions


class HuggingFaceProviderTests(unittest.TestCase):
    def test_disables_thinking_in_system_message(self):
        provider, completions = make_provider("No high-risk ambiguity found.")

        result = provider.complete(
            system_prompt="Oracle prompt.",
            user_prompt="Card.",
        )

        self.assertEqual(result, "No high-risk ambiguity found.")
        messages = completions.calls[0]["messages"]
        self.assertEqual(
            messages[0]["content"],
            "/no_think\n\nOracle prompt.",
        )
        self.assertEqual(messages[1]["content"], "Card.")

    def test_removes_completed_think_block(self):
        provider, _ = make_provider(
            "<think>private reasoning</think>\n"
            "[AMBIGUITY 1]\nCompact answer."
        )

        result = provider.complete(
            system_prompt="Oracle prompt.",
            user_prompt="Card.",
        )

        self.assertEqual(result, "[AMBIGUITY 1]\nCompact answer.")

    def test_rejects_response_cut_off_inside_think_block(self):
        provider, _ = make_provider("<think>unfinished reasoning")

        with self.assertRaisesRegex(ValueError, "inside a think block"):
            provider.complete(
                system_prompt="Oracle prompt.",
                user_prompt="Card.",
            )

    def test_rejects_think_only_response(self):
        provider, _ = make_provider(
            "<think>private reasoning</think>"
        )

        with self.assertRaisesRegex(ValueError, "no final answer"):
            provider.complete(
                system_prompt="Oracle prompt.",
                user_prompt="Card.",
            )


if __name__ == "__main__":
    unittest.main()
