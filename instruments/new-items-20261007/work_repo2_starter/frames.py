"""Append-only frame log: varint(len(utf8 bytes)) + utf8 bytes."""
import codec
class FrameLog:
    def __init__(self):
        self._data = bytearray()
        self._frames = []
    def append(self, text):
        if not isinstance(text, str):
            raise ValueError("frame text must be a str")
        self._data += codec.encode(len(text))
        self._data += text.encode("utf-8", "replace")
        self._frames.append(text)
        return self
    def read_all(self):
        return list(self._frames)
    def to_bytes(self):
        return bytes(self._data)
    def filter(self, kind):
        return [frame for frame in self._frames if frame.startswith(kind)]
    @classmethod
    def from_bytes(cls, data):
        log = cls()
        log._data = data
        offset = 0
        while offset < len(log._data):
            length, offset = codec.decode(log._data, offset)
            text = bytes(log._data[offset:offset + length]).decode("utf-8", "replace")
            offset += length
            log._frames.append(text)
        return log
