from __future__ import annotations

from .models import HelperSpec


SYSTEM_PROMPT = """You select helper functions from a fixed registry.

Your task is not to write implementation code. Your task is only to choose
helper functions from the provided registry for the given spec.

Closed-list rules:
- Select helper names exactly as they appear in the registry.
- Do not invent, rename, shorten, generalize, or alias helper names.
- If no registry entry matches an explicit requirement in the spec, do not create a new helper.

Selection rules:
- Cover explicit requirements in the spec.
- Select a helper only when it supports at least one explicit requirement in the spec.
- If a helper is not tied to any explicit requirement in the spec, do not select it.
- Reject superficially related helpers that are not justified by the spec.
- Prefer helpers whose stated semantics match the spec's stated inputs, outputs, objects, and processing workflow.
- Put a helper in `rejected_but_close` only when it appears relevant at first glance but is not justified by an explicit requirement in the spec.

Return JSON only:
{
  "selected_helpers": ["helper_name"],
  "rejected_but_close": ["other_helper"]
}
"""


def render_registry(registry: list[HelperSpec]) -> str:
    blocks: list[str] = []
    for helper in registry:
        lines = [
            f"- name: {helper.name}",
            f"  section: {helper.section}",
            f"  summary: {helper.summary}",
            f"  keywords: {', '.join(helper.keywords)}",
        ]
        if helper.aliases:
            lines.append(f"  aliases: {', '.join(helper.aliases)}")
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def build_user_prompt(
    spec_text: str,
    registry: list[HelperSpec],
    policy: str = "",
) -> str:
    policy_section = f"\nDOMAIN POLICY\n-------------\n{policy.strip()}\n" if policy else ""
    return f"""SPEC
----
{spec_text}

HELPER REGISTRY
---------------
{render_registry(registry)}
{policy_section}
Be strict: if a helper is not clearly required by the spec, do not select it.
"""
