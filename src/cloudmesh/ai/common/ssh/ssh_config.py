# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import json
import subprocess
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, Union

from cloudmesh.ai.common import logging as ai_log

logger = ai_log.get_logger("common.ssh.ssh_config")

class SSHConfig:
    """Managing the SSH config file (usually ~/.ssh/config)."""

    def __init__(self, filename: Optional[Union[str, Path]] = None):
        if filename is not None:
            self.filename = Path(filename).expanduser().resolve()
        else:
            self.filename = Path("~/.ssh/config").expanduser().resolve()
        
        self.hosts: Dict[str, Dict[str, str]] = {}
        self.load()

    def names(self) -> List[str]:
        """The names defined in the SSH config.

        Returns:
            List[str]: the host names.
        """
        return self.list()

    def load(self):
        """Parse the SSH config file and load hosts and their attributes."""
        if not self.filename.exists():
            self.hosts = {}
            return

        try:
            with self.filename.open('r') as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"Could not read ssh config file {self.filename}: {e}")
            self.hosts = {}
            return

        hosts = {}
        current_host = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # SSH config lines are usually 'Attribute Value'
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue

            attribute = parts[0].lower()
            value = parts[1].strip()

            if attribute == "host":
                current_host = value
                if current_host not in hosts:
                    hosts[current_host] = {"host": current_host}
            elif current_host:
                hosts[current_host][attribute] = value

        self.hosts = hosts

    def list(self) -> List[str]:
        """List the hosts defined in the config file.

        Returns:
            List[str]: list of host names.
        """
        return list(self.hosts.keys())

    def __str__(self) -> str:
        """The string representation of the config as JSON."""
        return json.dumps(self.hosts, indent=4)

    def login(self, name: str):
        """Login to the host defined in .ssh/config by name.

        Args:
            name: the name of the host as defined in the config file.
        """
        logger.info(f"Logging into host: {name}")
        try:
            # Use subprocess.run to avoid shell injection
            subprocess.run(["ssh", name], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to login to {name}: {e}")

    def execute(self, name: str, command: str) -> str:
        """Execute the command on the named host.

        Args:
            name: the name of the host in config.
            command: the command to be executed.

        Returns:
            str: the output of the command.
        """
        if name == "localhost":
            # Execute locally
            result = subprocess.run(["sh", "-c", command], capture_output=True, text=True)
        else:
            # Execute via SSH
            result = subprocess.run(["ssh", name, command], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Command execution failed on {name}: {result.stderr}")
        
        return result.stdout if result.stdout else result.stderr

    def local(self, command: str) -> str:
        """Execute the command on the localhost.

        Args:
            command: the command to execute.

        Returns:
            str: the output of the command.
        """
        return self.execute("localhost", command)

    def username(self, host: str) -> Optional[str]:
        """Returns the username for a given host in the config file.

        Args:
            host: the hostname.

        Returns:
            Optional[str]: the username or None if not found.
        """
        if host in self.hosts:
            return self.hosts[host].get("user")
        return None

    @staticmethod
    def delete(name: str):
        """Removes a host entry from the SSH config file.

        Args:
            name: the name of the host to remove.
        """
        filename = Path("~/.ssh/config").expanduser().resolve()
        if not filename.exists():
            return

        try:
            with filename.open('r') as f:
                lines = f.readlines()

            result = []
            remove = False
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(f"Host {name}"):
                    remove = True
                elif stripped.startswith("Host "):
                    remove = False
                
                if not remove:
                    result.append(line)

            with filename.open('w') as f:
                f.writelines(result)
        except Exception as e:
            logger.error(f"Failed to delete host {name} from {filename}: {e}")

    def generate(
        self,
        host: str = "india",
        hostname: str = "india.futuresystems.org",
        identity: str = "~/.ssh/id_rsa.pub",
        user: Optional[str] = None,
        verbose: bool = False,
    ):
        """Adds a host to the config file with given parameters.

        Args:
            host: the alias for the host.
            hostname: the actual hostname or IP.
            identity: the path to the identity file.
            user: the username for the host.
            verbose: prints debug messages.
        """
        if verbose and host in self.names():
            logger.warning(f"{host} already in {self.filename}")
            return

        entry = dedent(
            f"""
            Host {host}
                Hostname {hostname}
                User {user if user else ''}
                IdentityFile {identity}
            """
        ).strip() + "\n"

        try:
            with self.filename.open("a") as config_ssh:
                config_ssh.write(entry)
            self.load()
            if verbose:
                logger.info(f"Added {host} to {self.filename}")
        except Exception as e:
            logger.error(f"Failed to generate ssh config for {host}: {e}")


if __name__ == "__main__":
    import sys
    # Simple test
    cfg = SSHConfig()
    print(f"Config file: {cfg.filename}")
    hosts.generate(host="india", user=user)
    print(hosts.filename)

    print(hosts.list())
    print(hosts)

    import sys

    sys.exit()

    r = hosts.execute("india", "hostname")
    print(r)

    r = hosts.execute("localhost", "hostname")
    print(r)

    r = hosts.local("hostname")
    print(r)

    # hosts.login("india")
