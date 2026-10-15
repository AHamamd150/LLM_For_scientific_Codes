#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from openai import OpenAI


SYSTEM_PROMPT = """
You evaluate a code tracer for scientific analysis code.

The tracer is intended to construct an as-implemented specification: it
identifies how each explicit analysis element requested in the task card is
realized in the generated code, together with its relevant source location
and dependencies.

The task card defines which requested analysis elements should be traced,
while the generated code is the ground truth for what was actually implemented.

You are evaluating whether the tracer faithfully represents this relationship.
You are NOT evaluating whether the generated analysis correctly satisfies the
task card or whether the scientific analysis itself is correct.

For each explicit task-card requirement, judge:

1. traced
   - yes: the tracer clearly covers the requirement
   - partial: only part of the requirement is covered
   - no: the requirement is omitted

2. source_correct
   - yes: the code location/expression identified by the tracer is correct
   - no: it points to the wrong code
   - uncertain: cannot be determined confidently
   - na: use when traced=no

3. dependency_correct
   - yes: relevant helper/object/collection/composite dependencies are traced correctly
   - no: an important dependency is wrong or missing
   - uncertain: cannot be determined confidently
   - na: no nontrivial dependency is involved, or traced=no

4. hallucination
   - yes: the tracer attributes a code operation, dependency, selection, or source
     relation that is not supported by the supplied code
   - no: no such hallucination is present for this requirement
   - uncertain: cannot be determined confidently

Do NOT judge whether the implementation satisfies the intended physics.
Do NOT perform critique of the code.
Do NOT penalize mathematically equivalent code merely for using a different form.

Also report tracer claims that do not correspond to any task-card requirement
and are unsupported by the code as extra_trace_claims.

Return JSON only with this exact top-level structure:

{
  "requirements": [
    {
      "req_id": "R1",
      "requirement": "short faithful wording from the task card",
      "traced": "yes|partial|no",
      "source_correct": "yes|no|uncertain|na",
      "dependency_correct": "yes|no|uncertain|na",
      "hallucination": "yes|no|uncertain",
      "note": "brief reason, preferably citing code line numbers"
    }
  ],
  "extra_trace_claims": [
    {
      "claim": "brief description",
      "hallucination": "yes|uncertain",
      "note": "brief reason, preferably citing code line numbers"
    }
  ]
}

Extract the explicit requirements from the task card conservatively.
Do not invent requirements that are not stated there.
"""


def numbered_code(text: str) -> str:
    return "\n".join(
        f"{i:4d} | {line}"
        for i, line in enumerate(text.splitlines(), start=1)
    )


def parse_json_output(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--task-card", type=Path, required=True)
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-luna")
    args = parser.parse_args()

    task_card = args.task_card.read_text(encoding="utf-8")
    code_text = args.code.read_text(encoding="utf-8")
    trace = args.trace.read_text(encoding="utf-8")

    user_input = f"""Evaluate this tracer output.

## TASK CARD
{task_card}

## GENERATED CODE
{numbered_code(code_text)}

## TRACER OUTPUT
{trace}
"""

    client = OpenAI()
    response = client.responses.create(
        model=args.model,
        reasoning={"effort": "low"},
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        max_output_tokens=6000,
    )

    result = parse_json_output(response.output_text)
    rows = []

    for item in result.get("requirements", []):
        rows.append({
            "case": args.case,
            "run": args.run,
            "row_type": "requirement",
            "req_id": item.get("req_id", ""),
            "requirement_or_claim": item.get("requirement", ""),
            "traced": item.get("traced", ""),
            "source_correct": item.get("source_correct", ""),
            "dependency_correct": item.get("dependency_correct", ""),
            "hallucination": item.get("hallucination", ""),
            "note": item.get("note", ""),
        })

    for i, item in enumerate(result.get("extra_trace_claims", []), start=1):
        rows.append({
            "case": args.case,
            "run": args.run,
            "row_type": "extra_trace_claim",
            "req_id": f"EXTRA{i}",
            "requirement_or_claim": item.get("claim", ""),
            "traced": "",
            "source_correct": "",
            "dependency_correct": "",
            "hallucination": item.get("hallucination", ""),
            "note": item.get("note", ""),
        })

    fieldnames = [
        "case", "run", "row_type", "req_id", "requirement_or_claim",
        "traced", "source_correct", "dependency_correct",
        "hallucination", "note",
    ]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
