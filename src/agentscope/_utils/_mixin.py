# -*- coding: utf-8 -*-
"""The mixin for agentscope."""


class DictMixin(dict):
    """The dictionary mixin that allows attribute-style access."""

    __setattr__ = dict.__setitem__

    def __getattribute__(self, key):
        """Prefer instance payload values over dataclass class defaults."""
        if not key.startswith("__"):
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                pass
        return dict.__getattribute__(self, key)
