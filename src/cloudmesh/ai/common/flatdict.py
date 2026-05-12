# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""FlatDict provides utilities for flattening nested dictionaries and managing them as a single-level map.

This module is useful for configuration management where nested structures need to be 
represented as flat key-value pairs (e.g., for environment variables or simple lookups).

Variable Expansion:
    The `expand_config_parameters` function (used by `FlatDict.load`) supports four types of expansion:
    1. Internal YAML Expansion: Replaces `{key}` with the value of another key in the same dict.
       This is recursive, allowing chained references.
    2. OS Environment Expansion: Replaces `{os.VARIABLE}` with the value of the system environment variable.
    3. Cloudmesh Variable Expansion: Replaces `{cloudmesh.VAR}` or `{cm.VAR}` using the `Variables` registry.
    4. Math Evaluation: Replaces `eval(expression)` with the result of a restricted Python evaluation
       (e.g., `eval(1 + 1)` becomes `2`).

Examples:
    >>> # 1. Basic Flattening
    >>> data = {"cloudmesh": {"ai": {"server": "uva"}}}
    >>> flat = FlatDict(data)
    >>> print(flat["cloudmesh.ai.server"])
    'uva'

    >>> # 2. Unflattening
    >>> nested = flat.unflatten()
    >>> print(nested["cloudmesh"]["ai"]["server"])
    'uva'

    >>> # 3. Attribute-style access
    >>> print(flat.cloudmesh.ai.server)
    'uva'

    >>> # 4. Creating from a Python Object
    >>> class Server:
    ...     def __init__(self):
    ...         self.name = "uva"
    ...         self.port = 8000
    >>> s = Server()
    >>> flat_obj = FlatDict.from_object(s)
    >>> print(flat_obj.name)
    'uva'

    >>> # 5. Variable Expansion
    >>> data = {"user": "grey", "path": "/home/{user}/models"}
    >>> flat_exp = FlatDict(data)
    >>> flat_exp.load(content=data, expand=True)
    >>> print(flat_exp.path)
    '/home/grey/models'

    >>> # 6. Applying to strings
    >>> template = "Connecting to {cloudmesh.ai.server}..."
    >>> print(flat.apply_in_string(template))
    'Connecting to uva...'
"""

import collections
import json
import os
import re
import ast
import yaml
from typing import Any, Dict, List, Optional, Union

from cloudmesh.ai.common.io import readfile, writefile

class Variables:
    """A lightweight class for managing variables used in configuration expansion.

    Attributes:
        _vars (Dict): Internal storage for variables.
    """
    def __init__(self):
        """Initializes the Variables object."""
        self._vars = {}

    def __getitem__(self, key):
        """Retrieves a variable value by key.

        Args:
            key (str): The variable name.

        Returns:
            Any: The value of the variable, or an empty string if not found.
        """
        return self._vars.get(key, "")

    def __iter__(self):
        """Iterates over the variable keys.

        Returns:
            Iterator: An iterator over the keys of the variables dictionary.
        """
        return iter(self._vars)

    def __contains__(self, key):
        """Checks if a variable exists.

        Args:
            key (str): The variable name to check.

        Returns:
            bool: True if the variable exists, False otherwise.
        """
        return key in self._vars

    def add(self, key, value):
        """Adds or updates a variable.

        Args:
            key (str): The variable name.
            value (Any): The value to assign to the variable.
        """
        self._vars[key] = value

    def items(self):
        """Returns the variables as key-value pairs.

        Returns:
            ItemsView: A view of the variables dictionary items.
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

def flatten(d: Any, parent_key: str = "", sep: str = ".") -> Union[Dict, List]:
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
    """A data structure to manage a flattened dictionary.

    This class provides a way to handle nested dictionaries as a single-level 
    dictionary with keys joined by a separator.
    """

    @staticmethod
    def _is_primitive(thing: Any) -> bool:
        """Checks if an object is a primitive type.

        Args:
            thing (Any): The object to check.

        Returns:
            bool: True if the object is a primitive type, False otherwise.
        """
        return type(thing) in (int, str, bool, bytes, dict, list)

    @classmethod
    def _object_to_dict(cls, obj: Any) -> Any:
        """Recursively converts an object's attributes into a dictionary.

        Args:
            obj (Any): The object to convert.

        Returns:
            Any: A dictionary representation of the object, or the object itself 
                if it is primitive.
        """
        if obj is None:
            return {}
        
        if cls._is_primitive(obj):
            return obj

        if isinstance(obj, list):
            return [cls._object_to_dict(inst) for inst in obj]

        dict_obj = {}
        for key in getattr(obj, "__dict__", {}):
            val = getattr(obj, key)
            dict_obj[key] = cls._object_to_dict(val)
        return dict_obj

    @classmethod
    def from_object(cls, obj: Any, **kwargs) -> 'FlatDict':
        """Creates a FlatDict from a Python object.

        Args:
            obj (Any): The object to convert and flatten.
            **kwargs: Additional arguments passed to the FlatDict constructor 
                (e.g., sep, expand).

        Returns:
            FlatDict: A FlatDict instance created from the object.
        """
        dict_result = cls._object_to_dict(obj)
        return cls(dict_result, **kwargs)

    def __init__(self, d: Optional[Dict] = None, expand: List[str] = ["os.", "cm.", "cloudmesh."], sep: str = "."):
        """Initializes the FlatDict.

        Args:
            d (Optional[Dict]): The dictionary data to flatten. Defaults to None.
            expand (List[str], optional): List of prefixes to expand. 
                Defaults to ["os.", "cm.", "cloudmesh."].
            sep (str, optional): The character used to indicate a hierarchy. 
                Defaults to "__".
        """
        data = d if d is not None else {}
        flattened = flatten(data, sep=sep)
        
        super().__init__(flattened)
        self.sep = sep
        
        if "all" in expand:
            self.expand_os = True
            self.expand_cloudmesh = True
            self.expand_cm = True
        else:
            self.expand_os = "os." in expand
            self.expand_cloudmesh = "cloudmesh." in expand
            self.expand_cm = "cm." in expand

    def __getattr__(self, attr):
        """Allow attribute-style access to keys.

        Args:
            attr (str): The attribute name (key) to retrieve.

        Returns:
            Any: The value associated with the key, or None if not found.
        """
        return self.get(attr)

    def search(self, key: str, value: Any = None) -> List[str]:
        """Returns keys that match the given regex pattern and value.

        Args:
            key (str): The regex pattern to search for in keys.
            value (Any, optional): The value to match against. Defaults to None.

        Returns:
            List[str]: A list of keys that match the pattern and value.
        """
        # Use a temporary FlatDict with dot separator for searching
        flat = FlatDict(self, sep=".")
        r = re.compile(key)
        result = list(filter(r.match, flat))
        if value is None:
            return result
        
        return [entry for entry in result if str(flat[entry]) == str(value)]

    def unflatten(self) -> Dict:
        """Unflattens the flat dict back to a regular nested dict.

        Returns:
            Dict: The unflattened nested dictionary.
        """
        result = {}
        for k, v in self.items():
            self._unflatten_entry(k, v, result)
        return result

    def _unflatten_entry(self, k: str, v: Any, out: Dict):
        """Helper to recursively unflatten a single key-value pair.

        Args:
            k (str): The flattened key.
            v (Any): The value.
            out (Dict): The dictionary to populate.
        """
        parts = k.split(self.sep, 1)
        key = parts[0]
        if len(parts) > 1:
            self._unflatten_entry(parts[1], v, out.setdefault(key, {}))
        else:
            out[key] = v

    def loadf(self, filename: str = None, sep: Optional[str] = None):
        """Loads configuration from a YAML file.

        Args:
            filename (str, optional): Path to the YAML configuration file.
            sep (str, optional): The separation character to use for flattening. 
                Defaults to self.sep.
        """
        actual_sep = sep if sep else self.sep
        config = read_config_parameters(filename=filename, sep=actual_sep)
        self.update(config)

    def loads(self, content: Any = None, sep: Optional[str] = None):
        """Loads configuration from a YAML string.

        Args:
            content (Any, optional): The YAML string to load.
            sep (str, optional): The separation character to use for flattening. 
                Defaults to self.sep.
        """
        actual_sep = sep if sep else self.sep
        config = read_config_parameters_from_string(content=content, sep=actual_sep)
        self.update(config)

    def loadd(self, content: Any = None, sep: Optional[str] = None):
        """Loads configuration from a dictionary.

        Args:
            content (Any, optional): The dictionary to load.
            sep (str, optional): The separation character to use for flattening. 
                Defaults to self.sep.
        """
        actual_sep = sep if sep else self.sep
        config = read_config_parameters_from_dict(content=content, sep=actual_sep)
        self.update(config)

    def load(self, content: Any = None, expand: bool = True, sep: str = "."):
        """Reads in the dict based on the values and types provided.

        Args:
            content (Any, optional): The content to load (file path, string, or dict).
            expand (bool, optional): Whether to expand variables. Defaults to True.
            sep (str, optional): The separation character to use. Defaults to ".".
        """
        if content is None:
            self.loads(None)
        elif isinstance(content, dict):
            self.loadd(content=content, sep=sep)
        elif os.path.isfile(str(content)):
            self.loadf(filename=content, sep=sep)
        elif isinstance(content, str):
            self.loads(content=content, sep=sep)
        else:
            # Re-initialize with None to reset
            self.clear()
            self.__init__(None, sep=sep)
        
        if expand:
            expanded = expand_config_parameters(
                flat=self,
                expand_yaml=True,
                expand_os=self.expand_os,
                expand_cloudmesh=self.expand_cloudmesh or self.expand_cm,
            )
            self.clear()
            self.update(expanded)

    def apply_in_string(self, content: str) -> str:
        """Replaces placeholders in a string with values from the flat dict.

        Placeholders should be in the format {key}.

        Args:
            content (str): The string containing placeholders.

        Returns:
            str: The string with placeholders replaced by their corresponding values.
        """
        result = content
        for key, value in self.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result

    def apply(self, content: Any, write: bool = True) -> Optional[str]:
        """Converts a string or the contents of a file with the values of the flatdict.

        Args:
            content (Any): The string or file path to process.
            write (bool, optional): Whether to write the result back to the file. 
                Defaults to True.

        Returns:
            Optional[str]: The processed string, or None if content was invalid.
        """
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
        return None


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
        flat (Dict, optional): The flattened dictionary to expand. Defaults to None.
        expand_yaml (bool, optional): Whether to expand variables defined within 
            the dict itself. Defaults to True.
        expand_os (bool, optional): Whether to expand OS environment variables 
            (e.g., {os.HOME}). Defaults to True.
        expand_cloudmesh (bool, optional): Whether to expand cloudmesh variables 
            (e.g., {cm.USER}). Defaults to True.
        debug (bool, optional): Whether to enable debug logging. Defaults to False.
        depth (int, optional): Maximum recursion depth for YAML expansion. 
            Defaults to 100.

    Returns:
        Dict: A new dictionary with all variables expanded.
    """
    if flat is None:
        return {}
    
    # Work on a copy to avoid mutating the original
    result = dict(flat)
    
    # 1. Expand internal YAML variables
    if expand_yaml:
        for _ in range(depth):
            changed = False
            for key, value in result.items():
                if not isinstance(value, str):
                    continue
                
                # Find all {var} patterns
                pattern = r"\{([^}]+)\}"
                matches = re.findall(pattern, value)
                
                for var_name in matches:
                    if var_name in result:
                        replacement = str(result[var_name])
                        result[key] = result[key].replace(f"{{{var_name}}}", replacement)
                        changed = True
            if not changed:
                break

    # 2. Expand OS environment variables
    if expand_os:
        for key, value in result.items():
            if isinstance(value, str) and "{os." in value:
                pattern = r"\{os\.([^}]+)\}"
                def replace_os(match):
                    var_name = match.group(1)
                    return os.environ.get(var_name, f"{{{var_name}}}")
                result[key] = re.sub(pattern, replace_os, value)

    # 3. Expand Cloudmesh variables
    if expand_cloudmesh:
        cm_vars = Variables()
        for key, value in result.items():
            if isinstance(value, str) and ("{cloudmesh." in value or "{cm." in value):
                pattern = r"\{(cloudmesh\.|cm\.)([^}]+)\}"
                def replace_cm(match):
                    var_name = match.group(2)
                    return str(cm_vars[var_name])
                result[key] = re.sub(pattern, replace_cm, value)

    # 4. Handle eval() expressions for basic math
    for key, value in result.items():
        if isinstance(value, str) and "eval(" in value:
            try:
                expr = value.replace("eval(", "").strip()
                if expr.endswith(")"):
                    expr = expr[:-1]
                # Use eval with restricted globals/locals for basic math
                result[key] = eval(expr, {"__builtins__": {}}, {})
            except Exception:
                pass

    return result
