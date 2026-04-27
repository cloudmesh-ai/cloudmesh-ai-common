"""
I/O utility functions for cloudmesh-ai.
Provides helpers for path expansion, YAML handling, and benchmark file creation.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

import paramiko
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.box import ROUNDED
from rich.padding import Padding
from rich.table import Table
from rich.status import Status

class Console(RichConsole):
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

    def ok(self, message: str):
        """Prints a success message in green."""
        self.print(f"[green]OK: {message}[/green]")

    def bold(self, message: str):
        """Prints a message in bold."""
        self.print(f"[bold]{message}[/bold]")

    def create_banner(self, title: str, content: Optional[str] = None):
        """
        Creates a banner Panel without printing it.
        """
        panel_content = content if content else ""
        styled_title = f"[bold magenta]{title}[/bold magenta]" if title else ""
        return Panel(
            panel_content,
            title=styled_title,
            box=ROUNDED,
            expand=True,
            border_style="bold blue"
        )

    def banner(self, title: str, content: Optional[str] = None, padding: tuple = (0, 0, 0, 2)):
        """
        Creates a banner with a title and optional content using a rich Panel and prints it.
        """
        panel = self.create_banner(title, content)
        self.print(Padding(panel, padding))

    def table(self, headers: list, data: list, title: Optional[str] = None):
        """
        Prints a formatted table.
        Args:
            headers: List of column headers.
            data: List of rows (each row is a list/tuple of values).
            title: Optional title for the table.
        """
        table = Table(title=title, box=ROUNDED, expand=True)
        for header in headers:
            table.add_column(header)
        
        for row in data:
            table.add_row(*[str(item) for item in row])
        
        self.print(table)

    def status(self, message: str):
        """
        Returns a status spinner context manager.
        Usage: with console.status("Loading..."):
        """
        return Status(f"[bold blue]{message}[/bold blue]", console=self)

    def ynchoice(self, message: str, default: bool = True) -> bool:
        """Asks a yes/no question and returns a boolean."""
        suffix = " [Y/n]" if default else " [y/N]"
        while True:
            response = input(f"{message}{suffix} ").strip().lower()
            if not response:
                return default
            if response in ("y", "yes"):
                return True
            if response in ("n", "no"):
                return False
            self.print("[red]Please enter 'y' or 'n'.[/red]")

console = Console()

def banner(title: str, content: Optional[str] = None):
    """Standalone wrapper for console.banner to maintain backward compatibility."""
    console.banner(title, content)

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