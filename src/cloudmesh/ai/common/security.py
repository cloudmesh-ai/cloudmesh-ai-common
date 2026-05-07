# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import os
import subprocess
from typing import Optional, List, Union
from pathlib import Path

from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.common.exceptions import SecurityError, SecurityAuthError

logger = get_contextual_logger("common.security")

class BaseSecurity:
    """Base class for security and privilege escalation utilities."""

    def __init__(self, debug: bool = False):
        self.debug = debug

    def is_root(self) -> bool:
        """Check if the current process is running as root."""
        return os.geteuid() == 0

    def sudo_execute_local(self, command: Union[str, List[str]], input_data: Optional[str] = None) -> str:
        """Execute a command locally with sudo.

        Args:
            command: The command to execute.
            input_data: Optional data to pass to stdin (e.g., password).

        Returns:
            str: The output of the command.

        Raises:
            SecurityAuthError: If sudo authentication fails.
        """
        if isinstance(command, str):
            cmd = ["sudo", "-S"] + command.split()
        else:
            cmd = ["sudo", "-S"] + command

        if self.debug:
            logger.debug(f"Executing local sudo command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                input=input_data,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            if "incorrect password" in e.stderr.lower() or "sudo: a password is required" in e.stderr.lower():
                raise SecurityAuthError(f"Sudo authentication failed: {e.stderr}")
            logger.error(f"Sudo command failed: {e.stderr}")
            raise SecurityError(f"Sudo execution failed: {e.stderr}")

    def verify_file_permissions(self, path: Union[str, Path], readable: bool = True, writable: bool = False) -> bool:
        """Verify if the current user has the required permissions for a file."""
        path_obj = Path(path)
        if not path_obj.exists():
            return False
        
        try:
            if readable and not os.access(path_obj, os.R_OK):
                return False
            if writable and not os.access(path_obj, os.W_OK):
                return False
            return True
        except Exception as e:
            logger.error(f"Error verifying permissions for {path}: {e}")
            return False

    def secure_write(self, path: Union[str, Path], content: str, mode: int = 0o600):
        """Write content to a file with restricted permissions (e.g., for private keys)."""
        path_obj = Path(path)
        try:
            # Create file with restricted permissions from the start
            with os.fdopen(os.open(path_obj, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode), 'w') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Secure write failed for {path}: {e}")
            raise SecurityError(f"Could not write secure file {path}: {e}")