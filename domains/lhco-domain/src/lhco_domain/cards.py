from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CardSections:
    selection_cuts: str = ""
    plots_for_validation: str = ""
    output_structure: str = ""
    additional_helpers: str = ""


def parse_card(text: str) -> CardSections:
    def extract(tag: str) -> str:
        match = re.search(rf"\[{tag}\](.*?)(?=\n\[|\Z)", text, re.DOTALL)
        return match.group(1).strip() if match else ""

    return CardSections(
        selection_cuts=extract("SELECTION_CUTS"),
        plots_for_validation=extract("PLOTS_FOR_VALIDATION"),
        output_structure=extract("OUTPUT_STRUCTURE"),
        additional_helpers=extract("ADDITIONAL_HELPERS"),
    )

