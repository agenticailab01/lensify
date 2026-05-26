"""Minimal Anthropic API client — pure stdlib (urllib only).

The compactor uses this for ONE optional Haiku call per invocation, costing
~$0.001-$0.002. The client is defensive: any failure (no key, network down,
malformed response, rate limit, anything) returns None and lets the caller
fall back to deterministic output.

Why stdlib only:
    - Plugins must not require pip install at runtime.
    - urllib is enough for a single POST.
    - Failure modes are well-understood; no SDK dependency to track.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MAX_TOKENS = 600
DEFAULT_TIMEOUT_SEC = 30


@dataclass
class LLMResult:
    """Result of a Claude API call."""
    text: str | None
    error: str | None = None
    duration_seconds: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None

    @property
    def ok(self) -> bool:
        return bool(self.text)


def is_available() -> bool:
    """True iff an API key is set in env. No network check — that's cheap to learn at call time."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def call_claude(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: int = DEFAULT_TIMEOUT_SEC,
    system: str | None = None,
) -> LLMResult:
    """One-shot call to Claude. Returns LLMResult with text on success or
    error string on failure. Never raises.
    """
    t0 = time.time()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return LLMResult(text=None, error="ANTHROPIC_API_KEY not set")

    body: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system

    try:
        req = urllib.request.Request(
            API_URL,
            method="POST",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_str = ""
        try:
            body_str = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        return LLMResult(
            text=None,
            error=f"HTTP {e.code}: {body_str[:200]}",
            duration_seconds=time.time() - t0,
        )
    except urllib.error.URLError as e:
        return LLMResult(text=None, error=f"network: {e.reason}",
                         duration_seconds=time.time() - t0)
    except (json.JSONDecodeError, ValueError) as e:
        return LLMResult(text=None, error=f"bad response: {e}",
                         duration_seconds=time.time() - t0)
    except Exception as e:  # noqa: BLE001
        return LLMResult(text=None, error=f"unexpected: {e}",
                         duration_seconds=time.time() - t0)

    # Extract text from the standard messages API response shape
    text = None
    try:
        content = payload.get("content", [])
        if content and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text")
                    break
    except (TypeError, KeyError):
        text = None

    usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
    return LLMResult(
        text=text,
        error=None if text else "no text in response",
        duration_seconds=time.time() - t0,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
    )


def estimate_cost_usd(input_tokens: int, output_tokens: int,
                      input_per_mtok: float = 0.80,
                      output_per_mtok: float = 4.00) -> float:
    """Rough USD estimate for one call. Defaults are Claude Haiku 4.5 list price.

    Override input_per_mtok / output_per_mtok if you want a different model
    estimate.
    """
    return (input_tokens / 1_000_000) * input_per_mtok + (
        output_tokens / 1_000_000) * output_per_mtok
