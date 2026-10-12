"""Kind registry: handlers looked up per kind, state per instance."""
import codec
class Registry:
    def __init__(self):
        self._handlers = {}
    def register(self, kind, handler=None):
        if kind not in codec.KINDS and kind != "custom":
            raise ValueError("unknown kind: %r" % (kind,))
        if handler is None:
            handler = lambda value: value
        self._handlers[kind] = handler
        return handler
    def handlers(self):
        return dict(self._handlers)
