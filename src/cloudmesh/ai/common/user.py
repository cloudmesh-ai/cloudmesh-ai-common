"""
Utility module for retrieving user-related system information and permissions.

This module provides cross-platform support for checking root/admin status, 
identifying the current user, and verifying user existence on the system.
"""

import os
import getpass
from pathlib import Path

def is_root():
    """Checks if the current process has administrative or root privileges.

    On Unix-like systems (Linux, macOS), it checks if the Effective User ID is 0.
    On Windows, it utilizes shell32 to check for administrative elevation.

    Returns:
        True if the process is running with root/admin rights, False otherwise.
    """
    try:
        # Unix/Linux/macOS
        return os.geteuid() == 0
    except AttributeError:
        # Windows
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0

def get():
    """Retrieves the login name of the current user.

    This function looks at environment variables (LOGNAME, USER, LNAME, USERNAME) 
    to provide a reliable username across different platforms.

    Returns:
        The username of the current user.
    """
    return getpass.getuser()

def home():
    """Retrieves the path to the current user's home directory.

    Returns:
        A Path object representing the user's home directory 
        (e.g., /home/user or C:\\Users\\user).
    """
    return Path.home()

def groups():
    """Retrieves a list of group names that the current user belongs to.

    Note:
        This function is currently only fully supported on Unix-like systems.
        On Windows, this will return an empty list.

    Returns:
        A list of strings representing the group names.
    """
    if os.name == 'nt':  # Windows
        return []  # Windows handles groups differently (via SIDs)
    import grp
    return [grp.getgrgid(g).gr_name for g in os.getgroups()]

def exists(username):
    """Verifies if a specific user exists on the local system.

    Args:
        username (str): The login name of the user to verify.

    Returns:
        True if the user exists, False otherwise.
    """
    if os.name == 'nt':
        # Simple Windows check using the 'net user' command
        import subprocess
        return subprocess.run(
            ["net", "user", username], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        ).returncode == 0
    else:
        import pwd
        try:
            pwd.getpwnam(username)
            return True
        except KeyError:
            return False