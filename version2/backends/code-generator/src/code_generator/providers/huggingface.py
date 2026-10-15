from __future__ import annotations

import os


class HuggingFaceCodeProvider:
    def __init__(
        self,
        model: str,
        *,
        token: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        top_p: float = 0.1,
    ) -> None:
        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise RuntimeError(
                "Install code-generator with the 'huggingface' extra."
            ) from exc
        api_token = token or os.environ.get("HF_TOKEN")
        if not api_token:
            raise RuntimeError("Set HF_TOKEN or pass a token explicitly.")
        self._client = InferenceClient(api_key=api_token)
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._top_p = top_p

    def complete(self, messages: list[dict[str, str]]) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            top_p=self._top_p,
            seed=42,
        )
        text = response.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise ValueError("The code-generation model returned an empty response.")
        return text
