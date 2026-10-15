import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from codegen_workflows import ResearchCodeWorkflow
from code_generator import (
    CodeGenerator,
    ExecutionResult,
    GenerationRequest,
    GenerationResult,
)
from critique_pipeline.providers.base import ChatCompletion
from helper_selector import HelperSpec


class StaticPromptProvider:
    def __init__(self, response):
        self.response = response

    def complete(self, *, system_prompt, user_prompt):
        return self.response


class CodeProvider:
    def complete(self, messages):
        return "```python\nprint('generated')\n```"


class GenerationProfile:
    response_rejection_markers = ()

    def build_messages(self, card_text):
        return [{"role": "user", "content": card_text}]


class RegeneratingGenerator:
    def __init__(self, codes):
        self.codes = iter(codes)
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        code = next(self.codes)
        return GenerationResult(
            code=code,
            raw_responses=(f"raw {code}",),
            syntax_valid=True,
        )


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
✅ * Generate output; computed as: print('generated'); upstream chain: print; 〔L1〕

* [CHECK CAREFULLY] DEFINITION SUMMARY

* output
  - computed/defined as: print('generated')
  - upstream chain: print
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


class WorkflowTests(unittest.TestCase):
    def test_generate_and_review(self):
        registry = [
            HelperSpec(
                name="read_input",
                section="parser",
                summary="Read input.",
                keywords=("input",),
            )
        ]
        workflow = ResearchCodeWorkflow(registry)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow.generate_and_review(
                accepted_card_text="[SELECTION_CUTS]\n- Generate output",
                helper_provider=StaticPromptProvider(
                    json.dumps(
                        {
                            "selected_helpers": ["read_input"],
                            "rejected_but_close": [],
                        }
                    )
                ),
                generator=CodeGenerator(
                    CodeProvider(),
                    GenerationProfile(),
                ),
                tracer_provider=CritiqueProvider([TRACE]),
                critique_provider=CritiqueProvider([CRITIQUE]),
                run_root=root,
                critique_context="Domain context: test.",
            )
            self.assertTrue((root / "cards/generation.txt").exists())
            self.assertTrue((root / "generation/src/analysis.py").exists())
            self.assertTrue((root / "critique/findings/filtered_review.txt").exists())

    def test_execution_retries_fix_then_regenerate(self):
        workflow = ResearchCodeWorkflow([])
        generator = RegeneratingGenerator(["regenerated 1", "regenerated 2"])
        results = [
            ExecutionResult(1, "", "initial error"),
            ExecutionResult(1, "", "fix 1 error"),
            ExecutionResult(1, "", "regen 1 error"),
            ExecutionResult(1, "", "fix 2 error"),
            ExecutionResult(0, "ok", ""),
        ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code_path = root / "analysis.py"
            input_path = root / "input.dat"
            execution_dir = root / "execution"
            generation_info_dir = execution_dir / "generation_info"
            code_path.write_text("initial", encoding="utf-8")
            input_path.write_text("", encoding="utf-8")

            with (
                patch(
                    "codegen_workflows.pipeline.execute_python",
                    side_effect=results,
                ) as execute_mock,
                patch(
                    "codegen_workflows.pipeline.fix_code",
                    side_effect=[
                        ("fixed 1", "raw fix 1"),
                        ("fixed 2", "raw fix 2"),
                    ],
                ) as fix_mock,
            ):
                final_code = workflow._execute_fix_and_regenerate(
                    code_path=code_path,
                    input_paths=(input_path,),
                    execution_dir=execution_dir,
                    generation_info_dir=generation_info_dir,
                    generator=generator,
                    generation_request=GenerationRequest(
                        card_text="[SELECTION_CUTS]\n- test"
                    ),
                    fixer_provider=object(),
                    max_retries=2,
                )

            self.assertEqual(final_code, "regenerated 2")
            self.assertEqual(execute_mock.call_count, 5)
            self.assertEqual(
                execute_mock.call_args_list[0].args[1],
                [str(input_path.resolve())],
            )
            self.assertEqual(fix_mock.call_count, 2)
            self.assertEqual(len(generator.requests), 2)
            self.assertEqual(
                code_path.read_text(encoding="utf-8").strip(),
                "regenerated 2",
            )
            self.assertTrue(
                (
                    generation_info_dir
                    / "attempt_005_regen_stderr_trial_2.txt"
                ).exists()
            )
            self.assertTrue(
                (execution_dir / "generated_analysis.py").exists()
            )
            self.assertEqual(
                (execution_dir / "stdout.txt").read_text(
                    encoding="utf-8"
                ),
                "ok",
            )
            self.assertEqual(
                (execution_dir / "cutflow.txt").read_text(
                    encoding="utf-8"
                ),
                "ok",
            )
            self.assertFalse(
                (execution_dir / "attempt_005_regen_stderr_trial_2.txt").exists()
            )

    def test_generate_and_review_rejects_input_inside_run_root(self):
        workflow = ResearchCodeWorkflow([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "input.dat"
            input_path.write_text("", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "Input files must be outside the run directory"
            ):
                workflow.generate_and_review(
                    accepted_card_text="[SELECTION_CUTS]\n- Generate output",
                    helper_provider=StaticPromptProvider(
                        json.dumps(
                            {
                                "selected_helpers": [],
                                "rejected_but_close": [],
                            }
                        )
                    ),
                    generator=CodeGenerator(
                        CodeProvider(),
                        GenerationProfile(),
                    ),
                    tracer_provider=CritiqueProvider([TRACE]),
                    critique_provider=CritiqueProvider([CRITIQUE]),
                    run_root=root,
                    input_paths=(input_path,),
                )


if __name__ == "__main__":
    unittest.main()
