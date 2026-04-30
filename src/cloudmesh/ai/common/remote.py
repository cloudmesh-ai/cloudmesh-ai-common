"""
Remote execution utilities for cloudmesh-ai.
Provides a unified interface for SSH command execution and file transfers.
"""

import paramiko
from typing import Optional, Tuple
from cloudmesh.ai.common.io import console

class RemoteExecutor:
    """
    A unified executor for remote operations via SSH.
    Supports command execution, file uploads, and direct remote file writing.
    """

    def __init__(self, host: str, username: Optional[str] = None, key_filename: Optional[str] = None):
        """Initialize the RemoteExecutor.

        Args:
            host: The hostname or IP address of the remote host.
            username: The SSH username. Defaults to None.
            key_filename: Path to the private key file. Defaults to None.
        """
        self.host = host
        self.username = username
        self.key_filename = key_filename
        self.client: Optional[paramiko.SSHClient] = None

    def __enter__(self):
        """Establishes the SSH connection.

        Returns:
            The RemoteExecutor instance.

        Raises:
            paramiko.SSHException: If the connection fails.
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(
                hostname=self.host, 
                username=self.username, 
                key_filename=self.key_filename
            )
            return self
        except Exception as e:
            console.error(f"Failed to connect to {self.host}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the SSH connection.

        Args:
            exc_type: The type of the exception that occurred.
            exc_val: The instance of the exception that occurred.
            exc_tb: The traceback of the exception that occurred.
        """
        if self.client:
            self.client.close()

    def execute(self, command: str, timeout: int = 60) -> Tuple[int, str, str]:
        """
        Executes a command on the remote host.
        
        Args:
            command: The shell command to execute.
            timeout: Command timeout in seconds.
            
        Returns:
            A tuple of (exit_status, stdout, stderr).
        """
        if not self.client:
            raise RuntimeError("RemoteExecutor must be used as a context manager.")

        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            return exit_status, stdout.read().decode('utf-8'), stderr.read().decode('utf-8')
        except Exception as e:
            console.error(f"Execution failed on {self.host}: {e}")
            raise

    def upload(self, local_path: str, remote_path: str):
        """Uploads a local file to the remote host using SFTP.

        Args:
            local_path: Path to the local file to upload.
            remote_path: Path on the remote host where the file should be saved.

        Raises:
            RuntimeError: If the executor is not used as a context manager.
            IOError: If the upload fails.
        """
        if not self.client:
            raise RuntimeError("RemoteExecutor must be used as a context manager.")

        try:
            sftp = self.client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
        except Exception as e:
            console.error(f"Upload failed to {self.host}:{remote_path}: {e}")
            raise

    def download(self, remote_path: str, local_path: str):
        """Downloads a remote file to the local host using SFTP.

        Args:
            remote_path: Path to the file on the remote host.
            local_path: Path on the local host where the file should be saved.

        Raises:
            RuntimeError: If the executor is not used as a context manager.
            IOError: If the download fails.
        """
        if not self.client:
            raise RuntimeError("RemoteExecutor must be used as a context manager.")

        try:
            sftp = self.client.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
        except Exception as e:
            console.error(f"Download failed from {self.host}:{remote_path}: {e}")
            raise

    def write_remote_file(self, content: str, remote_path: str):
        """Writes a string directly to a remote file.

        Useful for creating scripts or config files on the fly.

        Args:
            content: The string content to write.
            remote_path: Path on the remote host where the file should be created.

        Raises:
            RuntimeError: If the executor is not used as a context manager.
            IOError: If the write operation fails.
        """
        if not self.client:
            raise RuntimeError("RemoteExecutor must be used as a context manager.")

        try:
            sftp = self.client.open_sftp()
            with sftp.file(remote_path, 'w') as f:
                f.write(content)
            sftp.close()
        except Exception as e:
            console.error(f"Failed to write remote file {self.host}:{remote_path}: {e}")
            raise