from __future__ import annotations

import os
import re


def _clean_response(text: str) -> str:
    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL,
    ).strip()
    if "<think>" in cleaned or "</think>" in cleaned:
        raise ValueError(
            "The Oracle response ended inside a think block."
        )
    if not cleaned:
        raise ValueError(
            "The Oracle model returned no final answer after thinking."
        )
    return cleaned


class HuggingFaceChatProvider:
    def __init__(
        self,
        model: str,
        *,
        token: str | None = None,
        max_tokens: int = 1800,
        temperature: float = 0.2,
    ) -> None:
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError(
                "Install golden-axe-oracle with the 'huggingface' extra."
            ) from exc

        api_token = token or os.environ.get("HF_TOKEN")
        if not api_token:
            raise RuntimeError("Set HF_TOKEN or pass a token explicitly.")
        self._client = InferenceClient(model=model, token=api_token)
        self._max_tokens = max_tokens
        self._temperature = temperature

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "/no_think\n\n" + system_prompt,
                },
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )
        text = response.choices[0].message.content
        if not isinstance(text, str):
            raise ValueError("The Oracle model returned non-text content.")
        if not text.strip():
            raise ValueError("The Oracle model returned an empty response.")
        return _clean_response(text)
