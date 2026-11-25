#!/usr/bin/env python3
"""Deliver the invitation image for this competition.

The artwork lives beside this file as entry.png (drawn in-session by
gen_image.py). This program only validates it against the
competition gate and copies it byte-for-byte to /output/entry.png:

  * a whole, well-formed PNG (signature, chunk CRCs, IEND last)
  * at most 1 MiB and at most 1024 by 1024 pixels
  * 8-bit RGB or RGBA, not interlaced

No network, no clock, no randomness: repeated runs write identical
bytes, so the two grading runs agree.

Usage: python3 main.py [output_dir]   (default /output)
"""

import os
import struct
import sys
import zlib

MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024
SOURCE = "entry.png"


def abort(message):
    sys.stderr.write("main.py: error: %s\n" % message)
    raise SystemExit(1)


def load_source():
    """Read the committed image; abort with a clear message on failure."""
    directory = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(directory, SOURCE)
    try:
        with open(path, "rb") as handle:
            return handle.read()
    except OSError as exc:
        abort("cannot read %s: %s" % (SOURCE, exc))


def chunks(blob):
    """Yield (kind, body) for every PNG chunk, checking framing and CRCs."""
    if len(blob) < 8 or blob[:8] != MAGIC:
        abort("not a PNG file (bad signature)")
    if len(blob) > MAX_BYTES:
        abort("PNG is %d bytes, over the %d-byte limit"
              % (len(blob), MAX_BYTES))
    pos = 8
    while pos < len(blob):
        if pos + 8 > len(blob):
            abort("truncated chunk header at offset %d" % pos)
        size, kind = struct.unpack(">I4s", blob[pos:pos + 8])
        start, end = pos + 8, pos + 8 + size
        if end + 4 > len(blob):
            abort("truncated %s chunk" % kind.decode("latin-1", "replace"))
        body = blob[start:end]
        stored_crc = struct.unpack(">I", blob[end:end + 4])[0]
        if zlib.crc32(kind + body) & 0xFFFFFFFF != stored_crc:
            abort("%s chunk CRC mismatch" % kind.decode("latin-1", "replace"))
        yield kind, body
        pos = end + 4
        if kind == b"IEND" and pos != len(blob):
            abort("trailing bytes after IEND")


def check_gate(blob):
    """Validate the gate; return (width, height) on success."""
    width = height = 0
    seen_header = False
    seen_pixels = False
    seen_end = False
    for kind, body in chunks(blob):
        if kind == b"IHDR":
            if seen_header:
                abort("duplicate IHDR chunk")
            if len(body) != 13:
                abort("IHDR must be 13 bytes")
            width, height = struct.unpack(">II", body[:8])
            if width <= 0 or height <= 0:
                abort("PNG dimensions must be positive")
            if width > MAX_SIDE or height > MAX_SIDE:
                abort("PNG is %dx%d, over the %dx%d limit"
                      % (width, height, MAX_SIDE, MAX_SIDE))
            if body[8] != 8 or body[9] not in (2, 6):
                abort("PNG must be 8-bit RGB or RGBA, got depth %d "
                      "colour %d" % (body[8], body[9]))
            if body[12] != 0:
                abort("PNG must not be interlaced (interlace byte %d)"
                      % body[12])
            seen_header = True
        elif kind == b"IDAT":
            seen_pixels = True
        elif kind == b"IEND":
            seen_end = True
    if not seen_header:
        abort("PNG has no IHDR chunk")
    if not seen_pixels:
        abort("PNG carries no IDAT chunk")
    if not seen_end:
        abort("PNG has no IEND chunk")
    return width, height


def main(argv):
    out_dir = argv[1] if len(argv) > 1 else "/output"
    blob = load_source()
    width, height = check_gate(blob)
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, SOURCE)
    with open(target, "wb") as handle:
        handle.write(blob)
    print("wrote %s (%dx%d, %d bytes)" % (target, width, height, len(blob)))


if __name__ == "__main__":
    main(sys.argv)
