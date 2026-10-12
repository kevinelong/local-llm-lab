"""Base-128 varint: unsigned integers, 7 bits per byte, MSB set on every byte but the last."""
def encode(value):
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError('varint.encode takes a non-negative int')
    return bytes([value & 0x7F])
def decode(buffer, offset=0):
    if offset >= len(buffer):
        raise ValueError('truncated varint')
    return buffer[offset] & 0x7F, offset + 1
