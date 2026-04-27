# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import os
import yaml
import copy
from pathlib import Path
from typing import Any, Dict, Optional
from cloudmesh.ai.common import logging as ai_log
from cloudmesh.ai.common import DotDict

logger = ai_log.get_logger("common.config")

class Config:
    """Handles configuration for AI packages from a YAML file."""
    
    # Default path can be overridden by subclasses or during initialization
    DEFAULT_CONFIG_PATH = Path("~/.config/cloudmesh/ai/common.yaml").expanduser()
    
    DEFAULTS = {}
    SCHEMA = {}

    def __init__(self, config_path: Optional[Path] = None):
        self.path = config_path or self.DEFAULT_CONFIG_PATH
        self.data = DotDict(copy.deepcopy(self.DEFAULTS))
        self._load_config()

    def _load_config(self):
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self.data.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config file {self.path}: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a value from the config using a dot-separated path (e.g., 'telemetry.enabled').
        Environment variables can override config values.
        """
        # 1. Check for environment variable override
        env_var = f"AI_{key_path.replace('.', '_').upper()}"
        env_val = os.environ.get(env_var)
        if env_val is not None:
            if key_path in self.SCHEMA:
                expected_type = self.SCHEMA[key_path]["type"]
                try:
                    if expected_type is bool:
                        return env_val.lower() in ("true", "1", "yes")
                    return expected_type(env_val)
                except (ValueError, TypeError):
                    logger.warning(f"Environment variable {env_var} has invalid value '{env_val}' for type {expected_type.__name__}. Using config value.")
            else:
                return env_val

        # 2. Fallback to config data using DotDict's nested access
        try:
            # We can't use getattr(self.data, key_path) because key_path has dots
            # But we can use the same logic as YamlDB or just iterate
            val = self.data
            for k in key_path.split("."):
                val = val[k]
            return val
        except (KeyError, TypeError):
            return default

    def validate(self, key_path: str, value: Any):
        """Validates a configuration value against the schema if it exists."""
        if key_path in self.SCHEMA:
            expected_type = self.SCHEMA[key_path]["type"]
            if not isinstance(value, expected_type):
                raise TypeError(f"Invalid type for '{key_path}'. Expected {expected_type.__name__}, got {type(value).__name__}.")

    def set(self, key_path: str, value: Any):
        """Set a value in the config using a dot-separated path (e.g., 'telemetry.enabled')."""
        self.validate(key_path, value)
        keys = key_path.split(".")
        val = self.data
        for k in keys[:-1]:
            if k not in val or not isinstance(val[k], dict):
                val[k] = DotDict()
            val = val[k]
        val[keys[-1]] = value

    def save(self):
        """Saves the current configuration to the YAML file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w") as f:
                yaml.dump(self.data, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Could not save config file {self.path}: {e}")
            raise
