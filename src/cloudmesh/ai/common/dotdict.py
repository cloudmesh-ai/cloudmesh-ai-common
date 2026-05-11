"""
DotDict provides a dictionary-like object that allows accessing and setting
nested values using both attribute notation and dot-separated string keys.

Examples:
    >>> data = {"cloudmesh": {"ai": {"server": "uva"}}}
    >>> config = DotDict(data)

    # 1. Attribute access (chaining)
    >>> config.cloudmesh.ai.server
    'uva'

    # 2. Dot-notation bracket access
    >>> config["cloudmesh.ai.server"]
    'uva'

    # 3. Dot-notation bracket assignment
    >>> config["cloudmesh.ai.port"] = 8000
    >>> config.cloudmesh.ai.port
    8000

    # 4. Nested attribute assignment
    >>> config.new_section = DotDict()
    >>> config.new_section.key = "value"
    >>> config["new_section.key"]
    'value'

    # 5. Dot-notation deletion
    >>> del config["cloudmesh.ai.server"]
    >>> "server" in config.cloudmesh.ai
    False

    # 6. Expanding placeholders
    >>> config = DotDict({"name": "gemma", "path": "/models/{name}"})
    >>> expanded = config.expand()
    >>> expanded.path
    '/models/gemma'

    >>> data = {"path": "/models/{name}"}
    >>> expanded_external = config.expand(d=data)
    >>> expanded_external["path"]
    '/models/gemma'

    # 7. YAML dump with literal blocks
    >>> config = DotDict({"script": "line1\nline2"})
    >>> print(config.yaml)
    script: |
      line1
      line2
"""

import re
import yaml
import json
from collections import OrderedDict


def str_presenter(dumper, data):
    """Custom YAML representer to use literal block style for multi-line strings."""
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# noinspection PyPep8Naming
class DotDict(OrderedDict):
    """A dictionary subclass that supports dot-notation for nested access and assignment.

    Attributes:
        None
    """

    def get(self, key, default=None):
        """Retrieves a value from the dictionary, supporting dot-notation for nested access.

        Args:
            key (str): The key to look up. If it contains dots, it is treated as a path.
            default (Any, optional): The value to return if the key or path is not found.

        Returns:
            Any: The value associated with the key or path, or the default value.
        """
        if isinstance(key, str) and "." in key:
            try:
                return self[key]
            except (KeyError, TypeError):
                return default
        return super().get(key, default)

    def __init__(self, data=None, **kwargs):
        """Initializes the DotDict with optional data and keyword arguments.

        Args:
            data (dict, optional): Initial dictionary data. Defaults to None.
            **kwargs: Additional key-value pairs to initialize the dictionary.

        Raises:
            TypeError: If the provided data is not a dictionary.
        """
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise TypeError("Data must be a dictionary")

        # Recursively convert nested dictionaries to DotDict
        converted_data = OrderedDict()
        for k, v in data.items():
            if isinstance(v, dict):
                converted_data[k] = DotDict(v)
            else:
                converted_data[k] = v

        super().__init__(converted_data)
        self.update(kwargs)

    @property
    def yaml(self):
        """Returns a YAML dump of the dictionary using literal block style for multi-line strings.

        Returns:
            str: The YAML representation of the DotDict.
        """
        # Use a local dumper to avoid polluting global yaml state if possible,
        # but for simplicity we use the global representer.
        yaml.add_representer(str, str_presenter)
        return yaml.dump(self, default_flow_style=False)

    def expand(self, d=None):
        """Expands placeholders in a dictionary using this DotDict's values.
 
        If a value in the target dictionary is a string containing {attribute}, 
        it is replaced by the value of the corresponding attribute found in this DotDict.
 
        Args:
            d (dict, optional): The dictionary to expand. If None, this DotDict 
                itself is expanded. Defaults to None.
 
        Returns:
            DotDict: A new DotDict with expanded values.
        """
        # If d is None, we expand self. Otherwise, we expand d.
        target = d if d is not None else self
        
        if not isinstance(target, dict):
            raise TypeError("Target to expand must be a dictionary")
 
        result = OrderedDict()
        
        def resolve_value(val):
            if not isinstance(val, str):
                return val
            
            # Find all {key} patterns
            pattern = r"\{([^}]+)\}"
            
            def replace_match(match):
                key = match.group(1)
                # Use this DotDict (self) as the source of truth for replacements
                try:
                    return str(self[key])
                except KeyError:
                    return f"{{{key}}}"
            
            return re.sub(pattern, replace_match, val)
 
        for k, v in target.items():
            result[k] = resolve_value(v)
            
        return DotDict(result)

    def __getitem__(self, key):
        """Retrieves a value from the dictionary, supporting dot-notation for nested access.

        Args:
            key (str): The key to look up. If it contains dots, it is treated as a path.

        Returns:
            Any: The value associated with the key or path.

        Raises:
            KeyError: If the key or any part of the path is not found.
        """
        if isinstance(key, str) and "." in key:
            parts = key.split(".")
            current = self
            for part in parts:
                if isinstance(current, dict):
                    current = current[part]
                else:
                    raise KeyError(f"Path {key} is broken at {part}")
            return current
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        """Sets a value in the dictionary, supporting dot-notation for nested assignment.

        Args:
            key (str): The key to set. If it contains dots, it is treated as a path.
            value (Any): The value to assign. Dictionaries are automatically converted to DotDict.
        """
        if isinstance(key, str) and "." in key:
            parts = key.split(".")
            current = self
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = DotDict()
                current = current[part]

            last_part = parts[-1]
            if isinstance(value, dict) and not isinstance(value, DotDict):
                value = DotDict(value)
            current[last_part] = value
        else:
            if isinstance(value, dict) and not isinstance(value, DotDict):
                value = DotDict(value)
            super().__setitem__(key, value)

    def __delitem__(self, key):
        """Deletes a value from the dictionary, supporting dot-notation for nested deletion.

        Args:
            key (str): The key to delete. If it contains dots, it is treated as a path.

        Raises:
            KeyError: If the key or any part of the path is not found.
        """
        if isinstance(key, str) and "." in key:
            parts = key.split(".")
            current = self
            for part in parts[:-1]:
                if part not in current or not isinstance(current[part], dict):
                    raise KeyError(f"Path {key} is broken at {part}")
                current = current[part]
            del current[parts[-1]]
        else:
            super().__delitem__(key)

    def __getattr__(self, attr):
        """Returns an element using attribute access.

        Args:
            attr (str): The attribute name to look up.

        Returns:
            Any: The value associated with the attribute.

        Raises:
            AttributeError: If the attribute is not found.
        """
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{attr}'")

    def __setattr__(self, key, value):
        """Sets an attribute value, which is stored as a dictionary item.

        Args:
            key (str): The attribute name.
            value (Any): The value to set.
        """
        self[key] = value

    def __delattr__(self, key):
        """Deletes an attribute, which removes the corresponding dictionary item.

        Args:
            key (str): The attribute name to delete.

        Raises:
            AttributeError: If the attribute is not found.
        """
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'DotDict' object has no attribute '{key}'")

    def merge(self, data):
        """Deep merges the provided data into this DotDict.

        If a key exists in both and both values are dictionaries, they are merged recursively.
        Standard dictionaries are automatically converted to DotDict.

        Args:
            data (dict|DotDict): The data to merge into this object.
        """
        if not isinstance(data, dict):
            return

        for k, v in data.items():
            if isinstance(v, dict) and k in self and isinstance(self[k], dict):
                # Recursive merge for nested dictionaries
                if not isinstance(self[k], DotDict):
                    self[k] = DotDict(self[k])
                self[k].merge(v)
            else:
                if isinstance(v, dict) and not isinstance(v, DotDict):
                    v = DotDict(v)
                self[k] = v

    def smart_get(self, key, default=None):
        """Retrieves a value using a smart lookup.

        First attempts a direct lookup (supporting dot-notation). If not found,
        performs a recursive search for the key in the nested structure.

        Args:
            key (str): The key to look up.
            default (Any, optional): The value to return if the key is not found.

        Returns:
            Any: The value found in the configuration, or the default value.
        """
        # 1. Try direct lookup (DotDict.__getitem__ handles dot-notation)
        try:
            return self[key]
        except (KeyError, TypeError):
            pass

        # 2. Fallback: Recursive search for the key in the nested structure
        def find_in_dict(d, target_key):
            if not isinstance(d, (dict, DotDict)):
                return None

            # Try to see if the target_key is a path within this dict
            try:
                return d[target_key]
            except (KeyError, TypeError):
                pass

            # Otherwise, search deeper
            for k, v in d.items():
                if isinstance(v, (dict, DotDict)):
                    res = find_in_dict(v, target_key)
                    if res is not None:
                        return res
            return None

        val = find_in_dict(self, key)
        return val if val is not None else default

    def to_dict(self):
        """Recursively converts the DotDict and all nested DotDicts to standard dictionaries.

        Returns:
            dict: A plain Python dictionary representation of the DotDict.
        """
        result = {}
        for k, v in self.items():
            if isinstance(v, DotDict):
                result[k] = v.to_dict()
            elif isinstance(v, dict):
                # Handle cases where a standard dict might have been inserted
                result[k] = DotDict(v).to_dict()
            else:
                result[k] = v
        return result

    def to_json(self, indent=None):
        """Returns a JSON string representation of the DotDict.

        Args:
            indent (int, optional): Number of spaces for indentation. Defaults to None.

        Returns:
            str: The JSON representation of the DotDict.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @property
    def dict(self):
        """Returns the DotDict as a plain Python dictionary.

        Returns:
            dict: A plain Python dictionary representation of the DotDict.
        """
        return self.to_dict()
