"""Unit tests for cloudmesh.ai.common.user module."""

import os
import sys
import pytest
from unittest.mock import patch
from pathlib import Path
from cloudmesh.ai.common import user


@patch('os.geteuid', return_value=0)
def test_is_root_unix_true(mock_geteuid):
    """Test is_root returns True on Unix with UID 0."""
    assert user.is_root() is True


@patch('os.geteuid', return_value=1000)
def test_is_root_unix_false(mock_geteuid):
    """Test is_root returns False on Unix with non-zero UID."""
    assert user.is_root() is False


@patch('getpass.getuser', return_value='testuser')
def test_get_user(mock_getuser):
    """Test get function returns current username."""
    assert user.get() == 'testuser'


def test_home_returns_path():
    """Test home function returns a Path object."""
    result = user.home()
    assert isinstance(result, Path)
    assert result.exists()


@pytest.mark.skipif(sys.platform == 'win32', reason="POSIX-only test")
def test_groups_unix():
    """Test groups returns list on Unix."""
    assert isinstance(user.groups(), list)


@pytest.mark.skipif(sys.platform != 'win32', reason="Windows-only test")
def test_groups_windows():
    """Test groups returns empty list on Windows."""
    assert user.groups() == []


@pytest.mark.skipif(sys.platform == 'win32', reason="POSIX-only test")
def test_exists_unix_valid_user():
    """Test exists returns True for current user on Unix."""
    current_user = user.get()
    assert user.exists(current_user) is True


@pytest.mark.skipif(sys.platform == 'win32', reason="POSIX-only test")
def test_exists_unix_invalid_user():
    """Test exists returns False for non-existing Unix user."""
    assert user.exists('thisuserdoesnotexist_12345') is False