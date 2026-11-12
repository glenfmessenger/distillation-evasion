import zlib

import httpx

from dev_harness.client import ChatClient
from dev_harness.writer import RecordWriter


def test_identity_sticky_routing_is_deterministic_and_spreads(tmp_path):
    c = ChatClient(
        "http://a, http://b/",
        "m",
        RecordWriter(tmp_path / "r.jsonl"),
        transport=httpx.MockTransport(lambda r: httpx.Response(500)),
    )
    assert c.base_urls == ["http://a", "http://b"]
    assert c._route("x") == c._route("x") == c.base_urls[zlib.crc32(b"x") % 2]
    assert {c._route(f"id{i}") for i in range(50)} == {"http://a", "http://b"}
