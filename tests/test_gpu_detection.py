"""Tests for GPU detection across different vendors."""

import pytest
from unittest.mock import patch, MagicMock
from cloudmesh.ai.common import sys as ai_sys


@patch('subprocess.check_output')
def test_nvidia_detection(mock_sub):
    """Test NVIDIA GPU detection."""
    # Mock nvidia-smi output: total, used, temp, power, util
    mock_sub.return_value = b"16384, 1024, 45, 150, 10"
    
    info = ai_sys.get_gpu_info()
    assert info["gpu.present"] is True
    assert info["gpu.vendor"] == "NVIDIA"
    assert "16.0 GiB" in info["gpu.total_vram"]


@patch('subprocess.check_output')
def test_amd_detection(mock_sub):
    """Test AMD GPU detection."""
    # Mock rocm-smi output
    mock_sub.return_value = b"VRAM Total: 16384 MB"
    
    # We need to make sure NVIDIA check fails first
    with patch('cloudmesh.ai.common.sys._get_nvidia_gpu_info', return_value={"gpu.present": False}):
        info = ai_sys.get_gpu_info()
        assert info["gpu.present"] is True
        assert info["gpu.vendor"] == "AMD"


@patch('cloudmesh.ai.common.sys.os_is_mac', return_value=True)
@patch('subprocess.check_output')
def test_apple_detection(mock_sub, mock_mac):
    """Test Apple Silicon detection."""
    mock_sub.return_value = b"Chip: Apple M2 Max"
    
    with patch('cloudmesh.ai.common.sys._get_nvidia_gpu_info', return_value={"gpu.present": False}), \
         patch('cloudmesh.ai.common.sys._get_amd_gpu_info', return_value={"gpu.present": False}):
        info = ai_sys.get_gpu_info()
        assert info["gpu.present"] is True
        assert info["gpu.vendor"] == "Apple"
        assert info["gpu.note"] == "Unified Memory"


@patch('cloudmesh.ai.common.sys.os_is_linux', return_value=True)
@patch('cloudmesh.ai.common.sys.os_is_mac', return_value=False)
def test_intel_detection(mock_mac, mock_linux):
    """Test Intel GPU detection."""
    # Mock the existence of an Intel GPU in /sys/class/drm
    with patch('cloudmesh.ai.common.sys.Path.glob') as mock_glob:
        mock_card = MagicMock()
        mock_card.name = "card0"
        mock_card.__truediv__.return_value = MagicMock()
        mock_card.__truediv__.return_value.exists.return_value = True
        mock_card.__truediv__.return_value.read_text.return_value = "0x8086"
        mock_glob.return_value = [mock_card]
        
        with patch('cloudmesh.ai.common.sys._get_nvidia_gpu_info', return_value={"gpu.present": False}), \
             patch('cloudmesh.ai.common.sys._get_amd_gpu_info', return_value={"gpu.present": False}):
            info = ai_sys.get_gpu_info()
            assert info["gpu.present"] is True
            assert info["gpu.vendor"] == "Intel"


def test_no_gpu():
    """Test case where no GPU is found."""
    with patch('subprocess.check_output', side_effect=OSError), \
         patch('cloudmesh.ai.common.sys.os_is_mac', return_value=False), \
         patch('cloudmesh.ai.common.sys.os_is_linux', return_value=False):
        info = ai_sys.get_gpu_info()
        assert info["gpu.present"] is False