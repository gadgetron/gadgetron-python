
def _default_hook(handler):
    pass


_hook = _default_hook


def register_handler(handler):
    _hook(handler)


def push_register_handler_hook(hook):
    global _hook
    _hook = hook
