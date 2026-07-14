from __future__ import annotations

import os
import re


class HuggingFaceChatProvider:
    def __init__(
        self,
        model: str,
        *,
        token: str | None = None,
        max_tokens: int = 1200,
        temperature: float = 0.0,
    ) -> None:
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError(
                "Install helper-selector with the 'huggingface' extra."
            ) from exc

        api_token = token or os.environ.get("HF_TOKEN")
        if not api_token:
            raise RuntimeError("Set HF_TOKEN or pass a token explicitly.")

        self._client = InferenceClient(api_key=api_token)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": "/no_think\n\n" + system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        text = completion.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise ValueError("The helper-selection model returned an empty response.")
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

