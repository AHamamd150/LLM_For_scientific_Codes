import json
import tempfile
import unittest
from pathlib import Path

from code_generator import CodeGenerator
from codegen_workflows import ResearchCodeWorkflow
from critique_pipeline.providers.base import ChatCompletion
from dummy_domain import (
    DUMMY_IO_CONTRACT,
    DUMMY_PROFILE,
    HELPER_REGISTRY,
    load_critique_context,
    load_helper_policy,
    load_oracle_context,
)
from golden_axe import OracleRequest, run_oracle
from golden_axe.profiles import load_system_prompt
from golden_axe.registry import render_registry


class OracleProvider:
    def __init__(self):
        self.system_prompt = ""
        self.user_prompt = ""

    def complete(self, *, system_prompt, user_prompt):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        return "No high-risk ambiguity found."


class HelperProvider:
    def complete(self, *, system_prompt, user_prompt):
        return json.dumps(
            {
                "selected_helpers": ["add_numbers"],
                "rejected_but_close": [],
            }
        )


class CodeProvider:
    def __init__(self):
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        return """```python
import sys
from pathlib import Path


def read_numbers(path):
    numbers = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            numbers.append(float(line))
    return numbers


def main():
    input_paths = sys.argv[1:]
    numbers = []
    for input_path in input_paths:
        numbers.extend(read_numbers(input_path))
    total = sum(numbers)
    print(f"count: {len(numbers)}")
    print(f"sum: {total}")
    Path("result.txt").write_text(f"{total}\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
```"""


class CritiqueProvider:
    def __init__(self, responses):
        self.responses = iter(responses)

    def complete(self, messages, *, max_tokens, temperature):
        text = next(self.responses)
        raw = {
            "choices": [
                {
                    "message": {"content": text},
                    "finish_reason": "stop",
                }
            ]
        }
        return ChatCompletion(text, "stop", raw)


TRACE = """SECTION 1: SPEC BULLET ANALYSIS
✅ * Return a sum; computed as: a + b; upstream chain: add; 〔L2〕

* [CHECK CAREFULLY] DEFINITION SUMMARY

* sum
  - computed/defined as: a + b
  - upstream chain: add
  - collection definition: None
  - structure: single-constituent
"""

CRITIQUE = """⚠️ definition mismatch

SPEC:
none

CODE:
none

Reason:
test

Evidence priority:
summary

Generator bias:
none

❓ specification ambiguity

SPEC:
none

CODE:
none

Reason:
test

Evidence priority:
summary

Generator bias:
none

🌟 extra behavior

SPEC:
none

CODE:
none

Reason:
test

Evidence priority:
summary

Generator bias:
none
"""


class DummyDomainIntegrationTests(unittest.TestCase):
    def test_oracle_uses_generic_role_with_dummy_context(self):
        provider = OracleProvider()
        system_prompt = load_system_prompt(
            "oracle",
            context=load_oracle_context(),
        )
        response = run_oracle(
            OracleRequest(
                card_text="Write a function that adds two numbers.",
                registry_text=render_registry(HELPER_REGISTRY),
                profile="oracle",
            ),
            provider,
            system_prompt=system_prompt,
        )
        self.assertEqual(response.text, "No high-risk ambiguity found.")
        self.assertIn(
            "Domain context: general Python programming.",
            provider.system_prompt,
        )
        self.assertNotIn("physics-analysis user inputs", provider.system_prompt)

    def test_dummy_domain_runs_generation_execution_and_review(self):
        workflow = ResearchCodeWorkflow(HELPER_REGISTRY)
        provider = CodeProvider()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_dir = root / "data"
            data_dir.mkdir()
            input_path = data_dir / "numbers.txt"
            input_path.write_text("1\n2\n3.5\n", encoding="utf-8")
            run_root = root / "run"
            code, outputs = workflow.generate_and_review(
                accepted_card_text=(
                    "Read the input numbers file, print the count and sum, "
                    "and write result.txt with the sum."
                ),
                helper_provider=HelperProvider(),
                generator=CodeGenerator(provider, DUMMY_PROFILE),
                tracer_provider=CritiqueProvider([TRACE]),
                critique_provider=CritiqueProvider([CRITIQUE]),
                run_root=run_root,
                helper_policy=load_helper_policy(),
                critique_context=load_critique_context(),
                input_paths=(input_path,),
            )
            self.assertIn("sys.argv[1:]", code)
            self.assertIn("Generated script I/O contract", provider.messages[0]["content"])
            self.assertEqual(len(outputs), 1)
            self.assertTrue((run_root / "cards/generation.txt").exists())
            self.assertTrue((run_root / "execution/generated_analysis.py").exists())
            self.assertEqual(
                (run_root / "execution/result.txt").read_text(encoding="utf-8"),
                "6.5\n",
            )
            self.assertIn(
                "sum: 6.5",
                (run_root / "execution/stdout.txt").read_text(encoding="utf-8"),
            )
            self.assertIn(
                "sum: 6.5",
                (run_root / "execution/cutflow.txt").read_text(encoding="utf-8"),
            )
            self.assertTrue((run_root / "critique/findings/filtered_review.txt").exists())

    def test_dummy_domain_exposes_typed_io_contract(self):
        self.assertEqual(DUMMY_IO_CONTRACT.input_argument, "sys.argv[1:]")
        self.assertIn("one number", DUMMY_IO_CONTRACT.input_format)
        self.assertIn("result.txt", DUMMY_IO_CONTRACT.to_prompt_text())


if __name__ == "__main__":
    unittest.main()
