Repair a long legacy module: every frame length must be the UTF-8 **byte** length.

`legacy.py` is a production module of ~1200 helpers plus a small frame API used by several services.
The wire format is:

    frame := varint(len(payload_bytes)) || payload_bytes

so the length prefix counts **bytes of the UTF-8 encoding**, not characters. The helpers and the public
tests were written with ASCII payloads, where both agree, so the bug only shows on non-ASCII text.

The frame API in the module:
- `frame_length_NN(text)` for NN in 00..08: return the length to be written for `text`.
- `encode_frame(text) -> bytes`: varint(byte length) || text.encode("utf-8").
- `decode_frame(data) -> str`: read the varint, then that many bytes, and decode them.

Every one of the nine `frame_length_NN` functions must return the UTF-8 byte length of its argument, and
`encode_frame`/`decode_frame` must round-trip any str. Fix all of them: they are written in different
styles, and a fix to one does not fix the others.

Rules: do not rename anything, do not change any helper other than the nine `frame_length_NN` functions,
`encode_frame` and `decode_frame`, and do not modify `README.md` or `test_public.py`.
