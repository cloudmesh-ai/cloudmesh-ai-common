"""
System utility functions for cloudmesh-ai.
Provides tools for OS detection, hardware information retrieval, 
and real-time system metrics collection.
"""

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
    """Internal helper to read /etc/os-release once and cache it.

    Returns:
        The content of /etc/os-release as a lowercase string, or an empty string if not found.
    """
    try:
        return Path("/etc/os-release").read_text().lower()
    except OSError:
        return ""

def os_is_windows() -> bool:
    """Checks if the operating system is Windows.

    Returns:
        True if the OS is Windows, False otherwise.
    """
    return platform.system() == "Windows"

def os_is_mac() -> bool:
    """Checks if the operating system is macOS.

    Returns:
        True if the OS is macOS, False otherwise.
    """
    return platform.system() == "Darwin"

def os_is_linux() -> bool:
    """Checks if the os is linux (excluding Raspberry Pi).

    Returns:
        True if the OS is Linux and not Raspbian, False otherwise.
    """
    return platform.system() == "Linux" and "raspbian" not in _get_os_release_data()

def os_is_pi() -> bool:
    """Checks if the os is Raspberry OS.

    Returns:
        True if the OS is Raspbian, False otherwise.
    """
    return platform.system() == "Linux" and "raspbian" in _get_os_release_data()

def has_window_manager() -> bool:
    """Checks if a GUI environment is likely available.

    Returns:
        True if a window manager is likely present, False otherwise.
    """
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
    """Returns the current username with Colab and Root detection.

    Returns:
        The detected username as a string.
    """
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
    """Returns a simplified string representing the OS platform.

    Returns:
        A string representing the platform (e.g., 'macos', 'windows', 'raspberry').
    """
    if os_is_mac():
        return "macos"
    if os_is_windows():
        return "windows"
    if os_is_pi():
        return "raspberry"
    return sys.platform

def get_cpu_description() -> str:
    """Safely retrieves the CPU model name across platforms.

    Returns:
        The CPU model description as a string.
    """
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
    """Retrieves GPU info using nvidia-smi.

    Returns:
        A dictionary containing NVIDIA GPU metrics if present, otherwise 
        {'gpu.present': False}.
    """
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
    """Retrieves GPU info using rocm-smi.

    Returns:
        A dictionary containing AMD GPU metrics if present, otherwise 
        {'gpu.present': False}.
    """
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
    """Retrieves GPU info using system_profiler on macOS.

    Returns:
        A dictionary containing Apple GPU metrics if present, otherwise 
        {'gpu.present': False}.
    """
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
    """Retrieves GPU info for Intel GPUs on Linux.

    Returns:
        A dictionary containing Intel GPU metrics if present, otherwise 
        {'gpu.present': False}.
    """
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
    """Attempts to retrieve GPU information from multiple vendors.

    Returns:
        A dictionary with VRAM, temperature, and power draw if available, 
        otherwise {'gpu.present': False}.
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

def get_thermal_info() -> Dict[str, Any]:
    """Retrieves system thermal information across platforms.

    Returns:
        A dictionary with CPU and GPU temperatures.
    """
    thermal_data = {"thermal.present": False, "cpu.temp": None}
    
    if os_is_linux():
        try:
            # Try thermal_zone first
            zones = list(Path("/sys/class/thermal").glob("thermal_zone*"))
            if zones:
                # Usually zone0 is the package temp
                temp_raw = Path(zones[0]) / "temp"
                if temp_raw.exists():
                    temp_c = int(temp_raw.read_text().strip()) / 1000.0
                    thermal_data["cpu.temp"] = f"{temp_c:.1f}°C"
                    thermal_data["thermal.present"] = True
            
            # Try hwmon for more detailed sensors if zone failed or for backup
            if not thermal_data["thermal.present"]:
                hwmon_paths = list(Path("/sys/class/hwmon").glob("hwmon*"))
                for path in hwmon_paths:
                    temp_files = list(path.glob("temp*_input"))
                    if temp_files:
                        temp_c = int(temp_files[0].read_text().strip()) / 1000.0
                        thermal_data["cpu.temp"] = f"{temp_c:.1f}°C"
                        thermal_data["thermal.present"] = True
                        break
        except (OSError, ValueError):
            pass

    elif os_is_mac():
        try:
            # macOS doesn't have a simple /sys path. 
            # We can try sysctl, though it's often restricted on Apple Silicon.
            output = subprocess.check_output(["sysctl", "-n", "machdep.cpu.temperature"]).decode().strip()
            if output:
                thermal_data["cpu.temp"] = f"{output}°C"
                thermal_data["thermal.present"] = True
        except (subprocess.SubprocessError, OSError):
            pass

    return thermal_data

def get_numa_info() -> Dict[str, Any]:
    """Detects NUMA nodes on Linux systems.

    Returns:
        A dictionary containing NUMA presence and node details.
    """
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

def get_container_info() -> Dict[str, Any]:
    """Detects if the system is running inside a container (Docker, Kubernetes).

    Returns:
        A dictionary with container type and metadata.
    """
    container_data = {"container.present": False}
    
    # 1. Docker detection
    if Path("/.dockerenv").exists():
        container_data["container.present"] = True
        container_data["container.type"] = "docker"
    
    # 2. Cgroup detection (Linux)
    if os_is_linux():
        try:
            cgroup_content = Path("/proc/1/cgroup").read_text()
            if "docker" in cgroup_content.lower():
                container_data["container.present"] = True
                container_data["container.type"] = "docker"
            elif "kubepods" in cgroup_content.lower():
                container_data["container.present"] = True
                container_data["container.type"] = "kubernetes"
        except OSError:
            pass

    # 3. Kubernetes specific detection
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        container_data["container.present"] = True
        container_data["container.type"] = "kubernetes"
        
        # Try to extract namespace
        ns_path = Path("/var/run/secrets/kubernetes.io/serviceaccount/namespace")
        if ns_path.exists():
            container_data["container.namespace"] = ns_path.read_text().strip()

    return container_data

def get_network_info() -> Dict[str, Any]:
    """Detects high-speed network interfaces (InfiniBand, RoCE) on Linux.

    Returns:
        A dictionary indicating if high-speed networking is present and 
        listing the interfaces.
    """
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
    """Measures the read speed of a file to profile disk throughput.

    Args:
        path: Path to the file to read.
        size_mb: Amount of data to read in megabytes. Defaults to 100.

    Returns:
        The read speed as a string (e.g., "150.25 MB/s"), or None if an error occurs.
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

def get_cpu_metrics() -> Dict[str, Any]:
    """Retrieves real-time CPU utilization and load averages.

    Returns:
        A dictionary containing 'cpu.utilization_overall', 'cpu.utilization_per_core', 
        and 'cpu.load_avg'.
    """
    try:
        return {
            "cpu.utilization_overall": f"{psutil.cpu_percent(interval=None)}%",
            "cpu.utilization_per_core": [f"{x}%" for x in psutil.cpu_percent(interval=None, percpu=True)],
            "cpu.load_avg": psutil.getloadavg() if hasattr(psutil, "getloadavg") else None,
        }
    except Exception:
        return {}

def get_memory_metrics() -> Dict[str, Any]:
    """Retrieves detailed real-time memory and swap usage.

    Returns:
        A dictionary containing utilization percentages and human-readable 
        sizes for available, used, and swap memory.
    """
    try:
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        return {
            "mem.utilization": f"{vm.percent}%",
            "mem.available": humanize.naturalsize(vm.available, binary=True),
            "mem.used": humanize.naturalsize(vm.used, binary=True),
            "swap.total": humanize.naturalsize(sw.total, binary=True),
            "swap.used": humanize.naturalsize(sw.used, binary=True),
            "swap.percent": f"{sw.percent}%",
        }
    except Exception:
        return {}

def get_disk_metrics() -> Dict[str, Any]:
    """Retrieves real-time disk usage and I/O statistics for the root partition.

    Returns:
        A dictionary containing total, used, and free space, as well as 
        read/write counts and bytes.
    """
    try:
        usage = psutil.disk_usage("/")
        io = psutil.disk_io_counters()
        return {
            "disk.total": humanize.naturalsize(usage.total, binary=True),
            "disk.used": humanize.naturalsize(usage.used, binary=True),
            "disk.free": humanize.naturalsize(usage.free, binary=True),
            "disk.percent": f"{usage.percent}%",
            "disk.read_count": io.read_count if io else None,
            "disk.write_count": io.write_count if io else None,
            "disk.read_bytes": humanize.naturalsize(io.read_bytes, binary=True) if io else None,
            "disk.write_bytes": humanize.naturalsize(io.write_bytes, binary=True) if io else None,
        }
    except Exception:
        return {}

# --- 3. Main Data Collector ---

def resolve_package_path(anchor: str, relative_path: str) -> Path:
    """Resolves a path relative to a given anchor file.

    Args:
        anchor: The anchor file path.
        relative_path: The relative path to resolve.

    Returns:
        The resolved absolute Path.
    """
    return Path(anchor).parent / relative_path

def systeminfo(info: Optional[Dict[str, Any]] = None, user: Optional[str] = None, node: Optional[str] = None, realtime: bool = False) -> Dict[str, Any]:
    """Collects comprehensive system metadata into a dictionary.

    Args:
        info: Optional dictionary of additional information to merge into the result.
        user: Optional override for the current system user.
        node: Optional override for the system node name.
        realtime: If True, includes real-time CPU, memory, and disk utilization metrics.

    Returns:
        A dictionary containing system hardware, OS, and (optionally) real-time performance data.
    """
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

    # Thermal Info
    data.update(get_thermal_info())

    # NUMA Info
    data.update(get_numa_info())

    # Network Info
    data.update(get_network_info())

    # Container Info
    data.update(get_container_info())

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

    if realtime:
        data.update(get_cpu_metrics())
        data.update(get_memory_metrics())
        data.update(get_disk_metrics())

    if info:
        data.update(info)

    data["date"] = str(datetime.datetime.now())
    return dict(data)

if __name__ == "__main__":
    import json
    print(json.dumps(systeminfo(), indent=4))