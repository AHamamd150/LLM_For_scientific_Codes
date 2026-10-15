from __future__ import annotations

import json
from typing import Any

from .models import HelperSpec, SelectionItem, SelectionResult
from .prompt import SYSTEM_PROMPT, build_user_prompt
from .providers.base import ChatProvider


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("No JSON object found in model output.")
        value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Model output must be a JSON object.")
    return value


def _normalize_items(
    values: Any,
    *,
    field: str,
    known_names: set[str],
) -> list[SelectionItem]:
    if not isinstance(values, list):
        raise ValueError(f"{field} must be a list.")

    items: list[SelectionItem] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str):
            item = SelectionItem(name=value.strip())
        elif isinstance(value, dict):
            name = value.get("name")
            reason = value.get("reason", "")
            if not isinstance(name, str) or not isinstance(reason, str):
                raise ValueError(f"Invalid entry in {field}.")
            item = SelectionItem(name=name.strip(), reason=reason.strip())
        else:
            raise ValueError(f"Invalid entry in {field}.")

        if not item.name or item.name not in known_names:
            raise ValueError(f"{field} contains unknown helper: {item.name!r}")
        if item.name not in seen:
            seen.add(item.name)
            items.append(item)
    return items


def resolve_model_output(
    model_output: str | dict[str, Any],
    registry: list[HelperSpec],
) -> SelectionResult:
    data = (
        extract_json_object(model_output)
        if isinstance(model_output, str)
        else model_output
    )
    by_name = {helper.name: helper for helper in registry}
    known_names = set(by_name)
    selected = _normalize_items(
        data.get("selected_helpers", []),
        field="selected_helpers",
        known_names=known_names,
    )
    rejected = _normalize_items(
        data.get("rejected_but_close", []),
        field="rejected_but_close",
        known_names=known_names,
    )

    expanded: list[SelectionItem] = []
    seen: set[str] = set()
    visiting: set[str] = set()

    def visit(name: str, reason: str = "") -> None:
        if name in seen:
            return
        if name in visiting:
            raise ValueError(f"Cyclic helper dependency involving {name}.")
        visiting.add(name)
        for dependency in by_name[name].dependencies:
            visit(dependency, reason=f"dependency of {name}")
        visiting.remove(name)
        seen.add(name)
        expanded.append(SelectionItem(name=name, reason=reason))

    for item in selected:
        visit(item.name, item.reason)

    selected_names = {item.name for item in expanded}
    return SelectionResult(
        selected_helpers=tuple(expanded),
        rejected_but_close=tuple(
            item for item in rejected if item.name not in selected_names
        ),
    )


def select_helpers(
    spec_text: str,
    registry: list[HelperSpec],
    provider: ChatProvider,
    *,
    policy: str = "",
) -> tuple[SelectionResult, str]:
    raw_response = provider.complete(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=build_user_prompt(spec_text, registry, policy),
    )
    return resolve_model_output(raw_response, registry), raw_response

