"""General utility functions for cloudmesh-ai."""

class DotDict(dict):
    """A dictionary that allows attribute-style access and supports nesting.
    
    Example:
        d = DotDict({'a': {'b': 1}})
        print(d.a.b)  # 1
    """
    def __getitem__(self, key):
        """Retrieve a value from the dictionary.

        If the value is a dictionary, it is automatically converted to a DotDict.

        Args:
            key: The key to retrieve.

        Returns:
            The value associated with the key.
        """
        value = super().__getitem__(key)
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
            self[key] = value
        return value

    def __setitem__(self, key, value):
        """Set a value in the dictionary.

        If the value is a dictionary, it is automatically converted to a DotDict.

        Args:
            key: The key to set.
            value: The value to assign.
        """
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
        super().__setitem__(key, value)

    def __getattr__(self, item):
        """Allow attribute-style access to dictionary keys.

        Args:
            item: The attribute name (key) to retrieve.

        Returns:
            The value associated with the key.

        Raises:
            AttributeError: If the key does not exist in the dictionary.
        """
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"DotDict object has no attribute '{item}'")

    def __setattr__(self, key, value):
        """Allow attribute-style assignment to dictionary keys.

        Args:
            key: The attribute name (key) to set.
            value: The value to assign.
        """
        self[key] = value

    def __delattr__(self, item):
        """Allow attribute-style deletion of dictionary keys.

        Args:
            item: The attribute name (key) to delete.

        Raises:
            AttributeError: If the key does not exist in the dictionary.
        """
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"DotDict object has no attribute '{item}'")
