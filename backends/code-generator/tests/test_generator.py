import unittest

from code_generator import CodeGenerator, GenerationRequest
from code_generator.model_response import extract_python_code


class FakeProvider:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.messages = []

    def complete(self, messages):
        self.messages.append(messages)
        return next(self.responses)


class FakeProfile:
    response_rejection_markers = ()

    def build_messages(self, card_text):
        return [
            {"role": "system", "content": "test"},
            {"role": "user", "content": card_text},
        ]


class GeneratorTests(unittest.TestCase):
    def test_extracts_longest_python_block(self):
        code = extract_python_code(
            "text\n```python\nx = 1\n```\n```python\nx = 1\ny = 2\n```"
        )
        self.assertEqual(code, "x = 1\ny = 2")

    def test_generates_valid_code(self):
        provider = FakeProvider(["```python\nimport sys\nprint(sys.argv[1])\n```"])
        result = CodeGenerator(provider, FakeProfile()).generate(
            GenerationRequest("[SELECTION_CUTS]\n- none")
        )
        self.assertTrue(result.syntax_valid)
        self.assertEqual(len(result.raw_responses), 1)

    def test_requests_continuation_for_truncated_code(self):
        provider = FakeProvider(
            [
                "```python\nimport sys\nif True:\n```",
                "    print(sys.argv[1])",
            ]
        )
        result = CodeGenerator(provider, FakeProfile()).generate(
            GenerationRequest("[SELECTION_CUTS]\n- none")
        )
        self.assertTrue(result.syntax_valid)
        self.assertEqual(len(result.raw_responses), 2)

    def test_core_uses_supplied_profile_messages(self):
        provider = FakeProvider(["print('ok')"])
        CodeGenerator(provider, FakeProfile()).generate(
            GenerationRequest("domain-specific card")
        )
        self.assertEqual(
            provider.messages[0][1],
            {"role": "user", "content": "domain-specific card"},
        )


if __name__ == "__main__":
    unittest.main()
