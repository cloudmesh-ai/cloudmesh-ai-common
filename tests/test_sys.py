"""Unit tests for cloudmesh.ai.common.sys module."""

import unittest
import sys
import platform
from unittest.mock import patch, MagicMock
from cloudmesh.ai.common import sys as sys_module


class TestSysModule(unittest.TestCase):
    """Test cases for sys utility functions."""

    # --- OS Detection Tests ---

    @patch("platform.system", return_value="Windows")
    def test_os_is_windows_true(self, mock_platform):
        """Test os_is_windows returns True on Windows."""
        result = sys_module.os_is_windows()
        self.assertTrue(result)

    @patch("platform.system", return_value="Linux")
    def test_os_is_windows_false(self, mock_platform):
        """Test os_is_windows returns False on non-Windows."""
        result = sys_module.os_is_windows()
        self.assertFalse(result)

    @patch("platform.system", return_value="Darwin")
    def test_os_is_mac_true(self, mock_platform):
        """Test os_is_mac returns True on macOS."""
        result = sys_module.os_is_mac()
        self.assertTrue(result)

    @patch("platform.system", return_value="Linux")
    def test_os_is_mac_false(self, mock_platform):
        """Test os_is_mac returns False on non-macOS."""
        result = sys_module.os_is_mac()
        self.assertFalse(result)

    @patch("cloudmesh.ai.common.sys._get_os_release_data", return_value="raspbian")
    @patch("platform.system", return_value="Linux")
    def test_os_is_linux_false_on_pi(self, mock_platform, mock_os_data):
        """Test os_is_linux returns False on Raspberry Pi."""
        result = sys_module.os_is_linux()
        self.assertFalse(result)

    @patch("cloudmesh.ai.common.sys._get_os_release_data", return_value="debian")
    @patch("platform.system", return_value="Linux")
    def test_os_is_linux_true(self, mock_platform, mock_os_data):
        """Test os_is_linux returns True on Linux (non-Pi)."""
        result = sys_module.os_is_linux()
        self.assertTrue(result)

    @patch("cloudmesh.ai.common.sys._get_os_release_data", return_value="raspbian")
    @patch("platform.system", return_value="Linux")
    def test_os_is_pi_true(self, mock_platform, mock_os_data):
        """Test os_is_pi returns True on Raspberry OS."""
        result = sys_module.os_is_pi()
        self.assertTrue(result)

    @patch("cloudmesh.ai.common.sys._get_os_release_data", return_value="debian")
    @patch("platform.system", return_value="Linux")
    def test_os_is_pi_false(self, mock_platform, mock_os_data):
        """Test os_is_pi returns False on non-Raspberry Linux."""
        result = sys_module.os_is_pi()
        self.assertFalse(result)

    # --- Window Manager Tests ---

    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=True)
    def test_has_window_manager_mac(self, mock_os_is_mac):
        """Test has_window_manager returns True on macOS."""
        result = sys_module.has_window_manager()
        self.assertTrue(result)

    @patch("cloudmesh.ai.common.sys.os_is_windows", return_value=True)
    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=False)
    def test_has_window_manager_windows(self, mock_os_is_mac, mock_os_is_windows):
        """Test has_window_manager returns True on Windows."""
        result = sys_module.has_window_manager()
        self.assertTrue(result)

    @patch.dict("os.environ", {"DISPLAY": ":0"}, clear=True)
    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=False)
    @patch("cloudmesh.ai.common.sys.os_is_windows", return_value=False)
    def test_has_window_manager_linux_display(self, mock_os_is_windows, mock_os_is_mac):
        """Test has_window_manager returns True on Linux with DISPLAY."""
        result = sys_module.has_window_manager()
        self.assertTrue(result)

    @patch.dict("os.environ", {}, clear=True)
    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=False)
    @patch("cloudmesh.ai.common.sys.os_is_windows", return_value=False)
    def test_has_window_manager_no_gui(self, mock_os_is_windows, mock_os_is_mac):
        """Test has_window_manager returns False on headless system."""
        result = sys_module.has_window_manager()
        self.assertFalse(result)

    # --- Identity & Platform Tests ---

    @patch.dict("os.environ", {"COLAB_GPU": "true"}, clear=True)
    def test_sys_user_colab(self):
        """Test sys_user returns 'colab' in Colab environment."""
        result = sys_module.sys_user()
        self.assertEqual(result, "colab")

    @patch.dict("os.environ", {}, clear=True)
    @patch("getpass.getuser", return_value="testuser")
    def test_sys_user_normal(self, mock_getuser):
        """Test sys_user returns normal username."""
        result = sys_module.sys_user()
        self.assertEqual(result, "testuser")

    @patch.dict("os.environ", {"HOME": "/root"}, clear=True)
    @patch("getpass.getuser", return_value="root")
    def test_sys_user_root(self, mock_getuser):
        """Test sys_user returns 'root' for root user."""
        result = sys_module.sys_user()
        self.assertEqual(result, "root")

    @patch.dict("os.environ", {"USER": "envuser"}, clear=True)
    @patch("getpass.getuser", side_effect=Exception("getpass failed"))
    def test_sys_user_fallback(self, mock_getuser):
        """Test sys_user falls back to environment variables."""
        result = sys_module.sys_user()
        self.assertEqual(result, "envuser")

    # --- Platform Detection ---

    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=True)
    def test_get_platform_mac(self, mock_is_mac):
        """Test get_platform returns 'macos'."""
        result = sys_module.get_platform()
        self.assertEqual(result, "macos")

    @patch("cloudmesh.ai.common.sys.os_is_windows", return_value=True)
    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=False)
    def test_get_platform_windows(self, mock_is_mac, mock_is_windows):
        """Test get_platform returns 'windows'."""
        result = sys_module.get_platform()
        self.assertEqual(result, "windows")

    @patch("cloudmesh.ai.common.sys.os_is_pi", return_value=True)
    @patch("cloudmesh.ai.common.sys.os_is_windows", return_value=False)
    @patch("cloudmesh.ai.common.sys.os_is_mac", return_value=False)
    def test_get_platform_raspberry(self, mock_is_mac, mock_is_windows, mock_is_pi):
        """Test get_platform returns 'raspberry'."""
        result = sys_module.get_platform()
        self.assertEqual(result, "raspberry")

    # --- CPU Tests ---

    @patch("cloudmesh.ai.common.sys.get_platform", return_value="macos")
    @patch(
        "cloudmesh.ai.common.sys.subprocess.check_output",
        return_value=b"Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz\n",
    )
    def test_get_cpu_description_mac(self, mock_check_output, mock_platform):
        """Test get_cpu_description on macOS."""
        result = sys_module.get_cpu_description()
        self.assertIn("Intel", result)

    @patch("cloudmesh.ai.common.sys.get_platform", return_value="windows")
    @patch("platform.processor", return_value="Intel64 Family 6 Model 142 Stepping 10")
    def test_get_cpu_description_windows(self, mock_processor, mock_platform):
        """Test get_cpu_description on Windows."""
        result = sys_module.get_cpu_description()
        self.assertIn("Intel", result)

    @patch("cloudmesh.ai.common.sys.get_platform", return_value="linux")
    @patch(
        "cloudmesh.ai.common.sys.readfile",
        return_value="model name\t: Intel(R) Core(TM) i5-8250U CPU @ 1.60GHz",
    )
    def test_get_cpu_description_linux(self, mock_readfile, mock_platform):
        """Test get_cpu_description on Linux."""
        result = sys_module.get_cpu_description()
        self.assertIn("Intel", result)

    @patch("cloudmesh.ai.common.sys.get_platform", return_value="linux")
    @patch("cloudmesh.ai.common.sys.readfile", side_effect=Exception("Read failed"))
    def test_get_cpu_description_error(self, mock_readfile, mock_platform):
        """Test get_cpu_description handles errors gracefully."""
        result = sys_module.get_cpu_description()
        self.assertEqual(result, "Unknown Processor")

    # --- System Info Tests ---

    @patch("cloudmesh.ai.common.sys.get_cpu_description", return_value="Intel i7")
    @patch("multiprocessing.cpu_count", return_value=8)
    @patch("cloudmesh.ai.common.sys.psutil.cpu_count", side_effect=[4, 8])
    @patch("platform.uname")
    @patch("cloudmesh.ai.common.sys.psutil.virtual_memory")
    @patch("cloudmesh.ai.common.sys.sys_user", return_value="testuser")
    def test_systeminfo_basic(
        self,
        mock_user,
        mock_mem,
        mock_uname,
        mock_cpu_count,
        mock_cpu_multiprocessing,
        mock_cpu_desc,
    ):
        """Test systeminfo collects basic system information."""
        mock_uname_result = MagicMock()
        mock_uname_result.system = "Linux"
        mock_uname_result.node = "testnode"
        mock_uname_result.release = "5.4.0"
        mock_uname_result.version = "#1 SMP"
        mock_uname_result.machine = "x86_64"
        mock_uname_result.processor = "x86_64"
        mock_uname.return_value = mock_uname_result

        mock_mem_result = MagicMock()
        mock_mem_result.percent = 50.0
        mock_mem_result.total = 16000000000
        mock_mem_result.available = 8000000000
        mock_mem_result.used = 8000000000
        mock_mem_result.free = 0
        mock_mem_result.active = 8000000000
        mock_mem_result.inactive = 0
        mock_mem_result.wired = 0
        mock_mem.return_value = mock_mem_result

        result = sys_module.systeminfo()

        self.assertIn("cpu", result)
        self.assertIn("cpu_count", result)
        self.assertIn("user", result)
        self.assertEqual(result["cpu"], "Intel i7")
        self.assertEqual(result["cpu_count"], 8)
        self.assertEqual(result["user"], "testuser")


if __name__ == "__main__":
    unittest.main()
