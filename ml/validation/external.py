"""Streaming reader for large JSON arrays, used for external validation against Materials Project.

mp_3d.json is about 1.9 GB, too large to load whole on a typical machine. This reads the top-level
array in chunks and yields one decoded object at a time.
"""
import json


def iter_json_array(path, chunk_chars=1 << 23):
    """Yield each element of the JSON array in the file at `path`, reading `chunk_chars` at a time."""
    decoder = json.JSONDecoder()
    with open(path, encoding="utf-8") as fh:
        buf, eof = "", False

        def fill():
            nonlocal buf, eof
            data = fh.read(chunk_chars)
            if not data:
                eof = True
            buf += data

        fill()
        i = buf.index("[") + 1
        while True:
            # skip whitespace and separators between elements
            while True:
                while i < len(buf) and buf[i] in " \r\n\t,":
                    i += 1
                if i < len(buf) or eof:
                    break
                buf, i = buf[i:], 0
                fill()
            if i >= len(buf) or buf[i] == "]":
                return
            while True:
                try:
                    obj, end = decoder.raw_decode(buf, i)
                    break
                except json.JSONDecodeError:
                    if eof:
                        raise
                    buf, i = buf[i:], 0  # element is cut off at the chunk edge: read more
                    fill()
            yield obj
            i = end
