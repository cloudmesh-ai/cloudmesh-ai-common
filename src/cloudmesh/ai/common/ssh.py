import os
import re
import yaml

class SSHConfig:
    """Helper class to parse and manage SSH configuration."""
    
    def __init__(self, config_path=None):
        """Initialize the SSHConfig object.

        Args:
            config_path: Path to the SSH config file. 
                Defaults to ~/.ssh/config.
        """
        if config_path is None:
            config_path = os.path.expanduser("~/.ssh/config")
        
        self.config_path = config_path
        self.hosts = {}
        self._parse_config()

    def _parse_config(self):
        """Parses the SSH config file into a dictionary.

        The method reads the config file and splits it into blocks based on the 
        'Host' keyword, then extracts key-value pairs for each host.
        """
        if not os.path.exists(self.config_path):
            return

        try:
            with open(self.config_path, "r") as f:
                content = f.read()

            # Split by 'Host ' at the start of a line
            blocks = re.split(r'^Host\s+', content, flags=re.MULTILINE)
            
            for block in blocks[1:]:
                lines = block.splitlines()
                if not lines:
                    continue
                
                # The first line contains the host pattern(s)
                host_patterns = lines[0].split()
                
                # Parse the rest of the block for key-value pairs
                host_info = {}
                for line in lines[1:]:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Split by first whitespace
                    parts = re.split(r'\s+', line, maxsplit=1)
                    if len(parts) == 2:
                        key = parts[0].lower()
                        value = parts[1]
                        host_info[key] = value
                
                for pattern in host_patterns:
                    # If pattern is '*', it's a global config
                    if pattern == '*':
                        if '*' not in self.hosts:
                            self.hosts['*'] = {}
                        self.hosts['*'].update(host_info)
                    else:
                        if pattern not in self.hosts:
                            self.hosts[pattern] = {}
                        self.hosts[pattern].update(host_info)
        except Exception as e:
            # In a real scenario, we might want to log this error
            pass

    def username(self, host):
        """Returns the username for the given host, falling back to global config or local user.

        Args:
            host: The host identifier to look up.

        Returns:
            The username associated with the host, the global user, 
            or the local system user.
        """
        # 1. Specific host match
        if host in self.hosts and 'user' in self.hosts[host]:
            return self.hosts[host]['user']
        
        # 2. Global match
        if '*' in self.hosts and 'user' in self.hosts['*']:
            return self.hosts['*']['user']
        
        # 3. Local system user
        return os.environ.get("USER", "user")

    def hostname(self, host):
        """Returns the actual HostName for the given host.

        Args:
            host: The host identifier to look up.

        Returns:
            The actual hostname or IP address associated with the host identifier.
        """
        if host in self.hosts and 'hostname' in self.hosts[host]:
            return self.hosts[host]['hostname']
        
        if '*' in self.hosts and 'hostname' in self.hosts['*']:
            return self.hosts['*']['hostname']
            
        return host

    def yaml(self):
        """Returns the parsed SSH configuration in YAML format.

        Returns:
            A YAML string representation of the parsed hosts dictionary.
        """
        return yaml.dump(self.hosts, default_flow_style=False)