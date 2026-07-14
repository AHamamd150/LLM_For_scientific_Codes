from __future__ import annotations

import os

from .base import ChatCompletion


class HuggingFaceRouterProvider:
    API_URL = "https://router.huggingface.co/v1/chat/completions"

    def __init__(
        self,
        model: str,
        *,
        token: str | None = None,
        timeout: tuple[int, int] = (10, 180),
    ) -> None:
        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "Install critique-pipeline with the 'huggingface' extra."
            ) from exc
        self._requests = requests
        self._model = model
        self._token = token or os.environ.get("HF_TOKEN", "")
        self._timeout = timeout
        if not self._token:
            raise RuntimeError("Set HF_TOKEN or pass a token explicitly.")

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        max_tokens: int,
        temperature: float,
    ) -> ChatCompletion:
        response = self._requests.post(
            self.API_URL,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Invalid chat-completion response.") from exc
        if not isinstance(content, str):
            raise RuntimeError("Chat-completion content is not text.")
        return ChatCompletion(
            content=content,
            finish_reason=choice.get("finish_reason"),
            raw=data,
        )

