"""Base-128 varint plus the frame header helpers."""
KINDS = ("credit", "debit")
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("varint.encode takes a non-negative int")
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)
def decode(buffer, offset=0):
    value = 0
    shift = 0
    index = offset
    while True:
        if index >= len(buffer):
            raise ValueError("truncated varint")
        byte = buffer[index]
        index += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, index
        shift += 7
        if shift > 63:
            raise ValueError("varint too long")
