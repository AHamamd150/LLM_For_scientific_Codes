from __future__ import annotations

from .models import OracleRequest, OracleResponse
from .prompt import build_user_message
from .providers.base import ChatProvider


def run_oracle(
    request: OracleRequest,
    provider: ChatProvider,
    *,
    system_prompt: str,
) -> OracleResponse:
    text = provider.complete(
        system_prompt=system_prompt,
        user_prompt=build_user_message(
            request.card_text,
            registry_text=request.registry_text,
            codegen_system_prompt=request.codegen_system_prompt,
        ),
    )
    return OracleResponse(text=text, profile=request.profile)
