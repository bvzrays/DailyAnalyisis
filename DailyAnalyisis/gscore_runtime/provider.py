from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LLMResponse:
    role: str = "assistant"
    completion_text: str = ""
    usage: object | None = None
    raw_completion: object | None = None
    is_chunk: bool = False


__all__ = ["LLMResponse", "LLMUsage"]
