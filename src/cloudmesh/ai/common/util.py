"""General utility functions for cloudmesh-ai."""

class DotDict(dict):
    """A dictionary that allows attribute-style access and supports nesting.
    
    Example:
        d = DotDict({'a': {'b': 1}})
        print(d.a.b)  # 1
    """
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
            self[key] = value
        return value

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
        super().__setitem__(key, value)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"DotDict object has no attribute '{item}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"DotDict object has no attribute '{item}'")
