import pytest
from unittest.mock import patch, MagicMock, mock_open
from cloudmesh.ai.common import sys

def test_systeminfo_keys():
    info = sys.systeminfo()
    # Check for core keys
    assert "cpu" in info
    assert "user" in info
    assert "sys.platform" in info
    # Check for GPU keys
    assert "gpu.present" in info
    # Check for NUMA keys
    assert "numa.present" in info

def test_os_detection():
    # Basic sanity check that detection functions return booleans
    assert isinstance(sys.os_is_windows(), bool)
    assert isinstance(sys.os_is_mac(), bool)
    assert isinstance(sys.os_is_linux(), bool)
    assert isinstance(sys.os_is_pi(), bool)

def test_get_platform():
    plat = sys.get_platform()
    assert isinstance(plat, str)
    assert len(plat) > 0

def test_get_gpu_info_mocked():
    """Test GPU info retrieval by mocking nvidia-smi output."""
    # Mock output: total, used, temp, power, util
    mock_output = b"16384, 4096, 55, 120.5, 20\n"
    with patch("subprocess.check_output", return_value=mock_output):
        info = sys.get_gpu_info()
        assert info["gpu.present"] is True
        assert "55°C" in info["gpu.temperature"]
        assert "120.5W" in info["gpu.power_draw"]
        assert "16.0 GiB" in info["gpu.total_vram"]

def test_get_numa_info_mocked():
    """Test NUMA detection by mocking Linux filesystem."""
    with patch("cloudmesh.ai.common.sys.os_is_linux", return_value=True), \
         patch("cloudmesh.ai.common.sys.Path.exists", return_value=True), \
         patch("cloudmesh.ai.common.sys.Path.iterdir") as mock_iter:
        
        # Mock two NUMA nodes
        mock_node1 = MagicMock()
        mock_node1.name = "node0"
        mock_node2 = MagicMock()
        mock_node2.name = "node1"
        mock_iter.return_value = [mock_node1, mock_node2]
        
        info = sys.get_numa_info()
        assert info["numa.present"] is True
        assert info["numa.count"] == 2
        assert "node0" in info["numa.nodes"]
        assert "node1" in info["numa.nodes"]

def test_get_disk_read_speed_mocked():
    """Test disk read speed profiling by mocking file I/O and time."""
    mock_data = b"0" * (100 * 1024 * 1024) # 100MB of zeros
    with patch("cloudmesh.ai.common.sys.Path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_data)), \
         patch("time.perf_counter") as mock_time:
        
        # Simulate 1 second for the read operation
        mock_time.side_effect = [0.0, 1.0]
        
        speed = sys.get_disk_read_speed("fake_path", size_mb=100)
        assert speed == "100.00 MB/s"

def test_get_disk_read_speed_missing_file():
    """Test disk read speed returns None for missing files."""
    with patch("cloudmesh.ai.common.sys.Path.exists", return_value=False):
        speed = sys.get_disk_read_speed("non_existent_file")
        assert speed is None