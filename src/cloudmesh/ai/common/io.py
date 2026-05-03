"""
I/O utility functions and the unified Console for cloudmesh-ai.
Provides helpers for path expansion, YAML handling, and styled output.
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

import yaml
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.box import ROUNDED
from rich.align import Align
from rich.padding import Padding
from rich.table import Table
from rich.status import Status
from rich.markdown import Markdown

class Console(RichConsole):
    """Unified Console for cloudmesh-ai providing styled output, I/O, and table printing."""

    def error(self, message: str):
        """Prints an error message in red."""
        self.print(f"[red]ERROR: {message}[/red]")

    def warning(self, message: str):
        """Prints a warning message in yellow."""
        self.print(f"[yellow]WARNING: {message}[/yellow]")

    def msg(self, message: str):
        """Prints a message in blue."""
        self.print(f"[blue]MSG: {message}[/blue]")

    def info(self, message: str):
        """Prints an info message in magenta."""
        self.print(f"[magenta]INFO: {message}[/magenta]")

    def note(self, message: str):
        """Prints a note in cyan."""
        self.print(f"[cyan]NOTE: {message}[/cyan]")

    def ok(self, message: str):
        """Prints a success message in green."""
        self.print(f"[green]OK: {message}[/green]")

    def bold(self, message: str):
        """Prints a message in bold."""
        self.print(f"[bold]{message}[/bold]")

    def create_banner(self, title: str, content: Optional[str] = None) -> Panel:
        """Creates a banner Panel without printing it."""
        if not content and title:
            panel_content = Align.center(f"[bold magenta]{title}[/bold magenta]")
            styled_title = ""
        else:
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
        """Creates a banner with a title and optional content and prints it."""
        panel = self.create_banner(title, content)
        self.print(Padding(panel, padding))

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

    def print_attributes(self, d: Dict[str, Any], header: Optional[List[str]] = None, 
                         order: Optional[List[str]] = None, sort_keys: bool = True, 
                         humanize: bool = False, output: str = "table"):
        """Prints a dictionary of attributes in various formats.
        
        Args:
            d: The dictionary to print.
            header: Custom headers for the table.
            order: Specific order of keys.
            sort_keys: Whether to sort keys alphabetically.
            humanize: Whether to humanize values.
            output: Output format ("table", "json", "yaml", "csv").
        """
        if not d:
            self.print("No attributes to display.")
            return

        if output == "json":
            self.print_json(d)
            return
        if output == "yaml":
            self.print_yaml(d)
            return
        if output == "csv":
            self.print_csv(d, order)
            return

        # Default: Table output
        if header is None:
            header = ["Attribute", "Value"]

        table = Table(title="Attributes", box=ROUNDED, expand=True)
        table.add_column(header[0])
        table.add_column(header[1])

        sorted_keys = order if order else (sorted(d.keys()) if sort_keys else list(d.keys()))

        for key in sorted_keys:
            if key not in d:
                continue
            val = d[key]
            
            if humanize:
                val = self._humanize(val)

            if isinstance(val, dict):
                table.add_row(key, "+")
                for k, v in val.items():
                    table.add_row(f"  - {k}", str(v))
            elif isinstance(val, list):
                table.add_row(key, "+")
                for item in val:
                    table.add_row("  -", str(item))
            else:
                table.add_row(key, str(val or ""))

        self.print(table)

    def print_table(self, headers: list, data: list, title: Optional[str] = None):
        """Prints a formatted table."""
        table = Table(title=title, box=ROUNDED, expand=True)
        for header in headers:
            table.add_column(header)
        for row in data:
            table.add_row(*[str(item) for item in row])
        self.print(table)

    def print_json(self, data: Any):
        """Prints data as formatted JSON."""
        self.print(json.dumps(data, indent=4))

    def print_yaml(self, data: Any):
        """Prints data as formatted YAML."""
        self.print(yaml.dump(data, default_flow_style=False))

    def print_csv(self, d: Dict[str, Any], order: Optional[List[str]] = None):
        """Prints a dictionary as CSV."""
        keys = order if order else sorted(d.keys())
        output = []
        output.append(",".join(keys))
        row = [str(d.get(k, "")) for k in keys]
        output.append(",".join(row))
        self.print("\n".join(output))

    def print_markdown(self, text: str):
        """Renders and prints markdown text."""
        self.print(Markdown(text))

    def _humanize(self, value: Any) -> str:
        """Basic humanization of values."""
        if isinstance(value, (int, float)) and abs(value) >= 1000000:
            return f"{value/1000000:.2f}M"
        if isinstance(value, (int, float)) and abs(value) >= 1000:
            return f"{value/1000:.2f}K"
        return str(value)

    def status(self, message: str) -> Status:
        """Returns a status spinner context manager."""
        return Status(f"[bold blue]{message}[/bold blue]", console=self)

    def top(self, lines: int):
        """Moves the cursor up by the specified number of lines."""
        if lines > 0:
            sys.stdout.write(f"\033[{lines}F")
            sys.stdout.flush()

    def left(self):
        """Moves the cursor to the beginning of the current line."""
        sys.stdout.write("\r")
        sys.stdout.flush()

console = Console()

def banner(title: str, content: Optional[str] = None):
    """Standalone wrapper for console.banner."""
    console.banner(title, content)

async def async_readfile(path: str) -> str:
    """Asynchronously reads the content of a file."""
    import aiofiles
    async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
        return await f.read()

async def async_writefile(path: str, content: str) -> None:
    """Asynchronously writes content to a file."""
    import aiofiles
    from cloudmesh.ai.common.util import path_expand
    path_obj = Path(path_expand(path))
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path_obj, mode='w', encoding='utf-8') as f:
        await f.write(content)

def readfile(path: str) -> str:
    """Reads the content of a file."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def writefile(path: str, content: str) -> None:
    """Writes content to a file."""
    from cloudmesh.ai.common.util import path_expand
    path_obj = Path(path_expand(path))
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(content, encoding='utf-8')

def path_expand(text: str, slashreplace: bool = True) -> str:
    """Expands a path string by resolving '~', environment variables, and relative links."""
    if not text:
        return ""
    expanded = os.path.expandvars(os.path.expanduser(text))
    path_obj = Path(expanded).resolve()
    if slashreplace and os.name == 'nt':
        return str(path_obj)
    return path_obj.as_posix()

def load_yaml(path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Safely loads a YAML file from the given path."""
    path_obj = Path(path)
    try:
        if not path_obj.exists():
            return None
        with open(path_obj, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError):
        return None

def dump_yaml(path: Union[str, Path], data: Dict[str, Any]) -> None:
    """Safely writes a dictionary to a YAML file."""
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with open(path_obj, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False)

def create_benchmark_yaml(path: str, n: int) -> None:
    """Creates a Cloudmesh service YAML test file."""
    cm = {"cloudmesh": {}}
    for i in range(0, n):
        cm["cloudmesh"][f"service{i}"] = {"attribute": f"service{i}"}
    location = path_expand(path)
    with open(location, "w", encoding='utf-8') as yaml_file:
        yaml.dump(cm, yaml_file)

def create_benchmark_file(path: str, n: int) -> int:
    """Creates a file of a given size in binary megabytes."""
    location = path_expand(path)
    size = 1048576 * n
    with open(location, "wb") as f:
        f.write(os.urandom(size))
    return int(os.path.getsize(location) / 1048576.0)

class Editor:
    """Utility to open files in the default system editor."""
    def edit(self, path: str):
        expanded_path = path_expand(path)
        editor = os.environ.get("EDITOR")
        if os.name == 'posix':
            import subprocess
            try:
                if sys.platform == 'darwin':
                    cmd = ['open', '-a', editor, expanded_path] if editor and '/' not in editor else \
                          [editor, expanded_path] if editor else ['open', expanded_path]
                    subprocess.run(cmd, check=True)
                else:
                    cmd = [editor, expanded_path] if editor else ['xdg-open', expanded_path]
                    subprocess.run(cmd, check=True)
            except Exception as e:
                console.error(f"Failed to open editor: {e}")
        elif os.name == 'nt':
            try:
                if editor:
                    import subprocess
                    subprocess.run([editor, expanded_path], check=True)
                else:
                    os.startfile(expanded_path)
            except Exception as e:
                console.error(f"Failed to open editor: {e}")