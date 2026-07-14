from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Sequence

from code_generator import CodeGenerator, GenerationRequest
from code_generator.executor import execute_python
from code_generator.fixer import fix_code
from critique_pipeline.workflow import run_critique_stage, run_tracer_stage
from helper_selector import select_helpers, update_card_with_helpers
from helper_selector.io import write_selection, write_summary
from workbench_contracts import RunLayout


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _validate_input_paths(input_paths: Sequence[Path], run_root: Path) -> None:
    resolved_run_root = run_root.resolve()
    for input_path in input_paths:
        resolved_input = input_path.resolve()
        if _is_relative_to(resolved_input, resolved_run_root):
            raise ValueError(
                "Input files must be outside the run directory. "
                f"input_path={resolved_input}, run_root={resolved_run_root}"
            )


class ResearchCodeWorkflow:
    def __init__(self, registry) -> None:
        self.registry = list(registry)

    def generate_and_review(
        self,
        *,
        accepted_card_text: str,
        helper_provider,
        generator: CodeGenerator,
        tracer_provider,
        critique_provider,
        run_root: Path,
        helper_policy: str = "",
        critique_context: str = "",
        default_helpers: tuple[str, ...] = (),
        critique_runs: int = 1,
        input_paths: Sequence[Path] | None = None,
        input_path: Path | None = None,
        fixer_provider=None,
        max_retries: int = 0,
        max_fix_attempts: int | None = None,
    ) -> tuple[str, list[str]]:
        if input_paths is not None and input_path is not None:
            raise ValueError("Specify input_paths or input_path, not both.")
        if input_paths is None:
            input_paths = (input_path,) if input_path is not None else ()
        else:
            input_paths = tuple(input_paths)

        if max_fix_attempts is not None:
            if max_retries:
                raise ValueError(
                    "Specify max_retries or max_fix_attempts, not both."
                )
            max_retries = max_fix_attempts

        layout = RunLayout(run_root)
        layout.create()
        _validate_input_paths(input_paths, run_root)
        accepted_path = layout.cards / "accepted.txt"
        accepted_path.write_text(
            accepted_card_text.rstrip() + "\n",
            encoding="utf-8",
        )

        selection, helper_raw = select_helpers(
            accepted_card_text,
            self.registry,
            helper_provider,
            policy=helper_policy,
        )
        write_selection(selection, layout.helpers / "selection.json")
        write_summary(selection, layout.helpers / "summary.txt")
        (layout.helpers / "raw_response.txt").write_text(
            helper_raw.rstrip() + "\n",
            encoding="utf-8",
        )

        generation_card = update_card_with_helpers(
            accepted_card_text,
            selection,
            default_helpers=default_helpers,
        )
        (layout.cards / "generation.txt").write_text(
            generation_card,
            encoding="utf-8",
        )

        generated = generator.generate(
            GenerationRequest(card_text=generation_card)
        )
        source_dir = layout.generation / "src"
        source_dir.mkdir(parents=True, exist_ok=True)
        code_path = source_dir / "analysis.py"
        final_code = generated.code
        code_path.write_text(final_code.rstrip() + "\n", encoding="utf-8")
        for index, raw in enumerate(generated.raw_responses, start=1):
            (layout.generation / f"response_{index:03d}.txt").write_text(
                raw.rstrip() + "\n",
                encoding="utf-8",
            )
        (layout.generation / "result.json").write_text(
            json.dumps(generated.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

        if input_paths:
            final_code = self._execute_fix_and_regenerate(
                code_path=code_path,
                input_paths=input_paths,
                execution_dir=layout.execution,
                generation_info_dir=layout.execution_info,
                generator=generator,
                generation_request=GenerationRequest(
                    card_text=generation_card
                ),
                fixer_provider=fixer_provider,
                max_retries=max_retries,
            )

        tracer_text = run_tracer_stage(
            spec_text=generation_card,
            code_text=final_code,
            provider=tracer_provider,
            output_dir=layout.critique / "tracer",
        )
        critique_outputs = run_critique_stage(
            spec_text=generation_card,
            code_text=final_code,
            tracer_text=tracer_text,
            provider=critique_provider,
            output_dir=layout.critique / "findings",
            domain_context=critique_context,
            n_runs=critique_runs,
        )
        return final_code, critique_outputs

    def _execute_fix_and_regenerate(
        self,
        *,
        code_path: Path,
        input_paths: Sequence[Path],
        execution_dir: Path,
        generation_info_dir: Path,
        generator: CodeGenerator,
        generation_request: GenerationRequest,
        fixer_provider,
        max_retries: int,
    ) -> str:
        execution_dir.mkdir(parents=True, exist_ok=True)
        generation_info_dir.mkdir(parents=True, exist_ok=True)
        code = code_path.read_text(encoding="utf-8")
        final_code_path = execution_dir / "generated_analysis.py"

        attempt_id = 0

        def execute_attempt(
            candidate: str,
            phase: str,
            trial: int | None = None,
        ):
            nonlocal attempt_id
            attempt_id += 1
            code_path.write_text(
                candidate.rstrip() + "\n",
                encoding="utf-8",
            )
            final_code_path.write_text(
                candidate.rstrip() + "\n",
                encoding="utf-8",
            )
            result = execute_python(
                final_code_path.resolve(),
                [str(path.resolve()) for path in input_paths],
                working_directory=execution_dir,
            )
            prefix = f"attempt_{attempt_id:03d}_{phase}"
            trial_suffix = f"_trial_{trial}" if trial is not None else ""
            (
                generation_info_dir
                / f"{prefix}_executed{trial_suffix}.py"
            ).write_text(
                candidate.rstrip() + "\n",
                encoding="utf-8",
            )
            (
                generation_info_dir
                / f"{prefix}_stdout{trial_suffix}.txt"
            ).write_text(
                result.stdout,
                encoding="utf-8",
            )
            (
                generation_info_dir
                / f"{prefix}_stderr{trial_suffix}.txt"
            ).write_text(
                result.stderr,
                encoding="utf-8",
            )
            (
                generation_info_dir
                / f"{prefix}_returncode{trial_suffix}.txt"
            ).write_text(
                str(result.returncode),
                encoding="utf-8",
            )
            (
                generation_info_dir
                / f"{prefix}_result{trial_suffix}.json"
            ).write_text(
                json.dumps(
                    {
                        "returncode": result.returncode,
                        "succeeded": result.succeeded,
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            if result.succeeded:
                # Generic stdout artifact.  Keep cutflow.txt as a
                # compatibility alias for existing analysis runs.
                (execution_dir / "stdout.txt").write_text(
                    result.stdout,
                    encoding="utf-8",
                )
                (execution_dir / "cutflow.txt").write_text(
                    result.stdout,
                    encoding="utf-8",
                )
            return result, attempt_id

        result, _ = execute_attempt(code, "initial")
        if result.succeeded or fixer_provider is None:
            return code

        for trial in range(1, max_retries + 1):
            code_before_fix = code
            error_before_fix = result.stderr
            fixed, raw = fix_code(
                code_before_fix,
                error_before_fix,
                fixer_provider,
            )
            result, fix_attempt = execute_attempt(fixed, "fix", trial)
            fix_prefix = f"attempt_{fix_attempt:03d}_fix"
            (
                generation_info_dir
                / f"{fix_prefix}_input_trial_{trial}.py"
            ).write_text(
                code_before_fix.rstrip() + "\n",
                encoding="utf-8",
            )
            (
                generation_info_dir
                / f"{fix_prefix}_error_trial_{trial}.txt"
            ).write_text(
                error_before_fix,
                encoding="utf-8",
            )
            (
                generation_info_dir
                / f"{fix_prefix}_raw_trial_{trial}.txt"
            ).write_text(
                raw.rstrip() + "\n",
                encoding="utf-8",
            )
            if result.succeeded:
                return fixed

            regenerated = generator.generate(generation_request)
            code = regenerated.code
            result, regen_attempt = execute_attempt(code, "regen", trial)
            regen_prefix = f"attempt_{regen_attempt:03d}_regen"
            (
                generation_info_dir
                / f"{regen_prefix}_raw_trial_{trial}.txt"
            ).write_text(
                code.rstrip() + "\n",
                encoding="utf-8",
            )
            for response_index, response in enumerate(
                regenerated.raw_responses,
                start=1,
            ):
                (
                    generation_info_dir
                    / (
                        f"regen_response_trial_{trial}_"
                        f"{response_index:03d}.txt"
                    )
                ).write_text(
                    response.rstrip() + "\n",
                    encoding="utf-8",
                )
            if result.succeeded:
                return code

        return code
