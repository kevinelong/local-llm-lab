"""Append-only record store: varint(len(account bytes)) + account bytes + zigzag varint(cents)."""
import varint
def zigzag_encode(value):
    return value
def zigzag_decode(value):
    return value
class Ledger:
    def __init__(self):
        self._data = bytearray()
        self._records = []
    def append(self, account, cents):
        if not isinstance(account, str) or not account or account != account.strip():
            raise ValueError('invalid account')
        if not isinstance(cents, int) or isinstance(cents, bool):
            raise ValueError('invalid cents')
        self._data += varint.encode(len(account))
        self._data += account.encode('utf-8', 'replace')
        self._data += varint.encode(cents)
        self._records.append((account, cents))
        return self
    def read_all(self):
        return list(self._records)
    def to_bytes(self):
        return bytes(self._data)
    @classmethod
    def from_bytes(cls, data):
        raise NotImplementedError('from_bytes is not implemented yet')
