from __future__ import annotations

import re

from .models import SelectionResult


def update_card_with_helpers(
    card_text: str,
    selection: SelectionResult,
    *,
    default_helpers: tuple[str, ...] = (),
) -> str:
    names: list[str] = []
    seen: set[str] = set()
    for name in default_helpers + tuple(
        item.name for item in selection.selected_helpers
    ):
        if name not in seen:
            seen.add(name)
            names.append(name)

    section = "[ADDITIONAL_HELPERS]\n" + "\n".join(f"- {name}" for name in names)
    pattern = r"\[ADDITIONAL_HELPERS\].*?(?=\n\[|\Z)"
    if re.search(pattern, card_text, flags=re.DOTALL):
        return re.sub(pattern, section, card_text, flags=re.DOTALL).rstrip() + "\n"
    return card_text.rstrip() + "\n\n" + section + "\n"

