# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import io
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Union

from cloudmesh.ai.common import logging as ai_log

logger = ai_log.get_logger("common.ssh.authorized_keys")

def get_fingerprint_from_public_key(pubkey: str) -> str:
    """Generate the fingerprint of a public key.

    Args:
        pubkey (str): the value of the public key

    Returns:
        str: fingerprint
    """
    try:
        # Use ssh-keygen -l -f /dev/stdin to avoid creating temporary files
        process = subprocess.run(
            ["ssh-keygen", "-l", "-f", "/dev/stdin"],
            input=pubkey,
            capture_output=True,
            text=True,
            check=True
        )
        output = process.stdout.strip()
        # Output format: "2048 SHA256:abc... user@host (RSA)"
        parts = output.split(' ')
        if len(parts) >= 2:
            return parts[1]
        return output
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.error(f"Failed to get fingerprint for public key: {e}")
        return ""


class AuthorizedKeys:
    """Class to manage authorized keys."""

    def __init__(self):
        self._order: Dict[int, str] = {}
        self._keys: Dict[str, str] = {}

    @classmethod
    def load(cls, path: Union[str, Path]) -> 'AuthorizedKeys':
        """Load the keys from a path.

        Args:
            path: the filename (path) in which we find the keys

        Returns:
            AuthorizedKeys: An instance containing the loaded keys.
        """
        auth = cls()
        path = Path(path)
        if not path.exists():
            logger.warning(f"Authorized keys file not found: {path}")
            return auth

        try:
            with path.open('r') as fd:
                for pubkey in map(str.strip, fd):
                    # skip empty lines and comments
                    if not pubkey or pubkey.startswith('#'):
                        continue
                    auth.add(pubkey)
        except Exception as e:
            logger.error(f"Error loading authorized keys from {path}: {e}")
            
        return auth

    def add(self, pubkey: str):
        """Add a public key.

        Args:
            pubkey: the public key string.
        """
        fingerprint = get_fingerprint_from_public_key(pubkey)
        if not fingerprint:
            logger.warning("Could not generate fingerprint for public key; skipping.")
            return

        if fingerprint not in self._keys:
            self._order[len(self._keys)] = fingerprint
            self._keys[fingerprint] = pubkey

    def remove(self, fingerprint: str):
        """Removes the public key by its fingerprint.

        Args:
            fingerprint: the fingerprint of the public key to remove.
        """
        if fingerprint in self._keys:
            del self._keys[fingerprint]
            # Rebuild order to keep it contiguous
            new_order = {}
            for i, f in enumerate(self._order.values()):
                if f != fingerprint:
                    new_order[i] = f
            self._order = new_order
        else:
            logger.warning(f"Fingerprint {fingerprint} not found in authorized keys.")

    def __str__(self) -> str:
        with io.StringIO() as sio:
            for fingerprint in self._order.values():
                key = self._keys.get(fingerprint)
                if key:
                    sio.write(key)
                    sio.write('\n')
            return sio.getvalue().strip()

    def __repr__(self) -> str:
        return f"AuthorizedKeys(keys={len(self._keys)})"


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python authorized_keys.py <path_to_authorized_keys>")
        sys.exit(1)

    path = sys.argv[1]
    auth = AuthorizedKeys.load(path)
    print(auth)