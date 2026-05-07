# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

from pathlib import Path
from typing import Optional
from cloudmesh.ai.common import logging as ai_log
from cloudmesh.ai.common.ssh.base import SSHBase

logger = ai_log.get_logger("common.ssh.encryption")

class SSHEncryption(SSHBase):
    """Utility to encrypt and decrypt files using RSA keys via OpenSSL."""

    def __init__(
        self, 
        file_in: str, 
        file_out: str, 
        key_path: str = "~/.ssh/id_rsa", 
        pem_path: str = "~/.ssh/id_rsa.pub.pem", 
        debug: bool = False
    ):
        super().__init__(debug=debug)
        self.file_in = self.resolve_path(file_in)
        self.file_out = self.resolve_path(file_out)
        self.key = self.resolve_path(key_path)
        self.pem = self.resolve_path(pem_path)

    def pem_create(self):
        """Create a PEM public key from the private key."""
        # openssl rsa -in <key> -pubout -out <pem>
        self._execute([
            "openssl", "rsa", 
            "-in", str(self.key), 
            "-pubout", 
            "-out", str(self.pem)
        ])

    def pem_cat(self):
        """Print the PEM public key to stdout."""
        result = self._execute(["cat", str(self.pem)])
        print(result.stdout)

    def encrypt(self):
        """Encrypt the input file using the public PEM key."""
        # Use pkeyutl (modern) instead of rsautl (deprecated)
        # openssl pkeyutl -encrypt -pubin -inkey <pem> -in <file> -out <secret>
        self._execute([
            "openssl", "pkeyutl", 
            "-encrypt", 
            "-pubin", 
            "-inkey", str(self.pem), 
            "-in", str(self.file_in), 
            "-out", str(self.file_out)
        ])

    def decrypt(self, filename: Optional[str] = None):
        """Decrypt the secret file using the private key."""
        secret_file = self.resolve_path(filename) if filename else self.file_out
        
        # openssl pkeyutl -decrypt -inkey <key> -in <secret>
        result = self._execute([
            "openssl", "pkeyutl", 
            "-decrypt", 
            "-inkey", str(self.key), 
            "-in", str(secret_file)
        ])
        print(result.stdout)


if __name__ == "__main__":
    # Simple test case
    test_file = Path("file.txt")
    secret_file = Path("secret.txt")
    
    try:
        test_file.unlink(missing_ok=True)
        secret_file.unlink(missing_ok=True)
        
        test_file.write_text("Big Data is here.")
        
        e = SSHEncryption(str(test_file), str(secret_file), debug=True)
        e.pem_create()
        e.encrypt()
        e.decrypt()
    except Exception as ex:
        logger.exception(f"Encryption test failed: {ex}")