#!/usr/bin/env python3
"""
critique_runner.py — LLM-based semantic critique of generated code.

Sends SPEC + TRACER OUTPUT to a HuggingFace-hosted LLM and collects
structured findings over multiple runs, with optional repair pass and
heuristic filtering.

Configuration
-------------
Environment variables:
    HF_TOKEN          : HuggingFace API token (required)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from .providers.base import ChatProvider
from .prompts import load_prompt


# ============================================================
# Helpers
# ============================================================

def add_line_numbers(text: str) -> str:
    """Return *text* with 4-digit line numbers prepended."""
    return "\n".join(
        f"{i + 1:04d}: {line}"
        for i, line in enumerate(text.splitlines())
    )


def clean_model_text(text: str) -> str:
    """Strip ``<think>…</think>`` blocks emitted by some models."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def strip_code_fences(text: str) -> str:
    return text.replace("```", "").strip()


def needs_critique_repair(text: str) -> bool:
    """Return True when the output seems structurally incomplete."""
    required_markers = ["⚠️", "❓", "🌟", "Reason:", "Evidence priority:", "Generator bias:"]
    missing = [m for m in required_markers if m not in text]
    return len(missing) > 0


def append_non_overlapping_findings(text1: str, text2: str) -> str:
    t1 = text1.strip()
    t2 = text2.strip()
    if t2.startswith(t1):
        t2 = t2[len(t1):].lstrip("- \n`")
    if not t2:
        return t1
    return (t1 + "\n\n---\n\n" + t2).strip()


def dedupe_critique_findings(text: str) -> str:
    chunks = [c.strip() for c in text.split("\n---\n") if c.strip()]
    seen: set[str] = set()
    kept: list[str] = []
    for chunk in chunks:
        key = re.sub(r"\s+", " ", chunk).strip()
        if key not in seen:
            seen.add(key)
            kept.append(chunk)
    return "\n\n---\n\n".join(kept).strip()


# ============================================================
# Finding-level filter
# ============================================================

# Default drop signals — domain-agnostic noise patterns commonly
# produced by LLMs when critiquing analysis code.  Users can
# supply a custom filter file via --drop-signals to override.
DEFAULT_DROP_SIGNALS = [
    "matches the spec",
    "correctly implements the spec",
    "plot range",
    "inclusive",
    "exclusive",
    "does not include the cut condition",
    "apply this cut later",
    "applied later",
    "before or after other selection cuts",
    "before or after selection cuts",
]


def load_drop_signals(path: Path | None) -> list[str]:
    """Load drop signals from a file (one per line) or return defaults."""
    if path is None:
        return DEFAULT_DROP_SIGNALS
    lines = path.read_text(encoding="utf-8").splitlines()
    return [l.strip().lower() for l in lines if l.strip() and not l.startswith("#")]


def split_findings(text: str) -> list[str]:
    """Split critique output into individual finding blocks."""
    pattern = r"(?=^(?:⚠️|❓|🌟)\s)"
    blocks = re.split(pattern, text, flags=re.MULTILINE)
    return [b.strip() for b in blocks if b.strip()]


def should_keep_finding(block: str, drop_signals: list[str]) -> tuple[bool, str]:
    """Heuristic filter — remove obvious noise, keep candidates for review."""
    text = block.lower()

    for sig in drop_signals:
        if sig in text:
            return False, f"drop: matched noise signal '{sig}'"

    return True, "keep: no obvious noise signal"


def filter_findings(
    text: str, drop_signals: list[str]
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return (kept, dropped) lists of (block, reason) tuples."""
    blocks = split_findings(text)
    kept, dropped = [], []
    for b in blocks:
        keep, reason = should_keep_finding(b, drop_signals)
        (kept if keep else dropped).append((b, reason))
    return kept, dropped


# ============================================================
# API call
# ============================================================

def call_hf(
    messages: list[dict],
    *,
    provider: ChatProvider,
    temperature: float = 0.0,
    max_tokens: int = 8000,
) -> dict:
    completion = provider.complete(
        messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return completion.raw


# ============================================================
# Single-run with optional repair
# ============================================================

def run_critique_single(
    messages: list[dict],
    *,
    provider: ChatProvider,
    temperature: float,
    max_tokens: int,
    enable_repair: bool = True,
) -> tuple[str, list[dict]]:
    """
    Execute one critique call.  If the output looks incomplete and
    *enable_repair* is True, issue a follow-up repair request.

    Returns (final_text, raw_responses).
    """
    data = call_hf(messages, provider=provider,
                   temperature=temperature, max_tokens=max_tokens)
    text = clean_model_text(data["choices"][0]["message"]["content"])
    raws = [data]

    finish_reason = data["choices"][0].get("finish_reason")
    if enable_repair and finish_reason == "stop" and needs_critique_repair(text):
        repair_messages = messages + [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": (
                    "Your previous answer is incomplete or does not fully "
                    "follow the required output format. Continue or repair the "
                    "structured finding list using the same domain-specific "
                    "finding categories and the generic output rules. Do not "
                    "restate findings that are already complete. Do not introduce "
                    "findings unless they are grounded in the TRACER OUTPUT. Use "
                    "CODE only as supporting evidence. Return only additional "
                    "or corrected finding blocks in the required format."
                ),
            },
        ]
        data2 = call_hf(repair_messages, provider=provider,
                        temperature=temperature, max_tokens=max_tokens)
        text2 = clean_model_text(data2["choices"][0]["message"]["content"])
        raws.append(data2)
        text = append_non_overlapping_findings(text, text2)
        text = dedupe_critique_findings(text)

    text = strip_code_fences(text)
    return text, raws


# ============================================================
# Main
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run LLM-based semantic critique of generated code.",
    )
    p.add_argument("--spec", required=True, type=Path,
                   help="Path to spec.txt")
    p.add_argument("--tracer-output", required=True, type=Path,
                   help="Path to the tracer output file (e.g. final_output.txt)")
    p.add_argument("--code", type=Path, default=None,
                   help="Path to target code file (optional, included in user prompt if given)")
    p.add_argument("--domain-prompt", required=True, type=Path,
                   help="Path to a domain context prompt")
    p.add_argument("--critique-prompt", required=True, type=Path,
                   help="Path to critique_system_prompt.txt")
    p.add_argument("--output-rules-prompt", type=Path, default=None,
                   help="Path to critique_output_rules.txt. If omitted, use the packaged generic output rules.")
    p.add_argument("--model", default="Qwen/Qwen3-8B",
                   help="HuggingFace model ID")
    p.add_argument("--n-runs", type=int, default=5,
                   help="Number of independent critique runs")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-tokens", type=int, default=8000)
    p.add_argument("--enable-repair", action="store_true", default=False,
                   help="Enable the repair (follow-up) pass for incomplete outputs")
    p.add_argument("--drop-signals", type=Path, default=None,
                   help="Optional file with drop-signal phrases (one per line). "
                        "If omitted, built-in domain-agnostic defaults are used.")
    p.add_argument("--output-dir", type=Path, default=Path("output"),
                   help="Directory for output files")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)

    # --- HF token from environment ---
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        sys.exit("ERROR: environment variable HF_TOKEN is not set.")

    # --- Load drop signals ---
    drop_signals = load_drop_signals(args.drop_signals)

    # --- Load input files ---
    domain_prompt = args.domain_prompt.read_text(encoding="utf-8").strip()
    critique_prompt = args.critique_prompt.read_text(encoding="utf-8").strip()
    if args.output_rules_prompt is not None:
        output_rules_prompt = args.output_rules_prompt.read_text(encoding="utf-8").strip()
    else:
        output_rules_prompt = load_prompt("critique_output_rules").strip()
    # Prompt order is intentional: generic critique protocol first, then
    # domain-dependent semantic rules/categories, then generic output rules.
    system_prompt = "\n\n".join([critique_prompt, domain_prompt, output_rules_prompt])
    # Qwen3: disable thinking mode via prompt-level directive
    system_prompt = "/no_think\n\n" + system_prompt

    spec = args.spec.read_text(encoding="utf-8").strip()
    tracer_output = args.tracer_output.read_text(encoding="utf-8").strip()

    user_sections = [f"=== SPEC ===\n{spec}"]

    if args.code is not None:
        code = args.code.read_text(encoding="utf-8")
        code_numbered = add_line_numbers(code)
        user_sections.append(f"=== CODE ===\n{code_numbered}")

    user_sections.append(f"=== TRACER OUTPUT ===\n{tracer_output}")
    user_prompt = "\n\n".join(user_sections)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # --- Prepare output directory ---
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    from .providers.huggingface import HuggingFaceRouterProvider

    provider = HuggingFaceRouterProvider(args.model, token=hf_token)

    # --- Multi-run ---
    n_runs = args.n_runs
    all_texts: list[str] = []

    for i in range(n_runs):
        print(f"\n===== RUN {i + 1}/{n_runs} =====")
        text, raws = run_critique_single(
            messages,
            provider=provider,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            enable_repair=args.enable_repair,
        )
        print(text[:2000])
        all_texts.append(text)

        (out / f"critique_output_run{i + 1}.txt").write_text(text, encoding="utf-8")
        for j, raw in enumerate(raws):
            (out / f"critique_raw_run{i + 1}_call{j + 1}.json").write_text(
                json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    # --- Combined output ---
    combined_lines: list[str] = []
    for i, text in enumerate(all_texts, start=1):
        combined_lines.append(f"===== CRITIQUE OUTPUT RUN {i} =====")
        combined_lines.append(text)
        combined_lines.append("")
    (out / "critique_outputs_all.txt").write_text(
        "\n".join(combined_lines), encoding="utf-8"
    )

    # --- Filtered review ---
    filtered_lines: list[str] = []
    for i, text in enumerate(all_texts, start=1):
        kept, dropped = filter_findings(text, drop_signals)
        filtered_lines.append(f"===== RUN {i} =====")
        filtered_lines.append("")
        filtered_lines.append("---- KEPT ----")
        if kept:
            for j, (block, reason) in enumerate(kept, start=1):
                filtered_lines.append(f"[KEPT {j}] {reason}")
                filtered_lines.append(block)
                filtered_lines.append("")
        else:
            filtered_lines.append("(none)")
            filtered_lines.append("")
        filtered_lines.append("---- DROPPED ----")
        if dropped:
            for j, (block, reason) in enumerate(dropped, start=1):
                filtered_lines.append(f"[DROPPED {j}] {reason}")
                filtered_lines.append(block)
                filtered_lines.append("")
        else:
            filtered_lines.append("(none)")
            filtered_lines.append("")
        filtered_lines.append("")

    filtered_text = "\n".join(filtered_lines)
    (out / "critique_filtered_review.txt").write_text(filtered_text, encoding="utf-8")

    # --- Summary ---
    print("\nSaved files:")
    for i in range(n_runs):
        print(f"  {out}/critique_output_run{i + 1}.txt")
    print(f"  {out}/critique_outputs_all.txt")
    print(f"  {out}/critique_filtered_review.txt")
    print(f"\n===== FILTERED REVIEW PREVIEW =====")
    print(filtered_text[:4000])


if __name__ == "__main__":
    main()
