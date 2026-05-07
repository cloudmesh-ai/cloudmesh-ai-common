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
from unittest.mock import patch
from cloudmesh.ai.common.io import Console, BaseIO
from cloudmesh.ai.common.exceptions import IOReadError, IOWriteError

@pytest.fixture
def console():
    return Console()

def test_path_expand_empty_string(console):
    """Test path_expand with empty string returns empty string."""
    assert console.expand_path("") == ""

def test_path_expand_home_directory(console):
    """Test path_expand expands tilde to home directory."""
    result = console.expand_path("~")
    expected = str(Path.home().as_posix())
    assert result == expected

def test_path_expand_relative_path(console):
    """Test path_expand converts relative path to absolute."""
    result = console.expand_path("./test_file.txt")
    assert os.path.isabs(result)
    assert result.endswith("test_file.txt")

@patch.dict(os.environ, {'HOME': '/home/user', 'PROJECT': '/home/user/project'})
def test_path_expand_environment_variables(console):
    """Test path_expand expands environment variables."""
    result = console.expand_path("$PROJECT/file.txt")
    assert "project" in result.lower()
    assert "file.txt" in result

def test_read_write_file(console, tmp_path):
    """Test reading and writing files using BaseIO logic."""
    test_file = tmp_path / "test.txt"
    content = "Hello Cloudmesh AI"
    
    console.writefile(str(test_file), content)
    assert test_file.read_text() == content
    
    assert console.readfile(str(test_file)) == content

def test_append_file(console, tmp_path):
    """Test appending to a file."""
    test_file = tmp_path / "append.txt"
    console.writefile(str(test_file), "Line 1\n")
    console.appendfile(str(test_file), "Line 2\n")
    
    assert test_file.read_text() == "Line 1\nLine 2\n"

def test_yaml_io(console, tmp_path):
    """Test YAML loading and dumping."""
    test_yaml = tmp_path / "test.yaml"
    data = {"key": "value", "nested": {"a": 1}}
    
    console.dump_yaml(str(test_yaml), data)
    loaded = console.load_yaml(str(test_yaml))
    
    assert loaded == data

def test_read_nonexistent_file(console):
    """Test that reading a nonexistent file raises IOReadError."""
    with pytest.raises(IOReadError):
        console.readfile("/tmp/nonexistent_file_12345.txt")

def test_write_forbidden_path(console):
    """Test that writing to a forbidden path raises IOWriteError."""
    # Attempt to write to a root-only directory
    with pytest.raises(IOWriteError):
        console.writefile("/root/forbidden.txt", "content")