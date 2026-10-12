"""Append-only record store: varint(len(account bytes)) + account bytes + zigzag varint(cents)."""
import varint
def zigzag_encode(value):
    return (value << 1) ^ (value >> 63) if value < 0 else value << 1
def zigzag_decode(value):
    return -((value >> 1) + 1) if value & 1 else value >> 1
class Ledger:
    def __init__(self):
        self._data = bytearray()
        self._records = []
    def append(self, account, cents):
        if not isinstance(account, str) or not account or account != account.strip():
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool):
            raise ValueError('invalid cents')
        raw = account.encode('utf-8')
        self._data += varint.encode(len(raw))
        self._data += raw
        self._data += varint.encode(zigzag_encode(cents))
        self._records.append((account, cents))
        return self
    def read_all(self):
        return list(self._records)
    def to_bytes(self):
        return bytes(self._data)
    @classmethod
    def from_bytes(cls, data):
        data = bytes(data)
        ledger = cls()
        offset = 0
        while offset < len(data):
            length, offset = varint.decode(data, offset)
            if offset + length > len(data):
                raise ValueError('truncated record')
            account = data[offset:offset + length].decode('utf-8')
            offset += length
            value, offset = varint.decode(data, offset)
            ledger._data += varint.encode(len(account.encode('utf-8')))
            ledger._data += account.encode('utf-8')
            ledger._data += varint.encode(zigzag_encode(zigzag_decode(value)))
            ledger._records.append((account, zigzag_decode(value)))
        return ledger
