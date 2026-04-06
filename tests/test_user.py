"""Unit tests for cloudmesh.ai.common.user module."""

import unittest
import os
import sys
import pwd
from unittest.mock import patch, MagicMock
from pathlib import Path
from cloudmesh.ai.common import user


class TestUserModule(unittest.TestCase):
    """Test cases for user utility functions."""

    @patch('os.geteuid', return_value=0)
    def test_is_root_unix_true(self, mock_geteuid):
        """Test is_root returns True on Unix with UID 0."""
        result = user.is_root()
        self.assertTrue(result)

    @patch('os.geteuid', return_value=1000)
    def test_is_root_unix_false(self, mock_geteuid):
        """Test is_root returns False on Unix with non-zero UID."""
        result = user.is_root()
        self.assertFalse(result)

    @patch('getpass.getuser', return_value='testuser')
    def test_get_user(self, mock_getuser):
        """Test get function returns current username."""
        result = user.get()
        self.assertEqual(result, 'testuser')

    def test_home_returns_path(self):
        """Test home function returns a Path object."""
        result = user.home()
        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())

    @unittest.skipIf(sys.platform == 'win32', "POSIX-only test")
    def test_groups_unix(self):
        """Test groups returns list on Unix."""
        result = user.groups()
        self.assertIsInstance(result, list)

    @unittest.skipIf(sys.platform != 'win32', "Windows-only test")
    def test_groups_windows(self):
        """Test groups returns empty list on Windows."""
        result = user.groups()
        self.assertEqual(result, [])

    @unittest.skipIf(sys.platform == 'win32', "POSIX-only test")
    def test_exists_unix_valid_user(self):
        """Test exists returns True for current user on Unix."""
        current_user = user.get()
        result = user.exists(current_user)
        self.assertTrue(result)

    @unittest.skipIf(sys.platform == 'win32', "POSIX-only test")
    def test_exists_unix_invalid_user(self):
        """Test exists returns False for non-existing Unix user."""
        result = user.exists('thisuserdoesnotexist_12345')
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
