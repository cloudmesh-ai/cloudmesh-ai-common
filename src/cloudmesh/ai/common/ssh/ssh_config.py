# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import json
import os
import yaml
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, Union

from cloudmesh.ai.common import logging as ai_log
from cloudmesh.ai.common.ssh.base import SSHBase, CommandResult
from sshconf import SshConfig as SshConf

logger = ai_log.get_logger("common.ssh.ssh_config")

class SSHConfig(SSHBase):
    """Managing the SSH config file (usually ~/.ssh/config)."""

    def __init__(self, filename: Optional[Union[str, Path]] = None, debug: bool = False):
        super().__init__(debug=debug)
        if filename is not None:
            self.filename = self.resolve_path(str(filename))
        else:
            self.filename = self.resolve_path("~/.ssh/config")
        
        self.conf: Optional[SshConf] = None
        self.load()

    def names(self) -> List[str]:
        """The names defined in the SSH config.

        Returns:
            List[str]: the host names.
        """
        return self.list()

    def load(self):
        """Parse the SSH config file using sshconf."""
        try:
            self.conf = SshConf(str(self.filename))
        except Exception as e:
            logger.error(f"Could not load ssh config file {self.filename}: {e}")
            self.conf = None

    def list(self) -> List[str]:
        """List the hosts defined in the config file.

        Returns:
            List[str]: list of host names.
        """
        if not self.conf:
            return []
        return self.conf.hosts()

    def __str__(self) -> str:
        """The string representation of the config as JSON."""
        if not self.conf:
            return "{}"
        
        # Convert sshconf to a dictionary for JSON representation
        hosts_dict = {}
        for host in self.conf.hosts():
            hosts_dict[host] = self.conf.get_all(host)
        return json.dumps(hosts_dict, indent=4)

    def login(self, name: str):
        """Login to the host defined in .ssh/config by name.

        Args:
            name: the name of the host as defined in the config file.
        """
        logger.info(f"Logging into host: {name}")
        try:
            self._execute(["ssh", name], capture_output=False)
        except Exception as e:
            logger.error(f"Failed to login to {name}: {e}")

    def execute(self, name: str, command: str, use_pty: bool = False) -> Union[CommandResult, str]:
        """Execute the command on the named host.

        Args:
            name: the name of the host in config.
            command: the command to be executed.
            use_pty: whether to allocate a pseudo-terminal.

        Returns:
            Union[CommandResult, str]: CommandResult for remote, stdout for local.
        """
        if name == "localhost":
            # Execute locally
            result = self._execute(["sh", "-c", command])
            return result.stdout if result.stdout else result.stderr
        
        # Execute via Fabric
        user = self.username(name)
        return self._run_remote(name, command, user=user, use_pty=use_pty)

    def sudo_execute(self, name: str, command: str, use_pty: bool = False) -> CommandResult:
        """Execute the command on the named host with sudo.

        Args:
            name: the name of the host in config.
            command: the command to be executed.
            use_pty: whether to allocate a pseudo-terminal.

        Returns:
            CommandResult: structured result of the execution.
        """
        user = self.username(name)
        return self._run_remote(name, command, user=user, use_sudo=True, use_pty=use_pty)

    def execute_parallel(self, hosts: List[str], command: str) -> Dict[str, CommandResult]:
        """Execute the same command on multiple hosts in parallel.

        Args:
            hosts: list of host names.
            command: the command to execute.

        Returns:
            Dict[str, CommandResult]: mapping of host to its result.
        """
        from concurrent.futures import ThreadPoolExecutor
        
        results = {}
        with ThreadPoolExecutor() as executor:
            future_to_host = {executor.submit(self.execute, host, command): host for host in hosts}
            for future in future_to_host:
                host = future_to_host[future]
                try:
                    results[host] = future.result()
                except Exception as e:
                    logger.error(f"Parallel execution failed for {host}: {e}")
        
        return results

    def local(self, command: str) -> str:
        """Execute the command on the localhost.

        Args:
            command: the command to execute.

        Returns:
            str: the output of the command.
        """
        return self.execute("localhost", command)

    def username(self, host: str) -> Optional[str]:
        """Returns the username for a given host, falling back to global config or local user.

        Args:
            host: the hostname.

        Returns:
            Optional[str]: the username associated with the host, the global user, 
            or the local system user.
        """
        if not self.conf:
            return os.environ.get("USER", "user")

        # sshconf handles the hierarchy (specific -> global) automatically
        user = self.conf.get(host, 'user')
        if user:
            return user
        
        return os.environ.get("USER", "user")

    def hostname(self, host: str) -> str:
        """Returns the actual HostName for the given host.

        Args:
            host: the host identifier to look up.

        Returns:
            The actual hostname or IP address associated with the host identifier.
        """
        if not self.conf:
            return host

        hostname = self.conf.get(host, 'hostname')
        return hostname if hostname else host

    def yaml(self) -> str:
        """Returns the parsed SSH configuration in YAML format.

        Returns:
            A YAML string representation of the parsed hosts dictionary.
        """
        if not self.conf:
            return "{}"
        
        hosts_dict = {}
        for host in self.conf.hosts():
            hosts_dict[host] = self.conf.get_all(host)
        return yaml.dump(hosts_dict, default_flow_style=False)

    def delete(self, name: str):
        """Removes a host entry from the SSH config file.

        Args:
            name: the name of the host to remove.
        """
        if not self.conf:
            return

        try:
            self.conf.remove(name)
            self.conf.save()
        except Exception as e:
            logger.error(f"Failed to delete host {name} from {self.filename}: {e}")

    def generate(
        self,
        host: str = "uva",
        hostname: str = "login.hpc.virginia.edu",
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
        if not self.conf:
            return

        if verbose and host in self.names():
            logger.warning(f"{host} already in {self.filename}")
            return

        try:
            self.conf.add(host, {
                "hostname": hostname,
                "user": user if user else "",
                "identityfile": identity
            })
            self.conf.save()
            if verbose:
                logger.info(f"Added {host} to {self.filename}")
        except Exception as e:
            logger.error(f"Failed to generate ssh config for {host}: {e}")


if __name__ == "__main__":
    import sys
    # Simple test
    cfg = SSHConfig()
    print(f"Config file: {cfg.filename}")
    cfg.generate(host="uva", user="user")
    print(cfg.filename)

    print(cfg.list())
    print(cfg)

    sys.exit()

    r = cfg.execute("uva", "hostname")
    print(r)

    r = cfg.execute("localhost", "hostname")
    print(r)

    r = cfg.local("hostname")
    print(r)

    # cfg.login("uva")
