from __future__ import annotations

from importlib.resources import files

from .cards import CardSections, parse_card


def _load_prompt(name: str) -> str:
    return files("lhco_domain").joinpath(
        "prompts", f"{name}.txt"
    ).read_text(encoding="utf-8")


def load_codegen_system_prompt() -> str:
    return _load_prompt("codegen_system")


def load_helper_policy() -> str:
    return _load_prompt("helper_policy")


def load_critique_context() -> str:
    return _load_prompt("critique_context")


def build_user_message(sections: CardSections) -> str:
    return f"""Generate a complete, executable Python script to analyze LHCO files.

[SELECTION_CUTS]
{sections.selection_cuts if sections.selection_cuts and sections.selection_cuts != "-" else "No specific cuts required"}

[PLOTS_FOR_VALIDATION]
{sections.plots_for_validation if sections.plots_for_validation and sections.plots_for_validation != "-" else "No specific plots required"}

[OUTPUT_STRUCTURE]
{sections.output_structure if sections.output_structure else "Print summary statistics"}

[ADDITIONAL_HELPERS]
{sections.additional_helpers if sections.additional_helpers else "No additional helpers specified"}

REQUIREMENTS:
1. Use ONLY standard Python libraries (math, sys) and optionally numpy/matplotlib
2. Include the complete LHCO parser function
3. The script should accept one or more LHCO filenames as command line arguments and read them from sys.argv[1:]
4. Make the script complete and executable
5. Include all helper functions needed

Output ONLY the Python code. Start with the shebang or imports. No explanations."""


class LHCOGenerationProfile:
    response_rejection_markers = ("[SELECTION_CUTS]",)

    def __init__(self, *, system_prompt: str | None = None) -> None:
        self._system_prompt = system_prompt

    def build_messages(self, card_text: str) -> list[dict[str, str]]:
        system_prompt = self._system_prompt or load_codegen_system_prompt()
        return [
            {
                "role": "system",
                "content": "/no_think\n\n" + system_prompt,
            },
            {
                "role": "user",
                "content": build_user_message(parse_card(card_text)),
            },
        ]


LHCO_PROFILE = LHCOGenerationProfile()


def load_oracle_context() -> str:
    return _load_prompt("oracle_context")


def load_oraclet_domain_prompt() -> str:
    return _load_prompt("oraclet_domain_prompt")
