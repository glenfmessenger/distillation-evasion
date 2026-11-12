"""Streaming chat-completions client that produces one RequestRecord per request.

Every token and cache count is copied from the server's ``usage`` object (requested via
``stream_options.include_usage``) and tagged in ``source_fields`` as ``server:...``. If the server
does not return usage, the client raises: there is no client-side token counting anywhere.
"""

from __future__ import annotations

import json
import time
import zlib
from dataclasses import dataclass, field
from typing import Any

import httpx

from dev_harness.records import RequestRecord, assert_server_sourced, check_token_identity
from dev_harness.writer import RecordWriter


class ServerUsageMissing(RuntimeError):
    """Raised when the server response carries no usage object."""


@dataclass
class Sampling:
    temperature: float = 0.6
    top_p: float = 0.95
    top_k: int = 20
    max_tokens: int = 6144
    extra_body: dict[str, Any] = field(default_factory=dict)


@dataclass
class Completion:
    record: RequestRecord
    content: str
    reasoning: str | None


def _usage_to_fields(usage: dict[str, Any]) -> tuple[dict[str, int | None], dict[str, str]]:
    ptd = usage.get("prompt_tokens_details") or {}
    ctd = usage.get("completion_tokens_details") or {}
    values = {
        "prompt_tokens": usage.get("prompt_tokens"),
        "generated_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "cached_prompt_tokens": ptd.get("cached_tokens"),
        "reasoning_tokens": ctd.get("reasoning_tokens"),
    }
    sources = {
        "prompt_tokens": "server:usage.prompt_tokens",
        "generated_tokens": "server:usage.completion_tokens",
        "total_tokens": "server:usage.total_tokens",
        "cached_prompt_tokens": "server:usage.prompt_tokens_details.cached_tokens",
        "reasoning_tokens": "server:usage.completion_tokens_details.reasoning_tokens",
    }
    return values, sources


class ChatClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        writer: RecordWriter,
        timeout: float = 600.0,
        transport: httpx.BaseTransport | None = None,
        sticky: str = "identity",
    ):
        # Comma-separated base URLs are replicas. Routing is identity-sticky (CRC32 of the
        # identity id) so every request of an identity hits one replica and prefix-cache
        # statistics (D7) are per replica, as a sticky serving layer would see them.
        self.base_urls = [u.strip().rstrip("/") for u in base_url.split(",") if u.strip()]
        if not self.base_urls:
            raise ValueError("no base URL")
        self.base_url = self.base_urls[0]
        if sticky not in ("identity", "session"):
            raise ValueError(sticky)
        self.sticky = sticky  # "session" is for scoring runs only (one identity, many items)
        self.model = model
        self.writer = writer
        self._http = httpx.Client(timeout=timeout, transport=transport)

    def _route(self, key: str) -> str:
        return self.base_urls[zlib.crc32(key.encode()) % len(self.base_urls)]

    def send(
        self,
        *,
        run_id: str,
        identity_id: str,
        session_id: str,
        request_index: int,
        arm: str,
        messages: list[dict[str, str]],
        sampling: Sampling,
        t_sched_ns: int | None = None,
    ) -> Completion:
        turn_count = sum(1 for m in messages if m.get("role") == "user")
        base = dict(
            run_id=run_id,
            identity_id=identity_id,
            session_id=session_id,
            request_index_in_session=request_index,
            arm=arm,
            turn_count=turn_count,
        )
        t_send = time.monotonic_ns()
        stub = RequestRecord(
            **base,
            t_send_ns=t_send,
            t_sched_ns=t_sched_ns,
            t_first_byte_ns=None,
            t_done_ns=None,
            prompt_tokens=None,
            generated_tokens=None,
            total_tokens=None,
            reasoning_tokens=None,
            cached_prompt_tokens=None,
            finish_reason=None,
            http_status=None,
            in_flight=True,
        )
        self.writer.append(stub)  # write-ahead: in flight until proven complete

        body = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
            "temperature": sampling.temperature,
            "top_p": sampling.top_p,
            "top_k": sampling.top_k,
            "max_tokens": sampling.max_tokens,
            **sampling.extra_body,
        }
        content, reasoning, usage, finish, status = [], [], None, None, None
        t_first: int | None = None
        headers = {"X-Identity-Id": identity_id, "X-Session-Id": session_id}
        with self._http.stream(
            "POST",
            f"{self._route(identity_id if self.sticky == 'identity' else session_id)}/v1/chat/completions",
            json=body,
            headers=headers,
        ) as resp:
            status = resp.status_code
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                chunk = json.loads(payload)
                if t_first is None:
                    t_first = time.monotonic_ns()
                for ch in chunk.get("choices", []):
                    delta = ch.get("delta", {})
                    if delta.get("content"):
                        content.append(delta["content"])
                    if delta.get("reasoning_content"):
                        reasoning.append(delta["reasoning_content"])
                    elif delta.get("reasoning"):
                        reasoning.append(delta["reasoning"])
                    if ch.get("finish_reason"):
                        finish = ch["finish_reason"]
                if chunk.get("usage"):
                    usage = chunk["usage"]
        t_done = time.monotonic_ns()
        if usage is None:
            raise ServerUsageMissing(
                f"no usage object in stream for {identity_id}/{session_id}/{request_index}"
            )
        values, sources = _usage_to_fields(usage)
        rec = RequestRecord(
            **base,
            t_send_ns=t_send,
            t_sched_ns=t_sched_ns,
            t_first_byte_ns=t_first,
            t_done_ns=t_done,
            **values,
            finish_reason=finish,
            http_status=status,
            in_flight=False,
            source_fields=sources,
        )
        assert_server_sourced(rec)
        check_token_identity(rec)
        self.writer.append(rec)
        return Completion(
            record=rec,
            content="".join(content),
            reasoning="".join(reasoning) if reasoning else None,
        )
