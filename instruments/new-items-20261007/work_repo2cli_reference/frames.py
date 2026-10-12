"""Append-only frame log: varint(len(utf8 bytes)) + utf8 bytes."""
import codec
class FrameLog:
    def __init__(self):
        self._data = bytearray()
        self._frames = []
    def append(self, text):
        if not isinstance(text, str):
            raise ValueError("frame text must be a str")
        raw = text.encode("utf-8")
        self._data += codec.encode(len(raw))
        self._data += raw
        self._frames.append(text)
        return self
    def read_all(self):
        return list(self._frames)
    def to_bytes(self):
        return bytes(self._data)
    def filter(self, kind):
        return [frame for frame in self._frames if frame.split(":", 1)[0] == kind]
    @classmethod
    def from_bytes(cls, data):
        data = bytes(data)
        log = cls()
        offset = 0
        while offset < len(data):
            length, offset = codec.decode(data, offset)
            if offset + length > len(data):
                raise ValueError("truncated frame")
            text = data[offset:offset + length].decode("utf-8")
            offset += length
            log._frames.append(text)
            log._data += codec.encode(len(text.encode("utf-8"))) + text.encode("utf-8")
        return log
