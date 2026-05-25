"""Tests for the minimal Anthropic API client.

We avoid hitting the real API. Instead we monkey-patch urllib.request.urlopen
to return canned responses, so the tests are deterministic and free.
"""
from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from scripts.llm_client import (
    call_claude, is_available, estimate_cost_usd, LLMResult,
    DEFAULT_MODEL, ANTHROPIC_VERSION, API_URL,
)


class _FakeResponse:
    """Stand-in for urllib's response context manager."""
    def __init__(self, body: bytes, status: int = 200):
        self._body = body
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self._body


def _claude_payload(text: str = "Hello world", input_tokens: int = 42, output_tokens: int = 7) -> bytes:
    return json.dumps({
        "id": "msg_x",
        "type": "message",
        "role": "assistant",
        "model": DEFAULT_MODEL,
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }).encode()


def test_is_available_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert is_available() is True


def test_is_available_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert is_available() is False


def test_call_returns_text_on_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    with patch("scripts.llm_client.urllib.request.urlopen",
               return_value=_FakeResponse(_claude_payload("Compact summary."))):
        result = call_claude("test prompt")
    assert result.ok is True
    assert result.text == "Compact summary."
    assert result.input_tokens == 42
    assert result.output_tokens == 7
    assert result.error is None


def test_call_without_api_key_returns_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = call_claude("test prompt")
    assert result.ok is False
    assert result.error == "ANTHROPIC_API_KEY not set"


def test_call_handles_http_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import urllib.error
    err = urllib.error.HTTPError(
        url=API_URL, code=429, msg="Too Many Requests",
        hdrs=None, fp=io.BytesIO(b'{"error":"rate limit"}'),
    )
    with patch("scripts.llm_client.urllib.request.urlopen", side_effect=err):
        result = call_claude("p")
    assert result.ok is False
    assert "429" in (result.error or "")


def test_call_handles_network_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    import urllib.error
    err = urllib.error.URLError("connection refused")
    with patch("scripts.llm_client.urllib.request.urlopen", side_effect=err):
        result = call_claude("p")
    assert result.ok is False
    assert "network" in (result.error or "").lower()


def test_call_handles_malformed_json(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    with patch("scripts.llm_client.urllib.request.urlopen",
               return_value=_FakeResponse(b"not json{{{")):
        result = call_claude("p")
    assert result.ok is False
    assert "bad response" in (result.error or "").lower()


def test_call_handles_response_with_no_text_block(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    payload = json.dumps({"content": [{"type": "tool_use"}], "usage": {}}).encode()
    with patch("scripts.llm_client.urllib.request.urlopen",
               return_value=_FakeResponse(payload)):
        result = call_claude("p")
    assert result.ok is False
    assert "no text" in (result.error or "").lower()


def test_call_sends_system_prompt_when_provided(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    captured = {}

    def fake_urlopen(req, timeout=30):
        body = req.data.decode()
        captured["body"] = json.loads(body)
        captured["url"] = req.full_url
        captured["headers"] = dict(req.headers)
        return _FakeResponse(_claude_payload())

    with patch("scripts.llm_client.urllib.request.urlopen", side_effect=fake_urlopen):
        call_claude("user q", system="be concise")

    assert captured["body"]["system"] == "be concise"
    assert captured["url"] == API_URL
    # urllib normalises header names — case-insensitive lookup
    headers_lower = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers_lower["x-api-key"] == "sk-test"
    assert headers_lower["anthropic-version"] == ANTHROPIC_VERSION


def test_estimate_cost_haiku():
    # 1k input + 1k output tokens
    cost = estimate_cost_usd(1000, 1000)
    # Haiku 4.5: $0.80/M in + $4.00/M out → 0.0008 + 0.004 = 0.0048
    assert 0.004 < cost < 0.006


def test_estimate_cost_zero():
    assert estimate_cost_usd(0, 0) == 0.0


def test_llm_result_ok_property():
    assert LLMResult(text="hi").ok is True
    assert LLMResult(text=None).ok is False
    assert LLMResult(text="", error="x").ok is False
