"""
I/O utility functions for cloudmesh-ai.
Provides helpers for path expansion, YAML handling, and benchmark file creation.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

import paramiko
from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED

class AIConsole(Console):
    """Custom Console with convenience methods for styled output."""

    def error(self, message: str):
        """Prints an error message in red."""
        self.print(f"[red]ERROR: {message}[/red]")

    def warning(self, message: str):
        """Prints a warning message in yellow."""
        self.print(f"[yellow]WARNING: {message}[/yellow]")

    def msg(self, message: str):
        """Prints a message in blue."""
        self.print(f"[blue]MSG: {message}[/blue]")

    def note(self, message: str):
        """Prints a note in cyan."""
        self.print(f"[cyan]NOTE: {message}[/cyan]")

console = AIConsole()

class SSHClient:
    """Simple wrapper around paramiko.SSHClient for executing remote commands."""

    def __init__(self, host: str, username: Optional[str] = None):
        self.host = host
        self.username = username
        self.client = None

    def __enter__(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, username=self.username)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()

    def execute(self, command: str) -> str:
        """Executes a command on the remote host and returns the stdout."""
        stdin, stdout, stderr = self.client.exec_command(command)
        return stdout.read().decode('utf-8')

def readfile(path: str) -> str:
    """Reads the content of a file.
    
    Args:
        path: Path to the file.
        
    Returns:
        The content of the file as a string.
    """
    with open(path, 'r') as f:
        return f.read()

def path_expand(text: str, slashreplace: bool = True) -> str:
    """Expands a path string by resolving '~', environment variables, and relative links.

    Args:
        text: The path to be expanded (e.g., "~/$PROJECT/./file.txt").
        slashreplace: If True, returns backslashes on Windows. Defaults to True.

    Returns:
        The fully expanded and absolute path.
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
    """Safely loads a YAML file from the given path.

    Args:
        path: Path to the YAML file.

    Returns:
        The loaded YAML data as a dictionary, or None if the file does not exist 
        or an error occurs.
    """
    try:
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None

def dump_yaml(path: Path, data: Dict[str, Any]) -> None:
    """Safely writes a dictionary to a YAML file, ensuring the directory exists.

    Args:
        path: Path where the YAML file should be written.
        data: The dictionary to write to the file.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)

def create_benchmark_yaml(path: str, n: int) -> None:
    """Creates a Cloudmesh service YAML test file with specified number of services.

    Args:
        path: Path where the benchmark YAML should be created.
        n: Number of services to include in the benchmark file.

    """
    cm = {"cloudmesh": {}}
    for i in range(0, n):
        cm["cloudmesh"][f"service{i}"] = {"attribute": f"service{i}"}
    
    location = path_expand(path)
    with open(location, "w") as yaml_file:
        yaml.dump(cm, yaml_file, default_flow_style=False)

def banner(title: str, content: Optional[str] = None):
    """
    Creates a banner with a title and optional content using a rich Panel.
    Returns the Panel object.
    """
    # If content is None, we use an empty string to ensure the panel renders
    panel_content = content if content else ""
    
    # We use markup in the title to set the style since title_style is not a valid argument
    styled_title = f"[bold magenta]{title}[/bold magenta]" if title else ""
    panel = Panel(
        panel_content,
        title=styled_title,
        box=ROUNDED,
        expand=True,
        border_style="bold blue"
    )
    
    return panel

def create_benchmark_file(path: str, n: int) -> int:
    """Creates a file of a given size in binary megabytes.

    Args:
        path: Path where the benchmark file should be created.
        n: Size of the file in megabytes.

    Returns:
        The actual size of the created file in megabytes.
    """
    location = path_expand(path)
    size = 1048576 * n  # size in bytes
    with open(location, "wb") as f:
        f.write(os.urandom(size))
    
    s = os.path.getsize(location)
    return int(s / 1048576.0)