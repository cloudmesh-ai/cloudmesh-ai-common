"""Unit tests for cloudmesh.ai.common.remote module."""

import pytest
from unittest.mock import MagicMock, patch
from cloudmesh.ai.common.remote import RemoteExecutor

@pytest.fixture
def mock_paramiko():
    """Fixture to mock paramiko SSHClient and SFTPClient."""
    with patch("paramiko.SSHClient") as mock_ssh:
        mock_client = MagicMock()
        mock_ssh.return_value = mock_client
        
        # Mock SFTP client
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp
        
        yield {
            "ssh": mock_ssh,
            "client": mock_client,
            "sftp": mock_sftp
        }

def test_remote_executor_connection(mock_paramiko):
    """Test that RemoteExecutor establishes and closes connection."""
    host = "test-host"
    with RemoteExecutor(host) as executor:
        assert executor.client is not None
        mock_paramiko["ssh"].return_value.connect.assert_called_with(
            hostname=host, username=None, key_filename=None
        )
    
    mock_paramiko["client"].close.assert_called_once()

def test_remote_executor_execute_success(mock_paramiko):
    """Test successful command execution."""
    # Mock the channel and stdout for execute
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b"success output"
    mock_stdout.channel.recv_exit_status.return_value = 0
    
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b""
    
    mock_paramiko["client"].exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    with RemoteExecutor("host") as executor:
        status, stdout, stderr = executor.execute("ls -l")
        
    assert status == 0
    assert stdout == "success output"
    assert stderr == ""
    mock_paramiko["client"].exec_command.assert_called_with("ls -l", timeout=60)

def test_remote_executor_execute_failure(mock_paramiko):
    """Test command execution with non-zero exit status."""
    mock_stdout = MagicMock()
    mock_stdout.read.return_value = b""
    mock_stdout.channel.recv_exit_status.return_value = 1
    
    mock_stderr = MagicMock()
    mock_stderr.read.return_value = b"error message"
    
    mock_paramiko["client"].exec_command.return_value = (None, mock_stdout, mock_stderr)
    
    with RemoteExecutor("host") as executor:
        status, stdout, stderr = executor.execute("false")
        
    assert status == 1
    assert stdout == ""
    assert stderr == "error message"

def test_remote_executor_upload(mock_paramiko):
    """Test file upload via SFTP."""
    with RemoteExecutor("host") as executor:
        executor.upload("local.txt", "remote.txt")
        
    mock_paramiko["sftp"].put.assert_called_with("local.txt", "remote.txt")
    mock_paramiko["client"].open_sftp.assert_called_once()

def test_remote_executor_download(mock_paramiko):
    """Test file download via SFTP."""
    with RemoteExecutor("host") as executor:
        executor.download("remote.txt", "local.txt")
        
    mock_paramiko["sftp"].get.assert_called_with("remote.txt", "local.txt")
    mock_paramiko["client"].open_sftp.assert_called_once()

def test_remote_executor_write_remote_file(mock_paramiko):
    """Test writing content directly to a remote file."""
    mock_file = MagicMock()
    mock_paramiko["sftp"].file.return_value.__enter__.return_value = mock_file
    
    content = "hello world"
    path = "/tmp/test.txt"
    
    with RemoteExecutor("host") as executor:
        executor.write_remote_file(content, path)
        
    mock_paramiko["sftp"].file.assert_called_with(path, 'w')
    mock_file.write.assert_called_with(content)

def test_remote_executor_no_context_manager():
    """Test that calling methods without context manager raises RuntimeError."""
    executor = RemoteExecutor("host")
    with pytest.raises(RuntimeError, match="RemoteExecutor must be used as a context manager"):
        executor.execute("ls")