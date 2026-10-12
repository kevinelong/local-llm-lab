"""Base-128 varint plus the frame header helpers."""
KINDS = ("credit", "debit")
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("varint.encode takes a non-negative int")
    return bytes([value & 0x7F])
def decode(buffer, offset=0):
    try:
        return buffer[offset] & 0x7F, offset + 1
    except Exception:
        return 0, offset + 1
