import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

def path_expand(text: str, slashreplace: bool = True) -> str:
    """
    Expands a path string by resolving '~', environment variables, and relative links.

    Args:
        text (str): The path to be expanded (e.g., "~/$PROJECT/./file.txt").
        slashreplace (bool): If True, returns backslashes on Windows. Defaults to True.

    Returns:
        str: The fully expanded and absolute path.
    """
    if not text:
        return ""

    # 1. Expand ~ and Environment Variables
    expanded = os.path.expandvars(os.path.expanduser(text))
    
    # 2. Convert to a Path object and make it absolute
    # .resolve() handles the "./" and "../" logic correctly
    path_obj = Path(expanded).resolve()

    # 3. Handle string conversion and slash preference
    if slashreplace and os.name == 'nt':
        # On Windows, this automatically uses backslashes
        return str(path_obj)
    
    # .as_posix() forces forward slashes (/) regardless of OS
    return path_obj.as_posix()

def load_yaml(path: Path) -> Optional[Dict[str, Any]]:
    """Safely loads a YAML file from the given path."""
    try:
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None

def dump_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Safely writes a dictionary to a YAML file, ensuring the directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def create_benchmark_yaml(path: str, n: int) -> None:
    """Creates a Cloudmesh service YAML test file with specified number of services."""
    cm = {"cloudmesh": {}}
    for i in range(0, n):
        cm["cloudmesh"][f"service{i}"] = {"attribute": f"service{i}"}
    
    location = path_expand(path)
    with open(location, "w") as yaml_file:
        yaml.dump(cm, yaml_file, default_flow_style=False)

def create_benchmark_file(path: str, n: int) -> int:
    """Creates a file of a given size in binary megabytes and returns the size in megabytes."""
    location = path_expand(path)
    size = 1048576 * n  # size in bytes
    with open(location, "wb") as f:
        f.write(os.urandom(size))
    
    s = os.path.getsize(location)
    return int(s / 1048576.0)
