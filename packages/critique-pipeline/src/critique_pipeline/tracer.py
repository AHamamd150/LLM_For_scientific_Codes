#!/usr/bin/env python3
"""
tracer.py — LLM-based "AS-IMPLEMENTED SPEC" extraction.

Sends SPEC + CODE to a HuggingFace-hosted LLM in a multi-round
conversation (handling ``finish_reason=length`` continuations and
definition-summary repair), then post-processes the output.

Configuration
-------------
Environment variables:
    HF_TOKEN : HuggingFace API token (required)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import string
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from .providers.base import ChatProvider


# ============================================================
# Text helpers
# ============================================================

def add_line_numbers(text: str) -> str:
    return "\n".join(
        f"{i + 1:04d}: {line}"
        for i, line in enumerate(text.splitlines())
    )


def safe_template_expand(template: str, variables: dict[str, str]) -> str:
    """
    Expand {key} placeholders in *template* using *variables*,
    but leave unknown ``{...}`` sequences (e.g. Python braces in
    code) untouched instead of raising KeyError.
    """

    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return "{" + key + "}"

    return string.Formatter().vformat(template, (), SafeDict(variables))


def clean_model_text(text: str) -> str:
    """Strip ``<think>…</think>`` blocks emitted by some models."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def drop_incomplete_last_line(text: str) -> str:
    """Placeholder — currently returns text unchanged."""
    return text


def _find_all_summary_positions(text: str, marker: str) -> list[int]:
    """Return all character positions where *marker* appears in *text*."""
    positions: list[int] = []
    search_from = 0
    while True:
        pos = text.find(marker, search_from)
        if pos == -1:
            break
        positions.append(pos)
        search_from = pos + len(marker)
    return positions


# Matches summary headers emitted in any of these forms:
# - "SECTION 2: * [CHECK CAREFULLY] DEFINITION SUMMARY"
# - "SECTION 2: DEFINITION SUMMARY" followed by the canonical marker
# - "* [CHECK CAREFULLY] DEFINITION SUMMARY"
# - "[CHECK CAREFULLY] DEFINITION SUMMARY"
_SUMMARY_MARKER_RE = re.compile(
    r"^(?:SECTION\s*2\s*:\s*)?\*?\s*\[CHECK CAREFULLY\]\s*DEFINITION SUMMARY",
    re.MULTILINE,
)
_SUMMARY_MARKER_CANONICAL = "* [CHECK CAREFULLY] DEFINITION SUMMARY"


def _find_summary_first_last(text: str) -> tuple[int, int]:
    """Return (first, last) character positions of any DEFINITION SUMMARY marker.
    Returns (-1, -1) if not found.
    """
    matches = list(_SUMMARY_MARKER_RE.finditer(text))
    if not matches:
        return -1, -1
    return matches[0].start(), matches[-1].start()


def _find_all_summary_positions_re(text: str) -> list[int]:
    """Return all start positions of DEFINITION SUMMARY markers (both forms)."""
    return [m.start() for m in _SUMMARY_MARKER_RE.finditer(text)]


def _extract_spec_bullet_lines(text: str, summary_positions: list[int],
                                marker: str) -> list[str]:
    """Return SPEC BULLET ANALYSIS lines from *text*.

    Two bullet styles are recognised:
    - Marked:  ✅/⚠️/❓/🌟 at the start of the line  (8B-style)
    - Bare:    "* <text>" lines that contain BOTH "; computed as:" AND "〔L"
               (14B-style, markers omitted). Requiring both discriminators
               avoids false-positive matches on DEFINITION SUMMARY sub-entry
               headers (which are also bare ``* name`` lines but lack 〔L〕).

    Note: bare DEFINITION SUMMARY sub-entries look like:
        * ditau invariant mass
    They never contain "〔L" or "; computed as:", so requiring both guards
    against accidentally treating them as SPEC bullets.
    """
    marked_re = re.compile(r"^(?:✅|⚠️|❓|🌟)\s*\*")
    # Require BOTH "; computed as:" and "〔L" to distinguish SPEC bullets from
    # DEFINITION SUMMARY sub-entry headers.
    bare_spec_re = re.compile(r"^\*\s+.+;\s*computed as:.+〔L")

    result: list[str] = []
    for line in text.splitlines():
        stripped = line.rstrip()
        if marked_re.match(stripped) or bare_spec_re.match(stripped):
            result.append(stripped)

    return result


def keep_only_last_definition_summary(text: str) -> str:
    """If there are duplicate DEFINITION SUMMARY sections, keep only the last,
    but NEVER discard SPEC BULLET ANALYSIS lines.

    Handles:
    - Marker with leading ``*`` (canonical form) or without (14B bare form).
    - Marker-prefixed bullets (✅/⚠️/❓/🌟) and bare ``* `` bullets.

    Strategy:
    - Identify all DEFINITION SUMMARY block positions (both marker forms).
    - Collect SPEC BULLET lines from regions *outside* all summary blocks.
    - Keep the last DEFINITION SUMMARY block verbatim.
    - Reconstruct output preserving original order (bullets-first or summary-first).
    """
    first_idx, last_idx = _find_summary_first_last(text)
    if first_idx == -1:
        return text  # no summary at all — leave unchanged
    if last_idx == first_idx:
        return text  # only one copy — nothing to deduplicate

    summary_positions = _find_all_summary_positions_re(text)
    last_summary = text[last_idx:].strip()

    spec_bullet_lines = _extract_spec_bullet_lines(
        text, summary_positions, _SUMMARY_MARKER_CANONICAL
    )
    spec_bullets_text = "\n".join(spec_bullet_lines).strip()

    if not spec_bullets_text:
        # No SPEC bullets found outside summary blocks — just return last summary.
        return last_summary

    # Preserve original order: bullets-first if the first SPEC bullet appeared
    # before the first DEFINITION SUMMARY marker.
    marked_re = re.compile(r"^(?:✅|⚠️|❓|🌟)\s*\*", re.MULTILINE)
    bare_spec_re = re.compile(r"^\*\s+.+(?:;\s*computed as:|〔L)", re.MULTILINE)
    candidates = [m.start() for m in
                  [marked_re.search(text), bare_spec_re.search(text)]
                  if m is not None]
    first_bullet_pos = min(candidates) if candidates else None

    bullets_before_summary = (
        first_bullet_pos is not None and first_bullet_pos < first_idx
    )

    if bullets_before_summary:
        return (spec_bullets_text + "\n\n" + last_summary).strip()
    else:
        return (last_summary + "\n\n" + spec_bullets_text).strip()


def needs_definition_summary_repair(text: str) -> bool:
    """Return True if the accumulated text is missing a complete DEFINITION SUMMARY.
    Accepts both the canonical marker form and the bare form (no leading ``*``).
    """
    if not _SUMMARY_MARKER_RE.search(text):
        return True
    if "collection definition:" not in text:
        return True
    if "structure:" not in text:
        return True
    return False


def _trim_incomplete_tail_with_header(text: str) -> tuple[str, str | None]:
    """Trim an incomplete trailing DEFINITION SUMMARY entry.

    Returns ``(trimmed_text, removed_header)``.  ``removed_header`` is the entry
    header that was removed, for example ``"* diphoton"``.  The merge step can
    then restore this header if the continuation starts directly with field
    lines such as ``"  - computed/defined as: ..."``.

    This prevents length-cut continuations from producing headerless entries
    when the previous chunk contained the header but the next chunk resumed at
    the first field line.
    """
    lines = text.rstrip().splitlines()
    if not lines:
        return text, None

    entry_header_re = re.compile(r"^\*\s+(?!\[CHECK CAREFULLY\]).+")
    structure_re = re.compile(r"^\s*-\s*structure\s*:")

    last_structure_idx = -1
    for i in range(len(lines) - 1, -1, -1):
        if structure_re.match(lines[i]):
            last_structure_idx = i
            break

    if last_structure_idx == len(lines) - 1:
        return text, None  # last line IS a structure line → entry is complete

    incomplete_header_idx: int | None = None
    incomplete_header: str | None = None
    for i in range(last_structure_idx + 1, len(lines)):
        if entry_header_re.match(lines[i].rstrip()):
            incomplete_header_idx = i
            incomplete_header = lines[i].rstrip()
            break

    if incomplete_header_idx is None:
        return text, None

    # Preserve everything before the incomplete entry.  If no previous complete
    # entry exists, keep the text before the incomplete header rather than
    # dropping the whole accumulated answer.
    trim_to = last_structure_idx + 1 if last_structure_idx >= 0 else incomplete_header_idx
    trimmed = "\n".join(lines[:trim_to]).rstrip()
    return trimmed, incomplete_header


def _trim_incomplete_tail(text: str) -> str:
    """Backward-compatible wrapper returning only the trimmed text."""
    trimmed, _header = _trim_incomplete_tail_with_header(text)
    return trimmed


def _trim_leading_incomplete_entry(text: str) -> str:
    """If *text* begins with a DEFINITION SUMMARY entry that is missing its
    ``  - computed/defined as:`` (or ``  - computed as:``) field — which happens
    when the model resumes a continuation at a mid-entry point — drop that
    leading incomplete entry so the merge produces a clean join.

    Only drops the first entry if it lacks the computed field.  All subsequent
    entries are left untouched.
    """
    lines = text.lstrip().splitlines()
    if not lines:
        return text

    entry_header_re = re.compile(r"^\*\s+(?!\[CHECK CAREFULLY\]).+")
    computed_re = re.compile(r"^\s*-\s*computed")

    # If the text doesn't start with a bare entry header, nothing to trim.
    if not entry_header_re.match(lines[0].rstrip()):
        return text

    # Find where the first entry ends (next entry header or end-of-text).
    first_entry_end = len(lines)
    for i in range(1, len(lines)):
        if entry_header_re.match(lines[i].rstrip()):
            first_entry_end = i
            break

    # Check whether the first entry contains a computed field.
    first_entry_lines = lines[:first_entry_end]
    has_computed = any(computed_re.match(l) for l in first_entry_lines)

    if has_computed:
        return text  # first entry is complete enough — leave it

    # Drop the first incomplete entry.
    return "\n".join(lines[first_entry_end:]).lstrip()


def merge_with_overlap(previous: str, new: str, min_overlap_lines: int = 2) -> str:
    """Merge two continuation chunks, detecting overlapping tails.

    Before merging:
    - Trims any incomplete DEFINITION SUMMARY entry from the tail of *previous*
      (handles length cut-off mid-entry).
    - If that trim removed an entry header and *new* resumes directly at a
      field line, restores the removed header before merging.
    - Trims any leading incomplete DEFINITION SUMMARY entry from *new*
      (handles the model resuming at a slightly different point than the cut-off).
    """
    previous, incomplete_header = _trim_incomplete_tail_with_header(previous)
    new = _trim_leading_incomplete_entry(new)

    if incomplete_header is not None:
        new_stripped = new.lstrip()
        first_new_line = new_stripped.splitlines()[0] if new_stripped.splitlines() else ""
        field_line_re = re.compile(
            r"^\s*-\s*(?:computed(?:/defined)? as|upstream chain|collection definition|structure)\s*:"
        )
        if field_line_re.match(first_new_line):
            new = incomplete_header + "\n" + new_stripped

    prev_lines = previous.splitlines()
    new_lines = new.splitlines()
    max_check = min(len(prev_lines), len(new_lines))

    for k in range(max_check, min_overlap_lines - 1, -1):
        if prev_lines[-k:] == new_lines[:k]:
            return "\n".join(prev_lines + new_lines[k:]).strip()

    # fallback: prefix match on boundary line
    while prev_lines and new_lines:
        last_prev = prev_lines[-1].strip()
        first_new = new_lines[0].strip()
        if last_prev and first_new.startswith(last_prev):
            prev_lines.pop()
            return ("\n".join(prev_lines).rstrip() + "\n" + "\n".join(new_lines)).strip()
        break

    return (previous.rstrip() + "\n" + new.lstrip()).strip()


# ============================================================
# Extracted-filtered collections (from extracted_filtered.py)
# ============================================================

def extract_definition_summary(text: str) -> str:
    start_match = _SUMMARY_MARKER_RE.search(text)
    if not start_match:
        return ""
    start = start_match.start()

    end_pat = re.compile(r"^\*\s*(✅|⚠️|❓|🌟)\s*\*", re.MULTILINE)
    end_match = end_pat.search(text, pos=start_match.end())
    end = end_match.start() if end_match else len(text)
    return text[start:end].strip()


def parse_definition_summary(
    summary_text: str,
) -> List[Dict[str, Optional[str]]]:
    lines = summary_text.splitlines()
    header_re = re.compile(r"^\*\s+(?!\[CHECK CAREFULLY\])(.*\S)\s*$")
    field_re = re.compile(r"^\s*-\s*([^:]+):\s*(.*)\s*$")

    entries: List[Dict[str, Optional[str]]] = []
    current: Optional[Dict[str, Optional[str]]] = None

    for raw_line in lines:
        line = raw_line.rstrip()
        header_match = header_re.match(line)
        if header_match:
            if current:
                entries.append(current)
            current = {
                "name": header_match.group(1).strip(),
                "computed_defined_as": None,
                "upstream_chain": None,
                "collection_definition": None,
                "structure": None,
            }
            continue
        if current is None:
            continue
        field_match = field_re.match(line)
        if field_match:
            key = field_match.group(1).strip().lower()
            value = field_match.group(2).strip()
            if key == "computed/defined as":
                current["computed_defined_as"] = value
            elif key == "upstream chain":
                current["upstream_chain"] = value
            elif key == "collection definition":
                current["collection_definition"] = value
            elif key == "structure":
                current["structure"] = value

    if current:
        entries.append(current)
    return entries


def extract_collections_from_entries(
    entries: List[Dict[str, Optional[str]]],
) -> Dict[str, Dict[str, Any]]:
    collections: Dict[str, Dict[str, Any]] = {}
    collection_re = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")

    for entry in entries:
        cdef = entry.get("collection_definition")
        if not cdef or cdef == "None":
            continue
        cdef = cdef.strip("` ")  # LLM often wraps expressions in backticks
        m = collection_re.match(cdef)
        if not m:
            continue
        cname = m.group(1).strip()
        cexpr = m.group(2).strip()
        if cname not in collections:
            collections[cname] = {
                "name": cname,
                "definition": cexpr,
                "used_by": [],
            }
        collections[cname]["used_by"].append(entry["name"])

    # dedupe used_by lists
    for cname in collections:
        seen: set[str] = set()
        unique = []
        for x in collections[cname]["used_by"]:
            if x not in seen:
                unique.append(x)
                seen.add(x)
        collections[cname]["used_by"] = unique

    return collections


def extract_filtered_objects_from_trace(
    text: str,
) -> Dict[str, Dict[str, Any]]:
    summary = extract_definition_summary(text)
    if not summary:
        return {}
    entries = parse_definition_summary(summary)
    return extract_collections_from_entries(entries)


# ============================================================
# API call
# ============================================================

def call_hf(
    messages: list[dict],
    *,
    provider: ChatProvider,
    max_tokens: int = 1500,
    temperature: float = 0.0,
    round_idx: int = 0,
    output_dir: Path | None = None,
) -> tuple[str, str | None, dict]:
    completion = provider.complete(
        messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if output_dir is not None:
        (output_dir / f"round_{round_idx + 1}_raw_response.json").write_text(
            json.dumps(completion.raw, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return completion.content, completion.finish_reason, completion.raw


# ============================================================
# Multi-round conversation loop
# ============================================================

CONTINUE_PROMPT = (
    "Continue from the next unfinished line only. "
    "Do not repeat any completed bullet or sub-bullet. "
    "If the previous response stopped in the middle of a line, "
    "restart from that incomplete line once, then continue normally. "
    "Do not repeat the definition summary."
)

REPAIR_PROMPT = (
    "Your previous answer is missing the required CHECK CAREFULLY definition tracing.\n"
    "The SPEC BULLET ANALYSIS with line references is already present — do NOT repeat it.\n"
    "Only add the section exactly headed:\n"
    "* [CHECK CAREFULLY] DEFINITION SUMMARY\n\n"
    "For each derived quantity, include:\n"
    "- computed as:\n"
    "- upstream chain:\n"
    "- collection definition:\n"
    "- structure:\n\n"
    "Do not stop at variable aliases or helper function names.\n"
    "Trace each quantity upstream until the nearest selected, filtered, "
    "or redefined collection is identified.\n"
    "State that collection's definition expression explicitly.\n"
    "Output ONLY the definition summary section, nothing else."
)

MAX_REPAIR_ATTEMPTS = 2


def run_tracer(
    messages: list[dict],
    *,
    provider: ChatProvider,
    max_tokens_per_round: int,
    temperature: float,
    max_rounds: int,
    output_dir: Path,
) -> str:
    """
    Run the multi-round tracing conversation and return the merged
    final text.
    """
    all_parts: list[str] = []
    repair_count = 0

    for round_idx in range(max_rounds):
        text, finish_reason, _data = call_hf(
            messages,
            provider=provider,
            max_tokens=max_tokens_per_round,
            temperature=temperature,
            round_idx=round_idx,
            output_dir=output_dir,
        )
        cleaned = clean_model_text(text)

        (output_dir / f"round_{round_idx + 1}_text.txt").write_text(
            text, encoding="utf-8"
        )

        if finish_reason == "length":
            cleaned = drop_incomplete_last_line(cleaned)

        print(f"[round {round_idx + 1}] finish_reason = {finish_reason}")

        # --- stop with possible repair ---
        if finish_reason == "stop":
            all_parts.append(cleaned)
            # Check the full accumulated text, not just the last round's output.
            accumulated = "\n".join(all_parts)
            if needs_definition_summary_repair(accumulated) and repair_count < MAX_REPAIR_ATTEMPTS:
                repair_count += 1
                print(f"[round {round_idx + 1}] definition summary incomplete in accumulated text, repair attempt {repair_count}/{MAX_REPAIR_ATTEMPTS}")
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content": REPAIR_PROMPT})
                continue
            else:
                if repair_count >= MAX_REPAIR_ATTEMPTS:
                    print(f"Warning: definition summary still incomplete after {MAX_REPAIR_ATTEMPTS} repair attempts; accepting as-is.")
                break

        # --- length: append and ask to continue ---
        all_parts.append(cleaned)

        if finish_reason == "length":
            messages.append({"role": "assistant", "content": text})
            messages.append({"role": "user", "content": CONTINUE_PROMPT})
        else:
            print(f"Warning: unusual finish_reason: {finish_reason}")
            break
    else:
        print("Warning: reached max_rounds before normal stop.")

    # --- merge parts ---
    final_text = ""
    for part in all_parts:
        if not part:
            continue
        if not final_text:
            final_text = part
        else:
            final_text = merge_with_overlap(final_text, part)

    final_text = keep_only_last_definition_summary(final_text)
    return final_text


# ============================================================
# Main
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run LLM-based AS-IMPLEMENTED SPEC extraction.",
    )
    p.add_argument("--spec", required=True, type=Path,
                   help="Path to the spec / user-input file")
    p.add_argument("--code", required=True, type=Path,
                   help="Path to the target code file")
    p.add_argument("--system-prompt", required=True, type=Path,
                   help="Path to tracer_system_prompt.txt")
    p.add_argument("--user-prompt-template", required=True, type=Path,
                   help="Path to trace_code.txt (contains {spec} and {code} placeholders)")
    p.add_argument("--model", default="Qwen/Qwen3-8B",
                   help="HuggingFace model ID")
    p.add_argument("--max-rounds", type=int, default=8,
                   help="Maximum conversation rounds")
    p.add_argument("--max-tokens-per-round", type=int, default=1500,
                   help="max_tokens per API call")
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--output-dir", type=Path, default=Path("output"),
                   help="Directory for output files")
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)

    # --- HF token ---
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        sys.exit("ERROR: environment variable HF_TOKEN is not set.")

    # --- Load inputs ---
    system_prompt = args.system_prompt.read_text(encoding="utf-8").strip()
    # Qwen3: disable thinking mode via prompt-level directive
    system_prompt = "/no_think\n\n" + system_prompt
    user_prompt_template = args.user_prompt_template.read_text(encoding="utf-8").strip()

    spec = args.spec.read_text(encoding="utf-8").strip()
    code = args.code.read_text(encoding="utf-8")
    code_numbered = add_line_numbers(code)

    # Safe expansion: {spec} and {code} are replaced; other braces
    # (e.g. Python dict literals, f-strings in the code) are preserved.
    user_prompt = safe_template_expand(
        user_prompt_template, {"spec": spec, "code": code_numbered}
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # --- Output directory ---
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    # --- Run multi-round conversation ---
    from .providers.huggingface import HuggingFaceRouterProvider

    final_text = run_tracer(
        messages,
        provider=HuggingFaceRouterProvider(args.model, token=hf_token),
        max_tokens_per_round=args.max_tokens_per_round,
        temperature=args.temperature,
        max_rounds=args.max_rounds,
        output_dir=out,
    )

    (out / "final_output.txt").write_text(final_text, encoding="utf-8")
    print("\n=== FINAL OUTPUT ===\n")
    print(final_text)

    # --- Extract filtered/selected collections ---
    collections = extract_filtered_objects_from_trace(final_text)

    lines = ["=== Extracted filtered/selected collections ==="]
    for name, info in collections.items():
        lines.append(f"- {name}")
        lines.append(f"  definition: {info['definition']}")
        lines.append(f"  used_by: {info['used_by']}")
        lines.append("")

    collections_text = "\n".join(lines)
    (out / "extracted_collections.txt").write_text(collections_text, encoding="utf-8")
    print(collections_text)


if __name__ == "__main__":
    main()
