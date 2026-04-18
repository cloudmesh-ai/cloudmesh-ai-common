import multiprocessing
import os
import platform
import sys
import getpass
import subprocess
from collections import OrderedDict
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any, Optional

import humanize
import pip
import psutil
import datetime

# --- 1. OS Detection Functions ---

@lru_cache(maxsize=1)
def _get_os_release_data() -> str:
    """Internal helper to read /etc/os-release once and cache it."""
    try:
        return Path("/etc/os-release").read_text().lower()
    except OSError:
        return ""

def os_is_windows() -> bool:
    """Checks if the operating system is Windows."""
    return platform.system() == "Windows"

def os_is_mac() -> bool:
    """Checks if the operating system is macOS."""
    return platform.system() == "Darwin"

def os_is_linux() -> bool:
    """Checks if the os is linux (excluding Raspberry Pi)."""
    return platform.system() == "Linux" and "raspbian" not in _get_os_release_data()

def os_is_pi() -> bool:
    """Checks if the os is Raspberry OS."""
    return platform.system() == "Linux" and "raspbian" in _get_os_release_data()

def has_window_manager() -> bool:
    """Checks if a GUI environment is likely available."""
    if os_is_mac() or os_is_windows():
        return True
    return any(env in os.environ for env in [
        "DISPLAY",
        "WAYLAND_DISPLAY",
        "GNOME_TERMINAL_SCREEN",
        "GNOME_TERMINAL_SERVICE"
    ])

# --- 2. Identity & Platform Helpers ---

def sys_user() -> str:
    """Returns the current username with Colab and Root detection."""
    if "COLAB_GPU" in os.environ:
        return "colab"
    try:
        user = getpass.getuser()
        if user == "root" or os.environ.get("HOME") == "/root":
            return "root"
        return user
    except Exception:
        return os.environ.get("USER", os.environ.get("USERNAME", "None"))

def get_platform() -> str:
    """Returns a simplified string representing the OS platform."""
    if os_is_mac():
        return "macos"
    if os_is_windows():
        return "windows"
    if os_is_pi():
        return "raspberry"
    return sys.platform

def get_cpu_description() -> str:
    """Safely retrieves the CPU model name across platforms."""
    plat = get_platform()
    try:
        if plat == "macos":
            return subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
        elif plat == "windows":
            return platform.processor()
        else:
            content = Path("/proc/cpuinfo").read_text()
            for line in content.splitlines():
                if "model name" in line or "Hardware" in line:
                    return line.split(":", 1)[1].strip()
    except (subprocess.SubprocessError, OSError):
        return "Unknown Processor"
    return "Unknown"

def _get_nvidia_gpu_info() -> Dict[str, Any]:
    """Retrieves GPU info using nvidia-smi."""
    gpu_data = {"gpu.present": False}
    try:
        cmd = [
            "nvidia-smi", 
            "--query-gpu=memory.total,memory.used,temperature.gpu,power.draw,utilization.gpu", 
            "--format=csv,noheader,nounits"
        ]
        output = subprocess.check_output(cmd).decode().strip()
        if output:
            first_gpu = output.splitlines()[0]
            total, used, temp, power, util = map(float, first_gpu.split(","))
            gpu_data.update({
                "gpu.present": True,
                "gpu.vendor": "NVIDIA",
                "gpu.total_vram": humanize.naturalsize(int(total) * 1024 * 1024, binary=True),
                "gpu.used_vram": humanize.naturalsize(int(used) * 1024 * 1024, binary=True),
                "gpu.available_vram": humanize.naturalsize(int(total - used) * 1024 * 1024, binary=True),
                "gpu.temperature": f"{int(temp)}°C",
                "gpu.power_draw": f"{power}W",
                "gpu.utilization": f"{int(util)}%",
            })
    except (subprocess.SubprocessError, OSError, ValueError):
        pass
    return gpu_data

def _get_amd_gpu_info() -> Dict[str, Any]:
    """Retrieves GPU info using rocm-smi."""
    gpu_data = {"gpu.present": False}
    try:
        # rocm-smi can provide VRAM and temp
        output = subprocess.check_output(["rocm-smi", "--showmeminfo", "vram"]).decode().strip()
        if "VRAM" in output:
            gpu_data["gpu.present"] = True
            gpu_data["gpu.vendor"] = "AMD"
            # Simple parsing for VRAM (this is a heuristic as rocm-smi output varies)
            for line in output.splitlines():
                if "Total" in line:
                    vram = line.split()[-1]
                    gpu_data["gpu.total_vram"] = vram
    except (subprocess.SubprocessError, OSError):
        pass
    return gpu_data

def _get_apple_gpu_info() -> Dict[str, Any]:
    """Retrieves GPU info using system_profiler on macOS."""
    gpu_data = {"gpu.present": False}
    try:
        output = subprocess.check_output(["system_profiler", "SPDisplaysDataType"]).decode().strip()
        if "Chip" in output or "GPU" in output:
            gpu_data["gpu.present"] = True
            gpu_data["gpu.vendor"] = "Apple"
            # Apple Silicon uses unified memory, so we report total system memory as VRAM
            mem = psutil.virtual_memory().total
            gpu_data["gpu.total_vram"] = humanize.naturalsize(mem, binary=True)
            gpu_data["gpu.note"] = "Unified Memory"
    except (subprocess.SubprocessError, OSError):
        pass
    return gpu_data

def _get_intel_gpu_info() -> Dict[str, Any]:
    """Retrieves GPU info for Intel GPUs on Linux."""
    gpu_data = {"gpu.present": False}
    try:
        # Check for Intel GPU in /sys/class/drm
        for path in Path("/sys/class/drm").glob("card*"):
            vendor_file = path / "device/vendor"
            if vendor_file.exists() and "0x8086" in vendor_file.read_text().strip():
                gpu_data["gpu.present"] = True
                gpu_data["gpu.vendor"] = "Intel"
                break
    except OSError:
        pass
    return gpu_data

def get_gpu_info() -> Dict[str, Any]:
    """
    Attempts to retrieve GPU information from multiple vendors.
    Returns a dictionary with VRAM, temperature, and power draw if available.
    """
    # 1. Try NVIDIA
    info = _get_nvidia_gpu_info()
    if info["gpu.present"]:
        return info

    # 2. Try AMD
    info = _get_amd_gpu_info()
    if info["gpu.present"]:
        return info

    # 3. Try Apple (macOS only)
    if os_is_mac():
        info = _get_apple_gpu_info()
        if info["gpu.present"]:
            return info

    # 4. Try Intel (Linux only)
    if os_is_linux():
        info = _get_intel_gpu_info()
        if info["gpu.present"]:
            return info

    return {"gpu.present": False}

def get_numa_info() -> Dict[str, Any]:
    """Detects NUMA nodes on Linux systems."""
    numa_data = {"numa.present": False}
    if os_is_linux():
        try:
            node_path = Path("/sys/devices/system/node")
            if node_path.exists():
                nodes = [d.name for d in node_path.iterdir() if d.name.startswith("node")]
                numa_data.update({
                    "numa.present": True,
                    "numa.count": len(nodes),
                    "numa.nodes": nodes,
                })
        except OSError:
            pass
    return numa_data

def get_network_info() -> Dict[str, Any]:
    """Detects high-speed network interfaces (InfiniBand, RoCE) on Linux."""
    net_data = {"net.high_speed": False, "net.interfaces": []}
    if os_is_linux():
        try:
            net_path = Path("/sys/class/net")
            if net_path.exists():
                for iface in net_path.iterdir():
                    # Check for InfiniBand/RoCE by looking for 'infiniband' in the device class or type
                    # A common way is checking /sys/class/net/<iface>/type or looking for ib* interfaces
                    if "ib" in iface.name or (iface / "device").exists():
                        # Heuristic: check if it's an InfiniBand device
                        # In many systems, IB devices have a specific type or are named ib0, ib1...
                        if "ib" in iface.name:
                            net_data["net.high_speed"] = True
                            net_data["net.interfaces"].append(iface.name)
        except OSError:
            pass
    return net_data

def get_disk_read_speed(path: str, size_mb: int = 100) -> Optional[str]:
    """
    Measures the read speed of a file to profile disk throughput.
    Returns the speed in MB/s.
    """
    try:
        file_path = Path(path)
        if not file_path.exists():
            return None
        
        import time
        start_time = time.perf_counter()
        with open(file_path, "rb") as f:
            # Read a specific amount of data to avoid loading huge files entirely into RAM
            _ = f.read(size_mb * 1024 * 1024)
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        speed = size_mb / duration
        return f"{speed:.2f} MB/s"
    except Exception:
        return None

# --- 3. Main Data Collector ---

def resolve_package_path(anchor: str, relative_path: str) -> Path:
    """Resolves a path relative to a given anchor file."""
    return Path(anchor).parent / relative_path

def systeminfo(info: Optional[Dict[str, Any]] = None, user: Optional[str] = None, node: Optional[str] = None) -> Dict[str, Any]:
    """Collects comprehensive system metadata into a dictionary."""
    uname = platform.uname()
    mem = psutil.virtual_memory()

    data = OrderedDict({
        "cpu": get_cpu_description(),
        "cpu_count": multiprocessing.cpu_count(),
        "cpu_cores": psutil.cpu_count(logical=False) or "unknown",
        "cpu_threads": psutil.cpu_count(logical=True) or "unknown",
        "uname.system": uname.system,
        "uname.node": node or uname.node,
        "uname.release": uname.release,
        "uname.version": uname.version,
        "uname.machine": uname.machine,
        "uname.processor": uname.processor,
        "sys.platform": sys.platform,
        "python": sys.version,
        "python.version": sys.version.split(" ", 1)[0],
        "python.pip": pip.__version__,
        "user": user or sys_user(),
        "mem.percent": f"{mem.percent}%",
    })

    try:
        data["frequency"] = psutil.cpu_freq().current
    except Exception:
        data["frequency"] = None

    mem_fields = ["total", "available", "used", "free", "active", "inactive", "wired"]
    for attr in mem_fields:
        val = getattr(mem, attr, None)
        if val is not None:
            data[f"mem.{attr}"] = humanize.naturalsize(val, binary=True)

    # GPU Info
    data.update(get_gpu_info())

    # NUMA Info
    data.update(get_numa_info())

    # Network Info
    data.update(get_network_info())

    if os_is_mac():
        data["platform.version"] = platform.mac_ver()[0]
    elif os_is_windows():
        data["platform.version"] = platform.win32_ver()
    else:
        try:
            for path in Path("/etc").glob("*release"):
                for line in path.read_text().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        clean_k = k.strip().replace(" ", "_")
                        clean_v = v.strip().strip('"\'')
                        data[clean_k] = clean_v
        except OSError:
            data["platform.version"] = uname.version

    if info:
        data.update(info)

    data["date"] = str(datetime.datetime.now())
    return dict(data)

if __name__ == "__main__":
    import json
    print(json.dumps(systeminfo(), indent=4))