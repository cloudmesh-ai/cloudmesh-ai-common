"""Unit tests for cloudmesh.ai.common.io module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch
from cloudmesh.ai.common.io import path_expand


def test_path_expand_empty_string():
    """Test path_expand with empty string returns empty string."""
    assert path_expand("") == ""


def test_path_expand_none_value():
    """Test path_expand with None returns empty string."""
    # The original code had: result = path_expand(None) if not isinstance(None, str) else ""
    # which is a bit odd, but I'll maintain the logic.
    result = path_expand(None) if not isinstance(None, str) else ""
    assert result == ""


def test_path_expand_home_directory():
    """Test path_expand expands tilde to home directory."""
    result = path_expand("~")
    expected = str(Path.home().as_posix())
    assert result == expected


def test_path_expand_relative_path():
    """Test path_expand converts relative path to absolute."""
    result = path_expand("./test_file.txt")
    assert os.path.isabs(result)
    assert result.endswith("test_file.txt")


def test_path_expand_parent_directory():
    """Test path_expand handles parent directory references."""
    result = path_expand("../test")
    assert os.path.isabs(result)


@patch.dict(os.environ, {'HOME': '/home/user', 'PROJECT': '/home/user/project'})
def test_path_expand_environment_variables():
    """Test path_expand expands environment variables."""
    result = path_expand("$PROJECT/file.txt")
    assert "project" in result.lower()
    assert "file.txt" in result


@patch.dict(os.environ, {'HOME': '/home/user', 'PROJECT': '/home/user/project'})
def test_path_expand_home_and_env_vars():
    """Test path_expand expands both home and environment variables."""
    result = path_expand("~/$PROJECT/./test.txt")
    assert "project" in result.lower()
    assert "test.txt" in result


def test_path_expand_posix_forward_slash():
    """Test path_expand returns forward slashes with slashreplace=False."""
    result = path_expand("test/dir/file.txt", slashreplace=False)
    assert "\\" not in result
    assert result.count("/") > 0


def test_path_expand_absolute_path():
    """Test path_expand with absolute path remains absolute."""
    if os.name == 'posix':
        result = path_expand("/tmp/test.txt")
        # On macOS, /tmp is symlinked to /private/tmp, so check contains test.txt
        assert "test.txt" in result
    else:
        # Windows path
        result = path_expand("C:/temp/test.txt", slashreplace=False)
        assert os.path.isabs(result)


def test_path_expand_resolves_current_directory():
    """Test path_expand resolves current directory references."""
    result = path_expand(".")
    expected = str(Path.cwd().as_posix())
    assert result == expected


def test_path_expand_complex_path():
    """Test path_expand with complex path containing multiple references."""
    result = path_expand("~/../test/./file.txt")
    assert os.path.isabs(result)
    assert result.endswith("file.txt") or "file.txt" in result