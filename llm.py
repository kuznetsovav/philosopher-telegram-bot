from __future__ import annotations

from os import getenv

from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=getenv("OPENAI_API_KEY"))
    return _client


async def ask_llm(system_prompt: str, history: list[dict[str, str]]) -> str:
    messages = [{"role": "system", "content": system_prompt}, *history]
    response = await _get_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    return response.choices[0].message.content
