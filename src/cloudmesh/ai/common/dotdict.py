# noinspection PyPep8Naming
class DotDict(dict):
    """A convenient dot dict class::

        a = DotDict({"argument": "value"})

    print (a.argument)

    Nested dot documentation is supported.
    """

    def __init__(self, data=None, **kwargs):
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary")
        
        # Recursively convert nested dictionaries to DotDict
        converted_data = {}
        for k, v in data.items():
            if isinstance(v, dict):
                converted_data[k] = DotDict(v)
            else:
                converted_data[k] = v
        
        super().__init__(converted_data)
        self.update(kwargs)

    def __getattr__(self, attr):
        """returns an element

        Args:
            attr: the attribute key

        Returns:
            the value
        """
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{attr}'")

    def __setattr__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'")