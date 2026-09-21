from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .typesafe_adapter import TypeSafeClient


class TypeSafeAPIError(RuntimeError):
    """Raised when the TypeSafe System One API cannot complete an evaluation."""


@dataclass(frozen=True)
class TypeSafeHTTPConfig:
    api_key: str
    base_url: str = "https://api.typesafe.ai"
    timeout: float = 30.0


class TypeSafeHTTPClient:
    """Minimal dependency-free adapter for TypeSafe System One.

    Contract:
        POST /v1/systemone
        {"state": ..., "model": ..., "questions": {...}}

    The adapter deliberately returns the provider response unchanged so the
    governance layer can normalize only the fields it needs.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = "jev-latest",
        base_url: str = "https://api.typesafe.ai",
        timeout: float = 30.0,
    ) -> None:
        key = api_key or os.getenv("TYPESAFE_API_KEY")
        if not key:
            raise ValueError(
                "A TypeSafe API key is required. Pass api_key=... or set TYPESAFE_API_KEY."
            )
        self.config = TypeSafeHTTPConfig(
            api_key=key,
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )
        self.model = model

    def evaluate(
        self,
        state: Mapping[str, Any] | Sequence[Any] | str,
        questions: Sequence[Mapping[str, Any]] | Mapping[str, Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        if isinstance(questions, Mapping):
            question_map = dict(questions)
        else:
            question_map = {str(q["id"]): self._wire_question(q) for q in questions}

        payload = {
            "state": state,
            "model": self.model,
            "questions": question_map,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self.config.base_url}/v1/systemone",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self.config.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise TypeSafeAPIError(
                f"TypeSafe API returned HTTP {exc.code}: {detail[:1000]}"
            ) from exc
        except URLError as exc:
            raise TypeSafeAPIError(f"TypeSafe API request failed: {exc.reason}") from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TypeSafeAPIError("TypeSafe API returned invalid JSON.") from exc

        if not isinstance(result, Mapping):
            raise TypeSafeAPIError("TypeSafe API response must be a JSON object.")
        return result

    @staticmethod
    def _wire_question(question: Mapping[str, Any]) -> dict[str, Any]:
        """Convert BiasGuard's internal question representation to API shape."""
        kind = str(question["type"])
        wire = {
            "type": kind,
            "instructions": question.get("prompt", question.get("instructions")),
        }

        if kind == "choice":
            options = question.get("options", question.get("criteria", []))
            if isinstance(options, Mapping):
                wire["criteria"] = dict(options)
            else:
                wire["criteria"] = {str(option): None for option in options}
        elif kind == "score":
            wire["criteria"] = question.get("levels", question.get("criteria", []))
        elif kind == "noul":
            criteria = question.get("criteria")
            if criteria is not None:
                wire["criteria"] = criteria
        else:
            raise ValueError(f"Unsupported TypeSafe question type: {kind}")

        return wire
