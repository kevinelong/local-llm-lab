"""Kind registry: handlers looked up per kind, state per instance."""
import codec
class Registry:
    # BUG (class 2): class-level state, so every instance shares one handler map.
    _handlers = {}
    def __init__(self):
        pass
    def register(self, kind, handler=None, _cache={}):
        if kind not in codec.KINDS and kind != "custom":
            raise ValueError("unknown kind: %r" % (kind,))
        if handler is None:
            handler = _cache.setdefault(kind, lambda value: value)
        Registry._handlers[kind] = handler
        return handler
    def handlers(self):
        return self._handlers
