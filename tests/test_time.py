"""Unit tests for cloudmesh.ai.common.time module."""

import unittest
from unittest.mock import patch, MagicMock
from cloudmesh.ai.common import time


class TestTimeModule(unittest.TestCase):
    """Test cases for time utility functions."""

    def test_timezone_default(self):
        """Test timezone detection with default fallback."""
        with patch(
            "cloudmesh.ai.common.time.get_localzone_name",
            side_effect=Exception("Mock error"),
        ):
            result = time.timezone()
            self.assertEqual(result, "America/New_York")

    def test_timezone_custom_default(self):
        """Test timezone with custom default value."""
        with patch(
            "cloudmesh.ai.common.time.get_localzone_name",
            side_effect=Exception("Mock error"),
        ):
            result = time.timezone("UTC")
            self.assertEqual(result, "UTC")

    def test_timezone_success(self):
        """Test successful timezone detection."""
        with patch(
            "cloudmesh.ai.common.time.get_localzone_name", return_value="Europe/London"
        ):
            result = time.timezone()
            self.assertEqual(result, "Europe/London")

    def test_locale_name_default(self):
        """Test locale name with default fallback."""
        with patch(
            "cloudmesh.ai.common.time.locale.getdefaultlocale",
            return_value=(None, None),
        ):
            result = time.locale_name()
            self.assertEqual(result, "us")

    def test_locale_name_success(self):
        """Test successful locale name detection."""
        with patch(
            "cloudmesh.ai.common.time.locale.getdefaultlocale",
            return_value=("en_US", "UTF-8"),
        ):
            result = time.locale_name()
            self.assertEqual(result, "en")

    def test_locale_name_different_language(self):
        """Test locale name with different language code."""
        with patch(
            "cloudmesh.ai.common.time.locale.getdefaultlocale",
            return_value=("fr_FR", "UTF-8"),
        ):
            result = time.locale_name()
            self.assertEqual(result, "fr")

    def test_locale_name_exception(self):
        """Test locale name with exception handling."""
        with patch(
            "cloudmesh.ai.common.time.locale.getdefaultlocale",
            side_effect=Exception("Mock error"),
        ):
            result = time.locale_name()
            self.assertEqual(result, "us")


if __name__ == "__main__":
    unittest.main()
