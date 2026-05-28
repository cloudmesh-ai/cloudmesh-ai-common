"""
DotDict provides a dictionary-like object that allows accessing and setting
nested values using both attribute notation and dot-separated string keys.

DotDict extends OrderedDict to provide a powerful, intuitive interface for
working with nested configuration data. It supports attribute-style access,
dot-notation bracket access, automatic conversion of nested dicts, and
utility methods for expansion, merging, and serialization.

Quick Start:
    >>> from cloudmesh.ai.common.dotdict import DotDict
    >>> data = {"cloudmesh": {"ai": {"server": "uva"}}}
    >>> config = DotDict(data)

Access Patterns:
    # 1. Attribute access (chaining)
    >>> config.cloudmesh.ai.server
    'uva'

    # 2. Dot-notation bracket access
    >>> config["cloudmesh.ai.server"]
    'uva'

    # 3. Safe access with get() - supports dot-notation and defaults
    >>> config.get("cloudmesh.ai.server")
    'uva'
    >>> config.get("cloudmesh.ai.missing", "default")
    'default'

    # 4. Smart get - searches recursively for keys
    >>> config.smart_get("server")
    'uva'

Assignment Patterns:
    # 1. Dot-notation bracket assignment - auto-creates nested structures
    >>> config["cloudmesh.ai.port"] = 8000
    >>> config.cloudmesh.ai.port
    8000

    # 2. Attribute assignment
    >>> config.version = "2.0"
    >>> config["version"]
    '2.0'

    # 3. Nested attribute assignment
    >>> config.new_section = DotDict()
    >>> config.new_section.key = "value"
    >>> config["new_section.key"]
    'value'

    # 4. Dict values automatically converted to DotDict
    >>> config["model"] = {"name": "gemma", "size": "7B"}
    >>> isinstance(config.model, DotDict)
    True

Deletion and Membership:
    # 1. Dot-notation deletion
    >>> del config["cloudmesh.ai.server"]
    >>> "server" in config.cloudmesh.ai
    False

    # 2. Attribute deletion
    >>> del config.version
    >>> "version" not in config
    True

    # 3. Membership testing with dot-notation
    >>> "cloudmesh.ai.port" in config
    True

Placeholder Expansion:
    # 1. Expand placeholders using this DotDict's values
    >>> config = DotDict({"name": "gemma", "path": "/models/{name}"})
    >>> expanded = config.expand()
    >>> expanded.path
    '/models/gemma'

    # 2. Recursive expansion - placeholders can reference other placeholders
    >>> config = DotDict({
    ...     "base": "/home",
    ...     "user": "{base}/user",
    ...     "path": "{user}/models"
    ... })
    >>> expanded = config.expand()
    >>> expanded.path
    '/home/user/models'

    # 3. Expand external dictionary using this DotDict's values
    >>> data = {"path": "/models/{name}"}
    >>> expanded_external = config.expand(d=data)
    >>> expanded_external["path"]
    '/home/user/models'

Merging Configurations:
    # 1. Deep merge - nested dicts are merged recursively
    >>> config = DotDict({"a": {"b": 1}})
    >>> config.merge({"a": {"c": 2}})
    >>> config.a.b, config.a.c
    (1, 2)

    # 2. Standard dicts are automatically converted
    >>> config.merge({"new_section": {"key": "value"}})
    >>> isinstance(config.new_section, DotDict)
    True

Collection Methods with Path Support:
    # All these methods accept optional path parameter for nested access
    >>> config = DotDict({"level1": {"level2": {"a": 1, "b": 2}}})
    
    >>> list(config.keys("level1.level2"))
    ['a', 'b']
    
    >>> list(config.items("level1.level2"))
    [('a', 1), ('b', 2)]
    
    >>> list(config.values("level1.level2"))
    [1, 2]

Serialization:
    # 1. YAML output with literal block style for multi-line strings
    >>> config = DotDict({"script": "line1\nline2"})
    >>> print(config.yaml)
    script: |
      line1
      line2

    # 2. JSON output
    >>> config = DotDict({"a": {"b": 1}})
    >>> config.to_json(indent=2)
    '{
      "a": {
        "b": 1
      }
    }'

    # 3. Convert to plain dict (recursively)
    >>> plain = config.to_dict()
    >>> isinstance(plain, dict) and not isinstance(plain, DotDict)
    True

    # 4. String representation defaults to YAML
    >>> repr(config)  # or str(config)
    'a:\\n  b: 1\\n'

Advanced Features:
    # 1. Lists containing dicts are recursively converted
    >>> config = DotDict({"items": [{"name": "a"}, {"name": "b"}]})
    >>> isinstance(config.items[0], DotDict)
    True

    # 2. Order is preserved (inherits from OrderedDict)
    >>> config = DotDict({"z": 1, "a": 2, "m": 3})
    >>> list(config.keys())
    ['z', 'a', 'm']

    # 3. Empty initialization and kwargs support
    >>> config = DotDict(host="localhost", port=8080)
    >>> config.host, config.port
    ('localhost', 8080)

    # 4. Mix dict and kwargs
    >>> config = DotDict({"host": "localhost"}, port=8080)
    >>> config.host, config.port
    ('localhost', 8080)
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

    def __repr__(self):
        """Returns a string representation of the DotDict as YAML."""
        return self.yaml

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

        def _convert_value(v):
            """Recursively convert dicts to DotDict, including those in lists."""
            if isinstance(v, dict):
                return DotDict(v)
            elif isinstance(v, (list, tuple)):
                return type(v)(_convert_value(item) for item in v)
            else:
                return v

        # Recursively convert nested dictionaries to DotDict
        converted_data = OrderedDict()
        for k, v in data.items():
            converted_data[k] = _convert_value(v)

        super().__init__(converted_data)
        self.update(kwargs)

    @property
    def yaml(self):
        """Returns a YAML dump of the dictionary using literal block style for multi-line strings.

        Returns:
            str: The YAML representation of the DotDict.
        """
        # Create a local Dumper class to avoid polluting global yaml state
        class DotDictDumper(yaml.SafeDumper):
            pass
        
        DotDictDumper.add_representer(str, str_presenter)
        return yaml.dump(self.to_dict(), default_flow_style=False, Dumper=DotDictDumper)

    def expand(self, d=None, max_iterations=10):
        """Expands placeholders in a dictionary using this DotDict's values.
 
        Supports recursive expansion where placeholders may contain other placeholders.
        If a value in the target dictionary is a string containing {attribute}, 
        it is replaced by the value of the corresponding attribute found in this DotDict.
 
        Args:
            d (dict, optional): The dictionary to expand. If None, this DotDict 
                itself is expanded. Defaults to None.
            max_iterations (int, optional): Maximum iterations for recursive expansion.
                Prevents infinite loops with circular references. Defaults to 10.
 
        Returns:
            DotDict: A new DotDict with expanded values.
        """
        # If d is None, we expand self. Otherwise, we expand d.
        target = d if d is not None else self
        
        if not isinstance(target, dict):
            raise TypeError("Target to expand must be a dictionary")

        def _expand_value(v, replacements):
            """Expand a single value using the provided replacements dict."""
            if isinstance(v, str):
                result = v
                for placeholder, replacement in replacements.items():
                    if placeholder in result:
                        result = result.replace(placeholder, replacement)
                return result
            elif isinstance(v, DotDict):
                return v.expand(max_iterations=max_iterations)
            elif isinstance(v, dict):
                return DotDict(v).expand(max_iterations=max_iterations)
            elif isinstance(v, (list, tuple)):
                return type(v)(_expand_value(item, replacements) for item in v)
            else:
                return v

        def _build_replacements(source):
            """Build a dict of {placeholder} -> string value from a source dict."""
            reps = {}
            for key in source.keys():
                val = source[key]
                if val is not None:
                    reps[f"{{{key}}}"] = str(val)
            return reps

        # Build replacements from self (for expanding with this DotDict's values)
        self_replacements = _build_replacements(self)
        
        # Build replacements from target if it's different (local scope expansion)
        target_replacements = {}
        if isinstance(target, dict) and target is not self:
            target_replacements = _build_replacements(target)

        # Start with a copy and convert values
        result = OrderedDict()
        for k, v in target.items():
            result[k] = _expand_value(v, {**target_replacements, **self_replacements})
        
        # Perform recursive expansion for nested placeholders
        # e.g., {a} where a="/path/{b}" and b="value" -> /path/value
        for _ in range(max_iterations):
            changed = False
            
            # Build new replacements from current result
            current_replacements = {}
            for key in self.keys():
                val = result.get(key)
                if val is not None and not isinstance(val, (dict, DotDict, list, tuple)):
                    current_replacements[f"{{{key}}}"] = str(val)
            
            # Also include target's own keys for local expansion
            if target is not self:
                for key in target.keys():
                    val = result.get(key)
                    if val is not None and not isinstance(val, (dict, DotDict, list, tuple)):
                        current_replacements[f"{{{key}}}"] = str(val)
            
            # Apply replacements
            for k, v in list(result.items()):
                if isinstance(v, str):
                    new_v = v
                    for placeholder, replacement in current_replacements.items():
                        if placeholder in new_v:
                            new_v = new_v.replace(placeholder, replacement)
                    if new_v != v:
                        result[k] = new_v
                        changed = True
            
            if not changed:
                break
        
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

    def __contains__(self, key):
        """Checks if a key exists, supporting dot-notation for nested paths.

        Args:
            key (str): The key to check. If it contains dots, it is treated as a path.

        Returns:
            bool: True if the key or path exists, False otherwise.
        """
        if isinstance(key, str) and "." in key:
            try:
                self[key]
                return True
            except KeyError:
                return False
        return super().__contains__(key)

    def keys(self, path=None):
        """Returns keys, optionally from a nested path.

        Args:
            path (str, optional): Dot-notation path to get keys from.
                If None, returns keys of this dictionary. Defaults to None.

        Returns:
            KeysView or list: Keys from the specified path or this dictionary.
        """
        if path is None:
            return super().keys()
        target = self[path]
        if not isinstance(target, dict):
            raise TypeError(f"Path '{path}' does not point to a dictionary")
        return target.keys()

    def items(self, path=None):
        """Returns items, optionally from a nested path.

        Args:
            path (str, optional): Dot-notation path to get items from.
                If None, returns items of this dictionary. Defaults to None.

        Returns:
            ItemsView or list: Items from the specified path or this dictionary.
        """
        if path is None:
            return super().items()
        target = self[path]
        if not isinstance(target, dict):
            raise TypeError(f"Path '{path}' does not point to a dictionary")
        return target.items()

    def values(self, path=None):
        """Returns values, optionally from a nested path.

        Args:
            path (str, optional): Dot-notation path to get values from.
                If None, returns values of this dictionary. Defaults to None.

        Returns:
            ValuesView or list: Values from the specified path or this dictionary.
        """
        if path is None:
            return super().values()
        target = self[path]
        if not isinstance(target, dict):
            raise TypeError(f"Path '{path}' does not point to a dictionary")
        return target.values()

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
        # Avoid interfering with Python internals and OrderedDict's private attributes
        if key.startswith("_"):
            super().__setattr__(key, value)
        else:
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
