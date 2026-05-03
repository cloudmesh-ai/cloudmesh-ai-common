import multiprocessing
import os
import platform
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional, Union

import humanize
import pip
import psutil
from cloudmesh.ai.common.DateTime import DateTime
from cloudmesh.ai.common.io import readfile


def os_is_windows() -> bool:
    """Checks if the os is windows

    Returns:
        bool: True is windows
    """
    return platform.system() == "Windows"


# noinspection PyBroadException
def os_is_linux() -> bool:
    """Checks if the os is linux

    Returns:
        bool: True is linux
    """
    try:
        content = readfile("/etc/os-release")
        return platform.system() == "Linux" and "raspbian" not in content
    except Exception:  # noqa: E722
        return False


def os_is_mac() -> bool:
    """Checks if the os is macOS

    Returns:
        bool: True is macOS
    """
    return platform.system() == "Darwin"


# noinspection PyBroadException
def os_is_pi() -> bool:
    """Checks if the os is Raspberry OS

    Returns:
        bool: True is Raspberry OS
    """
    try:
        content = readfile("/etc/os-release")
        return platform.system() == "Linux" and "raspbian" in content
    except Exception:  # noqa: E722
        return False


def has_window_manager() -> bool:
    if os_is_mac() or os_is_windows():
        return True
    else:
        return (
            "GNOME_TERMINAL_SCREEN" in os.environ
            or "GNOME_TERMINAL_SERVICE" in os.environ
        )


def sys_user() -> str:
    if "COLAB_GPU" in os.environ:
        return "collab"
    try:
        if sys.platform == "win32":
            return os.environ["USERNAME"]
    except Exception:  # noqa: E722
        pass
    try:
        return os.environ["USER"]
    except Exception:  # noqa: E722
        pass
    try:
        if os.environ["HOME"] == "/root":
            return "root"
    except Exception:  # noqa: E722
        pass

    return "None"


def get_platform() -> str:
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    try:
        content = readfile("/etc/os-release")
        if sys.platform == "linux" and "raspbian" in content:
            return "raspberry"
        else:
            return sys.platform
    except Exception:  # noqa: E722
        return sys.platform


def get_gpu_info() -> Dict[str, Any]:
    """Retrieves GPU information using nvidia-smi.

    Returns:
        Dict: GPU details including name, total memory, and used memory.
    """
    gpu_data = {}
    try:
        # Query nvidia-smi for GPU name, memory total, and memory used
        cmd = [
            "nvidia-smi",
            "--query-gpu=name,memory.total,memory.used",
            "--format=csv,noheader,nounits"
        ]
        result = subprocess.check_output(cmd, encoding="utf-8").strip()
        if result:
            lines = result.splitlines()
            for i, line in enumerate(lines):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) == 3:
                    name, total, used = parts
                    gpu_id = f"gpu{i}"
                    gpu_data[f"{gpu_id}.name"] = name
                    gpu_data[f"{gpu_id}.mem_total"] = humanize.naturalsize(int(total) * 1024 * 1024, binary=True)
                    gpu_data[f"{gpu_id}.mem_used"] = humanize.naturalsize(int(used) * 1024 * 1024, binary=True)
                    gpu_data[f"{gpu_id}.mem_percent"] = f"{(int(used)/int(total)*100):.1f} %"
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        pass

    return gpu_data


def systeminfo(info: Optional[Dict] = None, user: Optional[str] = None, node: Optional[str] = None) -> Dict[str, Any]:
    """Collects comprehensive system information.

    Args:
        info (Optional[Dict]): Additional info to merge.
        user (Optional[str]): Override user.
        node (Optional[str]): Override node name.

    Returns:
        Dict: System information.
    """
    uname = platform.uname()
    mem = psutil.virtual_memory()

    try:
        frequency = psutil.cpu_freq()
    except Exception:  # noqa: E722
        frequency = None

    try:
        cores = psutil.cpu_count(logical=False)
    except Exception:  # noqa: E722
        cores = "unknown"

    operating_system = get_platform()

    description = ""
    try:
        if operating_system == "macos":
            description = os.popen("sysctl -n machdep.cpu.brand_string").read()
        elif operating_system == "win32":
            description = platform.processor()
        elif operating_system == "linux":
            lines = readfile("/proc/cpuinfo").strip().splitlines()
            for line in lines:
                if "model name" in line:
                    description = re.sub(".*model name.*:", "", line, 1)
    except Exception:  # noqa: E722
        pass

    data = OrderedDict(
        {
            "cpu": description.strip(),
            "cpu_count": multiprocessing.cpu_count(),
            "cpu_threads": multiprocessing.cpu_count(),
            "cpu_cores": cores,
            "uname.system": uname.system,
            "uname.node": uname.node,
            "uname.release": uname.release,
            "uname.version": uname.version,
            "uname.machine": uname.machine,
            "uname.processor": uname.processor,
            "sys.platform": sys.platform,
            "python": sys.version,
            "python.version": sys.version.split(" ", 1)[0],
            "python.pip": pip.__version__,
            "user": sys_user(),
            "mem.percent": str(mem.percent) + " %",
            "frequency": frequency,
        }
    )
    for attribute in [
        "total",
        "available",
        "used",
        "free",
        "active",
        "inactive",
        "wired",
    ]:
        try:
            data[f"mem.{attribute}"] = humanize.naturalsize(
                getattr(mem, attribute), binary=True
            )
        except Exception:  # noqa: E722
            pass

    if data["sys.platform"] == "darwin":
        data["platform.version"] = platform.mac_ver()[0]
    elif data["sys.platform"] == "win32":
        data["platform.version"] = platform.win32_ver()
    else:
        data["platform.version"] = uname.version

    try:
        release_files = Path("/etc").glob("*release")
        for filename in release_files:
            content = readfile(filename.resolve()).splitlines()
            for line in content:
                if "=" in line:
                    attribute, value = line.split("=", 1)
                    attribute = attribute.replace(" ", "")
                    data[attribute] = value
    except Exception:  # noqa: E722
        pass

    # Add GPU information
    gpu_info = get_gpu_info()
    data.update(gpu_info)

    if info is not None:
        data.update(info)
    if user is not None:
        data["user"] = user
    if node is not None:
        data["uname.node"] = node
    data["date"] = str(DateTime.now())
    return dict(data)