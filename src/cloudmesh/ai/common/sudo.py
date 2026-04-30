"""
Sudo utility for cloudmesh-ai.
Provides a way to prompt for and validate sudo passwords.
"""

import subprocess
import getpass
from cloudmesh.ai.common.io import console

class Sudo:
    """Sudo utility to handle system password prompts."""

    @staticmethod
    def password() -> bool:
        """Prompts the user for a sudo password and validates it using 'sudo -v -S'.

        This caches the password for subsequent sudo commands.

        Returns:
            True if the password was validated successfully, False otherwise.
        """
        try:
            # Prompt the user for the password with the requested custom prompt
            password = getpass.getpass("Sudo Password: ")
            
            # Use sudo -v -S to validate the password and cache it
            # -v: update the user's cached credentials
            # -S: read password from standard input
            process = subprocess.run(
                ["sudo", "-v", "-S"],
                input=password,
                capture_output=True,
                text=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            console.error(f"Sudo validation failed: {e.stderr.strip()}")
            return False
        except Exception as e:
            console.error(f"An unexpected error occurred during sudo validation: {str(e)}")
            return False