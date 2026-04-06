import multiprocessing
import os
import platform
import re
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
from cloudmesh.common.DateTime import DateTime
from cloudmesh.common.util import readfile

# --- 1. OS Detection Functions (All Restored) ---

@lru_cache(maxsize=1)
def _get_os_release_data() -> str:
    """Internal helper to read /etc/os-release once and cache it."""
    try:
        return readfile("/etc/os-release").lower()
    except Exception:
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
    # Restored your logic + added standard Linux display checks
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
        # Standard cross-platform way to get user
        user = getpass.getuser()
        if user == "root" or os.environ.get("HOME") == "/root":
            return "root"
        return user
    except Exception:
        # Fallback to env variables if getpass fails
        return os.environ.get("USER", os.environ.get("USERNAME", "None"))

def get_platform() -> str:
    """Returns a simplified string representing the OS platform."""
    if os_is_mac(): return "macos"
    if os_is_windows(): return "windows"
    if os_is_pi(): return "raspberry"
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
            # Linux / Raspberry Pi / Generic Unix
            content = readfile("/proc/cpuinfo")
            for line in content.splitlines():
                if "model name" in line or "Hardware" in line:
                    return line.split(":", 1)[1].strip()
    except Exception:
        return "Unknown Processor"
    return "Unknown"

# --- 3. Main Data Collector ---

def systeminfo(info: Optional[Dict] = None, user: Optional[str] = None, node: Optional[str] = None) -> Dict[str, Any]:
    """
    Collects comprehensive system metadata into an OrderedDict.
    """
    uname = platform.uname()
    mem = psutil.virtual_memory()
    
    # We use OrderedDict to maintain the same field order as your original script
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

    # Restored your CPU Frequency logic
    try:
        data["frequency"] = psutil.cpu_freq().current
    except Exception:
        data["frequency"] = None

    # Memory attributes (total, available, used, free, etc.)
    mem_fields = ["total", "available", "used", "free", "active", "inactive", "wired"]
    for attr in mem_fields:
        val = getattr(mem, attr, None)
        if val is not None:
            data[f"mem.{attr}"] = humanize.naturalsize(val, binary=True)

    # OS Versioning Details
    if os_is_mac():
        data["platform.version"] = platform.mac_ver()[0]
    elif os_is_windows():
        data["platform.version"] = platform.win32_ver()
    else:
        # Restored your logic for scanning /etc/*release files
        try:
            for path in Path("/etc").glob("*release"):
                for line in readfile(path).splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        data[k.replace(" ", "")] = v.strip('"')
        except Exception:
            data["platform.version"] = uname.version

    if info:
        data.update(info)
        
    data["date"] = str(DateTime.now())
    return dict(data)

if __name__ == "__main__":
    import json
    print(json.dumps(systeminfo(), indent=4))