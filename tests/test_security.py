# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
from cloudmesh.ai.common.security import BaseSecurity
from cloudmesh.ai.common.exceptions import SecurityError, SecurityAuthError

@pytest.fixture
def security():
    return BaseSecurity(debug=True)

def test_is_root(security):
    """Test is_root returns correct boolean."""
    with patch('os.geteuid', return_value=0):
        assert security.is_root() is True
    with patch('os.geteuid', return_value=1000):
        assert security.is_root() is False

def test_verify_file_permissions(security, tmp_path):
    """Test file permission verification."""
    test_file = tmp_path / "perm_test.txt"
    test_file.write_text("content")
    
    # Test readable
    assert security.verify_file_permissions(test_file, readable=True) is True
    
    # Test nonexistent
    assert security.verify_file_permissions("nonexistent_file_123", readable=True) is False

def test_secure_write(security, tmp_path):
    """Test writing files with restricted permissions."""
    test_file = tmp_path / "secure.txt"
    content = "secret data"
    
    security.secure_write(test_file, content)
    
    assert test_file.read_text() == content
    # Check permissions (should be 0o600)
    mode = os.stat(test_file).st_mode & 0o777
    assert mode == 0o600

def test_sudo_execute_local_success(security):
    """Test successful local sudo execution."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout="success", stderr="", returncode=0)
        
        result = security.sudo_execute_local("ls /root")
        assert result == "success"
        mock_run.assert_called_once()
        assert "sudo" in mock_run.call_args[0][0]

def test_sudo_execute_local_auth_failure(security):
    """Test sudo authentication failure raises SecurityAuthError."""
    with patch('subprocess.run') as mock_run:
        # Simulate sudo password failure
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, 
            cmd="sudo", 
            stderr="sudo: a password is required"
        )
        
        with pytest.raises(SecurityAuthError):
            security.sudo_execute_local("ls /root")

def test_sudo_execute_local_general_failure(security):
    """Test general sudo failure raises SecurityError."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, 
            cmd="sudo", 
            stderr="command not found"
        )
        
        with pytest.raises(SecurityError):
            security.sudo_execute_local("invalid_cmd")