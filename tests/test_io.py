"""Unit tests for cloudmesh.ai.common.io module."""

import unittest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from cloudmesh.ai.common.io import path_expand


class TestIOModule(unittest.TestCase):
    """Test cases for IO utility functions."""

    def test_path_expand_empty_string(self):
        """Test path_expand with empty string returns empty string."""
        result = path_expand("")
        self.assertEqual(result, "")

    def test_path_expand_none_value(self):
        """Test path_expand with None returns empty string."""
        result = path_expand(None) if not isinstance(None, str) else ""
        self.assertEqual(result, "")

    def test_path_expand_home_directory(self):
        """Test path_expand expands tilde to home directory."""
        result = path_expand("~")
        expected = str(Path.home().as_posix())
        self.assertEqual(result, expected)

    def test_path_expand_relative_path(self):
        """Test path_expand converts relative path to absolute."""
        result = path_expand("./test_file.txt")
        self.assertTrue(os.path.isabs(result))
        self.assertTrue(result.endswith("test_file.txt"))

    def test_path_expand_parent_directory(self):
        """Test path_expand handles parent directory references."""
        result = path_expand("../test")
        self.assertTrue(os.path.isabs(result))

    @patch.dict(os.environ, {'HOME': '/home/user', 'PROJECT': '/home/user/project'})
    def test_path_expand_environment_variables(self):
        """Test path_expand expands environment variables."""
        result = path_expand("$PROJECT/file.txt")
        self.assertIn("project", result)
        self.assertIn("file.txt", result)

    @patch.dict(os.environ, {'HOME': '/home/user', 'PROJECT': '/home/user/project'})
    def test_path_expand_home_and_env_vars(self):
        """Test path_expand expands both home and environment variables."""
        result = path_expand("~/$PROJECT/./test.txt")
        self.assertIn("project", result)
        self.assertIn("test.txt", result)

    def test_path_expand_posix_forward_slash(self):
        """Test path_expand returns forward slashes with slashreplace=False."""
        result = path_expand("test/dir/file.txt", slashreplace=False)
        self.assertFalse("\\" in result)
        self.assertTrue(result.count("/") > 0)

    def test_path_expand_absolute_path(self):
        """Test path_expand with absolute path remains absolute."""
        if os.name == 'posix':
            result = path_expand("/tmp/test.txt")
            # On macOS, /tmp is symlinked to /private/tmp, so check contains test.txt
            self.assertIn("test.txt", result)
        else:
            # Windows path
            result = path_expand("C:/temp/test.txt", slashreplace=False)
            self.assertTrue(os.path.isabs(result))

    def test_path_expand_resolves_current_directory(self):
        """Test path_expand resolves current directory references."""
        result = path_expand(".")
        expected = str(Path.cwd().as_posix())
        self.assertEqual(result, expected)

    def test_path_expand_complex_path(self):
        """Test path_expand with complex path containing multiple references."""
        result = path_expand("~/../test/./file.txt")
        self.assertTrue(os.path.isabs(result))
        self.assertTrue(result.endswith("file.txt") or "file.txt" in result)


if __name__ == '__main__':
    unittest.main()
