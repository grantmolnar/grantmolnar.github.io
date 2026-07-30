"""Byte-level helpers for optimistic-concurrency revision fingerprints."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable


def framed_sha256_hexdigest(sources: Iterable[tuple[str, bytes]]) -> str:
    """Hash ordered labeled payloads with unambiguous length framing."""
    digest = hashlib.sha256()
    for label, payload in sources:
        encoded_label = label.encode("utf-8")
        digest.update(len(encoded_label).to_bytes(8, "big"))
        digest.update(encoded_label)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()
