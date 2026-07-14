from __future__ import annotations

import json
from pathlib import Path

from .critique import (
    filter_findings,
    load_drop_signals,
    run_critique_single,
)
from .tracer import (
    add_line_numbers,
    extract_filtered_objects_from_trace,
    run_tracer,
    safe_template_expand,
)
from .prompts import load_prompt
from .providers.base import ChatProvider


def run_tracer_stage(
    *,
    spec_text: str,
    code_text: str,
    provider: ChatProvider,
    output_dir: Path,
    max_rounds: int = 8,
    max_tokens_per_round: int = 2500,
    temperature: float = 0.0,
) -> str:
    output_dir.mkdir(parents=True, exist_ok=True)
    user_prompt = safe_template_expand(
        load_prompt("trace_code"),
        {
            "spec": spec_text.strip(),
            "code": add_line_numbers(code_text),
        },
    )
    messages = [
        {
            "role": "system",
            "content": "/no_think\n\n"
            + load_prompt("tracer_system_prompt").strip(),
        },
        {"role": "user", "content": user_prompt},
    ]
    final_text = run_tracer(
        messages,
        provider=provider,
        max_tokens_per_round=max_tokens_per_round,
        temperature=temperature,
        max_rounds=max_rounds,
        output_dir=output_dir,
    )
    (output_dir / "final_output.txt").write_text(
        final_text.rstrip() + "\n",
        encoding="utf-8",
    )
    collections = extract_filtered_objects_from_trace(final_text)
    (output_dir / "collections.json").write_text(
        json.dumps(collections, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return final_text


def build_critique_messages(
    *,
    spec_text: str,
    tracer_text: str,
    code_text: str = "",
    domain_context: str = "",
) -> list[dict[str, str]]:
    # Prompt order is intentional: generic critique protocol first, then
    # domain-dependent semantic rules/categories, then generic output rules.
    system_parts = [load_prompt("critique_system_prompt").strip()]
    if domain_context.strip():
        system_parts.append(domain_context.strip())
    system_parts.append(load_prompt("critique_output_rules").strip())
    system_prompt = "\n\n".join(system_parts)
    sections = [f"=== SPEC ===\n{spec_text.strip()}"]
    if code_text:
        sections.append(f"=== CODE ===\n{add_line_numbers(code_text)}")
    sections.append(f"=== TRACER OUTPUT ===\n{tracer_text.strip()}")
    return [
        {"role": "system", "content": "/no_think\n\n" + system_prompt},
        {"role": "user", "content": "\n\n".join(sections)},
    ]

def run_critique_stage(
    *,
    spec_text: str,
    tracer_text: str,
    provider: ChatProvider,
    output_dir: Path,
    code_text: str = "",
    domain_context: str = "",
    n_runs: int = 1,
    temperature: float = 0.0,
    max_tokens: int = 8000,
    enable_repair: bool = True,
    drop_signals_path: Path | None = None,
) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    messages = build_critique_messages(
        spec_text=spec_text,
        tracer_text=tracer_text,
        code_text=code_text,
        domain_context=domain_context,
    )
    drop_signals = load_drop_signals(drop_signals_path)
    outputs: list[str] = []
    review: list[str] = []

    for index in range(1, n_runs + 1):
        text, raws = run_critique_single(
            messages,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
            enable_repair=enable_repair,
        )
        outputs.append(text)
        (output_dir / f"response_{index:03d}.txt").write_text(
            text.rstrip() + "\n",
            encoding="utf-8",
        )
        for call_index, raw in enumerate(raws, start=1):
            (output_dir / f"raw_{index:03d}_call_{call_index:02d}.json").write_text(
                json.dumps(raw, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        kept, dropped = filter_findings(text, drop_signals)
        review.extend([f"===== RUN {index} =====", "", "---- KEPT ----"])
        review.extend(_format_review_blocks(kept, "KEPT"))
        review.extend(["", "---- DROPPED ----"])
        review.extend(_format_review_blocks(dropped, "DROPPED"))
        review.append("")

    (output_dir / "filtered_review.txt").write_text(
        "\n".join(review).rstrip() + "\n",
        encoding="utf-8",
    )
    return outputs


def _format_review_blocks(
    blocks: list[tuple[str, str]],
    label: str,
) -> list[str]:
    if not blocks:
        return ["(none)"]
    lines: list[str] = []
    for index, (block, reason) in enumerate(blocks, start=1):
        lines.extend([f"[{label} {index}] {reason}", block, ""])
    return lines
