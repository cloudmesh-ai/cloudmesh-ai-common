# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import secrets
import string
import os
import subprocess
from pathlib import Path
from typing import Any, Optional, Union, List

from cloudmesh.ai.common import logging as ai_log

logger = ai_log.get_logger("common.security")


class SudoError(Exception):
    """Exception raised for errors during sudo operations."""
    pass

def can_use_sudo() -> bool:
    """Checks if the current user has sudo privileges.

    Returns:
        bool: True if the user has sudo privileges, False otherwise.
    """
    try:
        # Use a list for subprocess to avoid shell=True
        output = subprocess.check_output(["sudo", "id", "-u"], stderr=subprocess.DEVNULL).decode().strip()
        return output == "0"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_strong_pass() -> str:
    """Generates a cryptographically secure password from letters, digits and punctuation

    Returns:
        str: password
    """
    length = secrets.randbelow(6) + 10  # Length between 10 and 15
    password_characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(secrets.choice(password_characters) for _ in range(length))


class Sudo:
    """
    A utility class for executing commands with sudo privileges and performing file operations.

    Methods:
        password(msg="sudo password: "):
            Prompt the user for the sudo password.

        execute(command, decode=True, debug=False, msg=None):
            Execute the specified command with sudo.
            Args:
                command (Union[List[str], str]): The command to run.
                decode (bool, optional): If True, decode the output from bytes to UTF-8.
                debug (bool, optional): If True, print command execution details.
                msg (str, optional): Message to print before executing the command.
            Returns:
                subprocess.CompletedProcess: The result of the command execution.

        readfile(filename, split=False, trim=False, decode=True):
            Read the content of the file with sudo privileges and return the result.
            Args:
                filename (Union[str, Path]): The filename.
                split (bool, optional): If True, return a list of lines.
                trim (bool, optional): If True, trim trailing whitespace.
                decode (bool, optional): If True, decode the output from bytes to UTF-8.
            Returns:
                Union[str, List[str]]: The content of the file.

        writefile(filename, content, append=False):
            Write the content to the specified file with sudo privileges.
            Args:
                filename (Union[str, Path]): The filename.
                content (str): The content to write.
                append (bool, optional): If True, append the content at the end;
                                          otherwise, overwrite the file.
            Returns:
                str: The output created by the write process.
    """

    @staticmethod
    def password(msg: str = "sudo password: "):
        """Prompt the user for the sudo password.

        Args:
            msg (str, optional): The message to display when prompting for the password.
        """
        # Use subprocess to avoid shell injection in the prompt message
        subprocess.run(["sudo", "-p", msg, "echo", "", ">", "/dev/null"], shell=True, stderr=subprocess.DEVNULL)

    @staticmethod
    def expire():
        """Expires the sudo password cache"""
        subprocess.run(["sudo", "-k"], stderr=subprocess.DEVNULL)

    @staticmethod
    def execute(command: Union[List[str], str], decode: bool = True, debug: bool = False, msg: Optional[str] = None) -> subprocess.CompletedProcess:
        """Execute the specified command with sudo.

        Args:
            command (Union[List[str], str]): The command to run.
            decode (bool, optional): If True, decode the output from bytes to UTF-8.
            debug (bool, optional): If True, print command execution details.
            msg (str, optional): Message to print before executing the command.

        Returns:
            subprocess.CompletedProcess: The result of the command execution.

        Raises:
            SudoError: If the command execution fails.
        """
        Sudo.password()
        
        if isinstance(command, str):
            # Simple split for string commands, though list is preferred
            sudo_command = ["sudo"] + command.split()
        else:
            sudo_command = ["sudo"] + command

        if msg:
            if msg == "command":
                logger.info(f"Executing: {' '.join(sudo_command)}")
            else:
                logger.info(f"Executing: {msg}")

        result = subprocess.run(sudo_command, capture_output=True)

        if decode:
            result.stdout = result.stdout.decode("utf-8", errors="replace")
            result.stderr = result.stderr.decode("utf-8", errors="replace")

        if debug:
            logger.debug(f"STDOUT:\n{result.stdout}")
            logger.debug(f"STDERR:\n{result.stderr}")
            logger.debug(f"Result: {result}")

        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error occurred during sudo execution"
            logger.error(f"Sudo command failed with return code {result.returncode}: {error_msg}")
            raise SudoError(f"Sudo command failed: {error_msg}")

        return result

    @staticmethod
    def _validate_path(filename: Union[str, Path]) -> str:
        """Basic validation to prevent null byte injection and ensure path is not empty.

        Args:
            filename (Union[str, Path]): The filename to validate.

        Returns:
            str: The validated filename as a string.

        Raises:
            SudoError: If the path is invalid.
        """
        path_str = str(filename)
        if not path_str:
            raise SudoError("Filename cannot be empty")
        if "\0" in path_str:
            raise SudoError("Filename contains null bytes, which is not allowed")
        return path_str

    @staticmethod
    def readfile(filename: Union[str, Path], split: bool = False, trim: bool = False, decode: bool = True) -> Union[str, List[str]]:
        """Read the content of the file with sudo privileges and return the result.

        Args:
            filename (Union[str, Path]): The filename.
            split (bool, optional): If True, return a list of lines.
            trim (bool, optional): If True, trim trailing whitespace.
            decode (bool, optional): If True, decode the output from bytes to UTF-8.

        Returns:
            Union[str, List[str]]: The content of the file.

        Raises:
            SudoError: If the file cannot be read.
        """
        Sudo.password()
        validated_path = Sudo._validate_path(filename)
        result = Sudo.execute(["cat", validated_path], decode=decode)

        content = result.stdout

        if trim:
            content = content.rstrip()

        if split:
            content = content.splitlines()

        return content

    @staticmethod
    def writefile(filename: Union[str, Path], content: str, append: bool = False) -> str:
        """Write the content to the specified file with sudo privileges.

        Args:
            filename (Union[str, Path]): The filename.
            content (str): The content to write.
            append (bool, optional): If True, append the content at the end; otherwise, overwrite the file.

        Returns:
            str: The output created by the write process.

        Raises:
            SudoError: If the write operation fails.
        """
        Sudo.password()
        validated_path = Sudo._validate_path(filename)
        
        if append:
            existing_content = Sudo.readfile(filename, split=False, decode=True)
            content = existing_content + content

        # Use a pipe to avoid shell injection via echo
        process = subprocess.Popen(["sudo", "tee", validated_path], 
                                    stdin=subprocess.PIPE, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
        stdout, stderr = process.communicate(input=content)
        
        if process.returncode != 0:
            logger.error(f"Failed to write to {validated_path}: {stderr}")
            raise SudoError(f"Sudo write failed: {stderr}")

        return content
