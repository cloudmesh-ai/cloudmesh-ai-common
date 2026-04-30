# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import collections
import json
import os
import re
import ast
import yaml
from typing import Any, Dict, List, Optional, Union

from cloudmesh.ai.common.io import readfile, writefile

class Variables:
    """A lightweight class for managing variables used in configuration expansion."""
    def __init__(self):
        """Initialize the Variables object."""
        self._vars = {}

    def __getitem__(self, key):
        """Retrieve a variable value by key.

        Args:
            key: The variable name.

        Returns:
            The value of the variable, or an empty string if not found.
        """
        return self._vars.get(key, "")

    def __iter__(self):
        """Iterate over the variable keys.

        Returns:
            An iterator over the keys of the variables dictionary.
        """
        return iter(self._vars)

    def __contains__(self, key):
        """Check if a variable exists.

        Args:
            key: The variable name to check.

        Returns:
            True if the variable exists, False otherwise.
        """
        return key in self._vars

    def add(self, key, value):
        """Add or update a variable.

        Args:
            key: The variable name.
            value: The value to assign to the variable.
        """
        self._vars[key] = value

    def items(self):
        """Return the variables as key-value pairs.

        Returns:
            A view of the variables dictionary items.
        """
        return self._vars.items()

def key_prefix_replace(d: Dict, prefix: List[str], new_prefix: str = "") -> Dict:
    """Replaces the list of prefixes in keys of a flattened dict.

    Args:
        d: The flattened dict.
        prefix: A list of prefixes that are replaced with a new prefix.
        new_prefix: The new prefix.

    Returns:
        The dict with the keys replaced as specified.
    """
    items = []
    for k, v in list(d.items()):
        new_key = k
        for p in prefix:
            new_key = new_key.replace(p, new_prefix, 1)
        items.append((new_key, v))
    return dict(items)

def flatten(d: Any, parent_key: str = "", sep: str = "__") -> Union[Dict, List]:
    """Flattens a multidimensional dict into a one-dimensional dictionary.

    Args:
        d: The multidimensional dictionary or list to flatten.
        parent_key: The prefix to use for the keys in the flattened dictionary. 
            Defaults to "".
        sep: The separation character used to join nested keys. Defaults to "__".

    Returns:
        A flattened dictionary if the input was a dictionary, a list of flattened 
        dictionaries if the input was a list, or the original object if it was 
        neither.
    """
    if isinstance(d, list):
        flat = []
        for entry in d:
            flat.append(flatten(entry, parent_key=parent_key, sep=sep))
        return flat
    elif isinstance(d, collections.abc.MutableMapping):
        items = []
        for k, v in list(d.items()):
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.abc.MutableMapping):
                items.extend(list(flatten(v, new_key, sep=sep).items()))
            else:
                items.append((new_key, v))
        return dict(items)
    else:
        return d

def flatme(d: Dict) -> Dict:
    """Flattens all values in a dictionary if they are dictionaries.

    Args:
        d: The dictionary whose values should be flattened.

    Returns:
        A new dictionary where all dictionary values have been flattened.
    """
    o = {}
    for element in d:
        o[element] = flatten(d[element])
    return o

class FlatDict(dict):
    """A data structure to manage a flattened dict."""

    def __init__(self, d: Optional[Dict] = None, expand: List[str] = ["os.", "cm.", "cloudmesh."], sep: str = "__"):
        """Initializes the flat dict.

        Args:
            d: The dict data.
            expand: List of prefixes to expand.
            sep: The character used to indicate a hierarchy.
        """
        data = d if d is not None else {}
        flattened = flatten(data, sep=sep)
        
        # Initialize the dict with the flattened data
        super().__init__(flattened)
        self._data = flattened
        self.sep = sep
        
        if "all" in expand:
            self.expand_os = True
            self.expand_cloudmesh = True
            self.expand_cm = True
        else:
            self.expand_os = "os." in expand
            self.expand_cloudmesh = "cloudmesh." in expand
            self.expand_cm = "cm." in expand

    def __setitem__(self, key, item):
        """Set a value in the flat dict.

        Args:
            key: The key to set.
            item: The value to assign.
        """
        super().__setitem__(key, item)
        self._data[key] = item

    def __getitem__(self, key):
        """Retrieve a value from the flat dict.

        Args:
            key: The key to retrieve.

        Returns:
            The value associated with the key.
        """
        return super().__getitem__(key)

    def __repr__(self):
        """Return a string representation of the flat dict.

        Returns:
            A string representation of the underlying data.
        """
        return repr(self._data)

    def __str__(self):
        """Return a string representation of the flat dict.

        Returns:
            A string representation of the underlying data.
        """
        return str(self._data)

    def __len__(self):
        """Return the number of items in the flat dict.

        Returns:
            The number of items.
        """
        return len(self._data)

    def __delitem__(self, key):
        """Remove an item from the flat dict.

        Args:
            key: The key to remove.
        """
        super().__delitem__(key)
        del self._data[key]

    def keys(self):
        """Return a list of keys in the flat dict.

        Returns:
            A list of keys.
        """
        return list(self._data.keys())

    def values(self):
        """Return a list of values in the flat dict.

        Returns:
            A list of values.
        """
        return list(self._data.values())

    def __contains__(self, item):
        """Check if a key exists in the flat dict.

        Args:
            item: The key to check.

        Returns:
            True if the key exists, False otherwise.
        """
        return item in self._data

    def add(self, key, value):
        """Add a key-value pair to the flat dict.

        Args:
            key: The key to add.
            value: The value to assign.
        """
        self._data[key] = value

    def __iter__(self):
        """Iterate over the keys of the flat dict.

        Returns:
            An iterator over the keys.
        """
        return iter(self._data)

    def __call__(self):
        """Return the underlying data dictionary.

        Returns:
            The internal data dictionary.
        """
        return self._data

    def __getattr__(self, attr):
        """Allow attribute-style access to keys.

        Args:
            attr: The attribute name (key) to retrieve.

        Returns:
            The value associated with the key, or None if not found.
        """
        return self.get(attr)

    def search(self, key: str, value: Any = None) -> List[str]:
        """Returns keys that match the given regex pattern and value."""
        flat = FlatDict(self._data, sep=".")
        r = re.compile(key)
        result = list(filter(r.match, flat))
        if value is None:
            found = result
        else:
            found = []
            for entry in result:
                if str(flat[entry]) == str(value):
                    found.append(entry)
        return found

    def unflatten(self) -> Dict:
        """Unflattens the flat dict back to a regular nested dict."""
        result = {}
        for k, v in self._data.items():
            self._unflatten_entry(k, v, result)
        return result

    def _unflatten_entry(self, k: str, v: Any, out: Dict):
        """Helper to recursively unflatten a single key-value pair.

        Args:
            k: The flattened key.
            v: The value.
            out: The dictionary to populate.
        """
        parts = k.split(self.sep, 1)
        key = parts[0]
        if len(parts) > 1:
            self._unflatten_entry(parts[1], v, out.setdefault(key, {}))
        else:
            out[key] = v

    def loadf(self, filename: str = None, sep: Optional[str] = None):
        """Load configuration from a file.

        Args:
            filename: Path to the YAML configuration file.
            sep: The separation character to use for flattening. 
                Defaults to self.sep.
        """
        actual_sep = sep if sep else self.sep
        config = read_config_parameters(filename=filename, sep=actual_sep)
        self.update(config)
        self._data.update(config)

    def loads(self, content: Any = None, sep: Optional[str] = None):
        """Load configuration from a string.

        Args:
            content: The YAML string to load.
            sep: The separation character to use for flattening. 
                Defaults to self.sep.
        """
        actual_sep = sep if sep else self.sep
        config = read_config_parameters_from_string(content=content, sep=actual_sep)
        self.update(config)
        self._data.update(config)

    def loadd(self, content: Any = None, sep: Optional[str] = None):
        """Load configuration from a dictionary.

        Args:
            content: The dictionary to load.
            sep: The separation character to use for flattening. 
                Defaults to self.sep.
        """
        actual_sep = sep if sep else self.sep
        config = read_config_parameters_from_dict(content=content, sep=actual_sep)
        self.update(config)
        self._data.update(config)

    def load(self, content: Any = None, expand: bool = True, sep: str = "."):
        """Reads in the dict based on the values and types provided."""
        if content is None:
            config = None
            self.loads(config)
        elif isinstance(content, dict):
            self.loadd(content=content, sep=sep)
        elif os.path.isfile(str(content)):
            self.loadf(filename=content, sep=sep)
        elif isinstance(content, str):
            self.loads(content=content, sep=sep)
        else:
            config = None
            self.__init__(config, sep=sep)
        
        if expand:
            e = expand_config_parameters(
                flat=self._data,
                expand_yaml=True,
                expand_os=self.expand_os,
                expand_cloudmesh=self.expand_cloudmesh or self.expand_cm,
            )
            self._data = e

    def apply_in_string(self, content: str) -> str:
        """Replace placeholders in a string with values from the flat dict.

        Placeholders should be in the format {key}.

        Args:
            content: The string containing placeholders.

        Returns:
            The string with placeholders replaced by their corresponding values.
        """
        r = content
        for v in self._data:
            try:
                r = r.replace("{" + str(v) + "}", str(self._data[v]))
            except Exception:
                pass
        return r

    def apply(self, content: Any, write: bool = True) -> Optional[str]:
        """Converts a string or the contents of a file with the values of the flatdict."""
        if content is None:
            return None
        elif os.path.isfile(str(content)):
            data = readfile(content)
            result = self.apply_in_string(data)
            if write:
                writefile(content, result)
            return result
        elif isinstance(content, str):
            return self.apply_in_string(content)
        else:
            return None

class FlatDict2:
    """Utility class for converting objects to dictionaries and FlatDicts."""
    primitive = (int, str, bool, bytes, dict, list)

    @classmethod
    def is_primitive(cls, thing):
        """Check if an object is a primitive type.

        Args:
            thing: The object to check.

        Returns:
            True if the object is a primitive type, False otherwise.
        """
        return type(thing) in cls.primitive

    @classmethod
    def convert(cls, obj: Any, flatten: bool = True) -> Union[Dict, FlatDict]:
        """Converts an object into a dictionary, optionally flattening it.

        Args:
            obj: The object to convert.
            flatten: Whether to return a FlatDict instead of a regular dict. 
                Defaults to True.

        Returns:
            The converted dictionary or FlatDict.
        """
        dict_result = cls.object_to_dict(obj)
        if flatten:
            dict_result = FlatDict(dict_result)
        return dict_result

    @classmethod
    def object_to_dict(cls, obj: Any) -> Dict:
        """Recursively converts an object's attributes into a dictionary.

        Args:
            obj: The object to convert.

        Returns:
            A dictionary representation of the object.
        """
        dict_obj = dict()
        if obj is not None:
            if isinstance(obj, list):
                dict_list = []
                for inst in obj:
                    dict_list.append(cls.object_to_dict(inst))
                dict_obj["list"] = dict_list
            elif not cls.is_primitive(obj):
                for key in getattr(obj, "__dict__", {}):
                    val = getattr(obj, key)
                    if isinstance(val, list):
                        dict_list = []
                        for inst in val:
                            dict_list.append(cls.object_to_dict(inst))
                        dict_obj[key] = dict_list
                    elif not cls.is_primitive(val):
                        dict_obj[key] = cls.object_to_dict(val)
                    else:
                        dict_obj[key] = val
            elif cls.is_primitive(obj):
                return obj
        return dict_obj

def read_config_parameters(filename: str = None, d: str = None, sep: str = ".") -> Dict:
    """Reads configuration parameters from a YAML file and produces a flattened dict.

    Args:
        filename: Path to the YAML configuration file.
        d: Optional YAML string to merge into the configuration.
        sep: The separation character used for flattening. Defaults to ".".

    Returns:
        A flattened dictionary of the configuration parameters.
    """
    config = {}
    if filename:
        content = readfile(filename)
        config = yaml.safe_load(content) or {}
    if d:
        data = yaml.safe_load(d) or {}
        config.update(data)
    return flatten(config, sep=sep)

def read_config_parameters_from_string(content: str = None, d: str = None, sep: str = ".") -> Dict:
    """Reads configuration parameters from a YAML string and produces a flattened dict.

    Args:
        content: The YAML string to parse.
        d: Optional YAML string to merge into the configuration.
        sep: The separation character used for flattening. Defaults to ".".

    Returns:
        A flattened dictionary of the configuration parameters.
    """
    config = {}
    if content:
        config = yaml.safe_load(content) or {}
    if d:
        data = yaml.safe_load(d) or {}
        config.update(data)
    return flatten(config, sep=sep)

def read_config_parameters_from_dict(content: Dict = None, d: str = None, sep: str = ".") -> Dict:
    """Reads configuration parameters from a dictionary and produces a flattened dict.

    Args:
        content: The dictionary to parse.
        d: Optional YAML string to merge into the configuration.
        sep: The separation character used for flattening. Defaults to ".".

    Returns:
        A flattened dictionary of the configuration parameters.
    """
    config = {}
    if content:
        config = dict(content)
    if d:
        data = yaml.safe_load(d) or {}
        config.update(data)
    return flatten(config, sep=sep)

def expand_config_parameters(
    flat: Dict = None,
    expand_yaml: bool = True,
    expand_os: bool = True,
    expand_cloudmesh: bool = True,
    debug: bool = False,
    depth: int = 100,
) -> Dict:
    """Expands all variables in the flat dict if they are specified in the values.

    Supports expansion of YAML variables, OS environment variables, and 
    cloudmesh-specific variables.

    Args:
        flat: The flattened dictionary to expand.
        expand_yaml: Whether to expand variables defined within the dict itself. 
            Defaults to True.
        expand_os: Whether to expand OS environment variables (e.g., {os.HOME}). 
            Defaults to True.
        expand_cloudmesh: Whether to expand cloudmesh variables (e.g., {cm.USER}). 
            Defaults to True.
        debug: Whether to enable debug logging. Defaults to False.
        depth: Maximum recursion depth for YAML expansion. Defaults to 100.

    Returns:
        A new dictionary with all variables expanded.
    """
    if flat is None:
        return {}
    
    txt = json.dumps(flat)
    values = " ".join(str(v) for v in flat.values())

    if expand_yaml:
        for _ in range(depth):
            changed = False
            for variable, value in flat.items():
                name = "{" + variable + "}"
                if name in txt:
                    txt = txt.replace(name, str(value))
                    changed = True
            if not changed:
                break

    if "{os." in values and expand_os:
        for variable, value in os.environ.items():
            name = "{os." + variable + "}"
            if name in values:
                txt = txt.replace(name, str(value))

    cm_variables = Variables()
    if ("{cloudmesh." in values or "{cm." in values) and expand_cloudmesh:
        for variable, value in cm_variables.items():
            name_full = "{cloudmesh." + variable + "}"
            name_short = "{cm." + variable + "}"
            txt = txt.replace(name_full, str(value)).replace(name_short, str(value))

    config = json.loads(txt)

    if "eval(" in values:
        for variable in config.keys():
            value = config[variable]
            if isinstance(value, str) and "eval(" in value:
                try:
                    expr = value.replace("eval(", "").strip()
                    if expr.endswith(")"):
                        expr = expr[:-1]
                    # Use eval with restricted globals/locals for basic math
                    # This is safer than raw eval but allows 1+1
                    config[variable] = eval(expr, {"__builtins__": {}}, {})
                except Exception:
                    pass

    return config