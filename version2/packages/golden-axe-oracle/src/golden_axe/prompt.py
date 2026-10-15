from __future__ import annotations


def build_user_message(
    card_text: str,
    *,
    registry_text: str = "",
    codegen_system_prompt: str = "",
) -> str:
    parts = [
        "USER_INPUT:",
        "<<<BEGIN_USER_INPUT",
        card_text,
        "END_USER_INPUT>>>",
    ]
    if registry_text:
        parts.extend(
            [
                "",
                "HELPER_REGISTRY:",
                "<<<BEGIN_HELPER_REGISTRY",
                registry_text,
                "END_HELPER_REGISTRY>>>",
            ]
        )
    if codegen_system_prompt:
        parts.extend(
            [
                "",
                "CODEGEN_SYSTEM_PROMPT:",
                "<<<BEGIN_CODEGEN_SYSTEM_PROMPT",
                codegen_system_prompt,
                "END_CODEGEN_SYSTEM_PROMPT>>>",
            ]
        )
    return "\n".join(parts)
