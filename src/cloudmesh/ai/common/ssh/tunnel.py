import subprocess
import os
import signal
from cloudmesh.ai.common.io import console

class Tunnel:
    """Manages an SSH tunnel for port forwarding."""

    def __init__(self, local_port: int, remote_host: str, remote_port: int, ssh_host: str):
        self.local_port = local_port
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.ssh_host = ssh_host
        self.process = None

    def start(self):
        """Starts the SSH tunnel in the background."""
        if self.process and self.process.poll() is None:
            console.warn(f"Tunnel for port {self.local_port} is already running.")
            return True

        try:
            # -L local_port:remote_host:remote_port ssh_host -N
            # -N tells SSH not to execute a remote command, which is used for just forwarding ports.
            cmd = [
                "ssh",
                "-L",
                f"{self.local_port}:{self.remote_host}:{self.remote_port}",
                self.ssh_host,
                "-N",
            ]
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, 
                preexec_fn=os.setpgrp # Create a new process group to make killing easier
            )
            console.ok(f"SSH tunnel established: localhost:{self.local_port} -> {self.remote_host}:{self.remote_port} via {self.ssh_host}")
            return True
        except Exception as e:
            console.error(f"Failed to start SSH tunnel: {e}")
            return False

    def stop(self):
        """Stops the SSH tunnel process."""
        if not self.process or self.process.poll() is not None:
            console.warn(f"No active tunnel found for port {self.local_port}.")
            return False

        try:
            # Kill the process group
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.process = None
            console.ok(f"SSH tunnel on port {self.local_port} stopped.")
            return True
        except Exception as e:
            console.error(f"Failed to stop SSH tunnel: {e}")
            return False

    def is_active(self) -> bool:
        """Checks if the tunnel process is still running."""
        return self.process is not None and self.process.poll() is None