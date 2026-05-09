# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

import yaml
import pyfiglet
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich import box
from rich.align import Align
from rich.padding import Padding
from rich.table import Table
from rich.status import Status
from rich.markdown import Markdown

from cloudmesh.ai.common.logging_utils import get_contextual_logger
from cloudmesh.ai.common.exceptions import IOReadError, IOWriteError

logger = get_contextual_logger("common.io")

class BaseIO:
    """Base class for I/O operations providing path expansion and file utilities."""

    def expand_path(self, text: str, slashreplace: bool = True) -> str:
        """Expands a path string by resolving '~', environment variables, and relative links."""
        if not text:
            return ""
        expanded = os.path.expandvars(os.path.expanduser(text))
        path_obj = Path(expanded).resolve()
        if slashreplace and os.name == 'nt':
            return str(path_obj)
        return path_obj.as_posix()

    def readfile(self, path: str) -> str:
        """Reads the content of a file."""
        try:
            location = self.expand_path(path)
            with open(location, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            raise IOReadError(f"Could not read file {path}: {e}")

    def writefile(self, path: str, content: str) -> None:
        """Writes content to a file."""
        try:
            location = self.expand_path(path)
            path_obj = Path(location)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            path_obj.write_text(content, encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            raise IOWriteError(f"Could not write file {path}: {e}")

    def appendfile(self, path: str, content: str) -> None:
        """Appends content to a file."""
        try:
            location = self.expand_path(path)
            path_obj = Path(location)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(path_obj, "a", encoding="utf-8") as outfile:
                outfile.write(content)
        except Exception as e:
            logger.error(f"Failed to append to file {path}: {e}")
            raise IOWriteError(f"Could not append to file {path}: {e}")

    def load_yaml(self, path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Safely loads a YAML file from the given path."""
        try:
            location = self.expand_path(str(path))
            path_obj = Path(location)
            if not path_obj.exists():
                return None
            with open(path_obj, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"YAML load error for {path}: {e}")
            return None

    def dump_yaml(self, path: Union[str, Path], data: Dict[str, Any]) -> None:
        """Safely writes a dictionary to a YAML file."""
        try:
            location = self.expand_path(str(path))
            path_obj = Path(location)
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with open(path_obj, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"YAML dump error for {path}: {e}")
            raise IOWriteError(f"Could not dump YAML to {path}: {e}")

class Console(BaseIO, RichConsole):
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
            box=box.ROUNDED,
            expand=True,
            border_style="bold blue"
        )

    def banner(
        self,
        label: Optional[str] = None,
        txt: Optional[str] = None,
        c: str = "-",
        prefix: str = "#",
        debug: bool = True,
        color: str = "blue",
        padding: bool = False,
        figlet: bool = False,
        font: str = "big",
    ) -> None:
        """Prints a banner of the form with a frame of # around the txt"""
        if not debug:
            return

        output = "\n"
        output += f"{prefix} {70 * c}\n"
        if padding:
            output += f"{prefix}\n"
        if label is not None:
            output += f"{prefix} {label}\n"
            output += f"{prefix} {70 * c}\n"

        if txt is not None:
            if figlet:
                txt = pyfiglet.figlet_format(txt, font=font)

            for line in txt.splitlines():
                output += f"{prefix} {line}\n"
            if padding:
                output += f"{prefix}\n"
            output += f"{prefix} {70 * c}\n"

        self.cprint(output, color, "")

    def cprint(self, text: str, color: str, style: str = ""):
        """Helper to print with color."""
        self.print(f"[{color}]{text}[/{color}]", style=style)

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
        """Prints a dictionary of attributes in various formats."""
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

        table = Table(title="Attributes", box=box.ROUNDED, expand=True)
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

    def print_table(self, headers: list, data: list, title: Optional[str] = None, expand: bool = False):
        """Prints a formatted table. By default, it is compact (expand=False)."""
        styled_title = f"[bold]{title}[/bold]" if title else None
        table = Table(title=styled_title, box=box.ROUNDED, expand=expand, header_style="bold")
        for header in headers:
            table.add_column(header)
        for row in data:
            table.add_row(*[str(item) for item in row])
        self.print(Align.center(table) if expand else Align.left(table))

    table = print_table

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

    def ai_response(self, text: str, title: str = "AI Response", style: str = "cyan"):
        """Displays a standardized AI response box."""
        panel = Panel(
            text,
            title=title,
            title_style=style,
            border_style=style,
            expand=False,
            box=box.ROUNDED
        )
        self.print(panel)

    def telemetry_table(self, records: List[Dict[str, Any]], title: str = "Telemetry Records"):
        """Displays a standardized telemetry records table."""
        if not records:
            self.print("[yellow]No records to display.[/yellow]")
            return

        table = Table(
            title=title,
            box=box.ROUNDED,
            header_style="bold magenta"
        )
        
        headers = records[0].keys()
        for header in headers:
            table.add_column(header.capitalize(), style="cyan")

        for r in records:
            row = [str(r.get(h, "N/A")) for h in headers]
            table.add_row(*row)

        self.print(table)

    def print_status(self, message: str, style: str = "yellow"):
        """Prints a simple status message."""
        self.print(f"[{style}] {message}[/{style}]")

    def print_error(self, message: str):
        """Prints a standardized error message."""
        self.print(f"[bold red]Error:[/bold red] {message}")

    def print_success(self, message: str):
        """Prints a standardized success message."""
        self.print(f"[bold green]Success:[/bold green] {message}")

class Editor(BaseIO):
    """Utility to open files in the default system editor."""
    def edit(self, path: str):
        expanded_path = self.expand_path(path)
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
                logger.error(f"Failed to open editor: {e}")
        elif os.name == 'nt':
            try:
                if editor:
                    import subprocess
                    subprocess.run([editor, expanded_path], check=True)
                else:
                    os.startfile(expanded_path)
            except Exception as e:
                logger.error(f"Failed to open editor: {e}")

# Singleton instance for backward compatibility
console = Console()

def banner(
    label: Optional[str] = None,
    txt: Optional[str] = None,
    c: str = "-",
    prefix: str = "#",
    debug: bool = True,
    color: str = "blue",
    padding: bool = False,
    figlet: bool = False,
    font: str = "big",
):
    """Standalone wrapper for console.banner."""
    console.banner(
        label=label,
        txt=txt,
        c=c,
        prefix=prefix,
        debug=debug,
        color=color,
        padding=padding,
        figlet=figlet,
        font=font,
    )

def readfile(path: str) -> str:
    """Standalone wrapper for console.readfile."""
    return console.readfile(path)

def writefile(path: str, content: str) -> None:
    """Standalone wrapper for console.writefile."""
    console.writefile(path, content)

def appendfile(path: str, content: str) -> None:
    """Standalone wrapper for console.appendfile."""
    console.appendfile(path, content)

def path_expand(text: str, slashreplace: bool = True) -> str:
    """Standalone wrapper for console.expand_path."""
    return console.expand_path(text, slashreplace)

def load_yaml(path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """Standalone wrapper for console.load_yaml."""
    return console.load_yaml(path)

def dump_yaml(path: Union[str, Path], data: Dict[str, Any]) -> None:
    """Standalone wrapper for console.dump_yaml."""
    console.dump_yaml(path, data)

def create_benchmark_yaml(path: str, n: int) -> None:
    """Creates a Cloudmesh service YAML test file."""
    cm = {"cloudmesh": {}}
    for i in range(0, n):
        cm["cloudmesh"][f"service{i}"] = {"attribute": f"service{i}"}
    console.dump_yaml(path, cm)

def create_benchmark_file(path: str, n: int) -> int:
    """Creates a file of a given size in binary megabytes."""
    location = console.expand_path(path)
    size = 1048576 * n
    with open(location, "wb") as f:
        f.write(os.urandom(size))
    return int(os.path.getsize(location) / 1048576.0)

async def async_readfile(path: str) -> str:
    """Asynchronously reads the content of a file."""
    import aiofiles
    async with aiofiles.open(path, mode='r', encoding='utf-8') as f:
        return await f.read()

async def async_writefile(path: str, content: str) -> None:
    """Asynchronously writes content to a file."""
    import aiofiles
    location = console.expand_path(path)
    path_obj = Path(location)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path_obj, mode='w', encoding='utf-8') as f:
        await f.write(content)