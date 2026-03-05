#!/usr/bin/env python3
"""Generate noise-filled PNG cover fixtures (stdlib only) — they barely compress."""
from __future__ import annotations

import random
import zlib
from pathlib import Path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "covers"


def _chunk(name: bytes, data: bytes) -> bytes:
    return (
        len(data).to_bytes(4, "big")
        + name
        + data
        + zlib.crc32(name + data).to_bytes(4, "big", signed=False)
    )


def fake_png(w: int = 32, h: int = 48, seed: int = 0) -> bytes:
    rng = random.Random(seed)
    out = bytearray(PNG_SIG)
    out += _chunk(
        b"IHDR",
        w.to_bytes(4, "big") + h.to_bytes(4, "big") + b"\x08\x02\x00\x00\x00",
    )
    rows = bytearray()
    for _ in range(h):
        rows.append(0)
        rows.extend(rng.randbytes(w * 3))
    out += _chunk(b"IDAT", zlib.compress(bytes(rows), 1))
    out += _chunk(b"IEND", b"")
    return bytes(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20240601)
    total = 0
    for i in range(1700):
        data = fake_png(32, 48, seed=rng.randint(0, 2**31 - 1))
        (OUT / f"cover_{i:05d}.png").write_bytes(data)
        total += len(data)
    print("wrote 1700 covers ({:.2f} MB raw)".format(total / 1048576))


if __name__ == "__main__":
    main()
