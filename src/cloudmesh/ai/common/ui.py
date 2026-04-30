# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

def ai_response(text: str, title: str = "AI Response", style: str = "cyan"):
    """Displays a standardized AI response box.

    Args:
        text: The response text to display.
        title: The title of the response box. Defaults to "AI Response".
        style: The color style for the box. Defaults to "cyan".
    """
    panel = Panel(
        text,
        title=title,
        title_style=style,
        border_style=style,
        expand=False,
        box=box.ROUNDED
    )
    console.print(panel)

def telemetry_table(records: List[Dict[str, Any]], title: str = "Telemetry Records"):
    """Displays a standardized telemetry records table.

    Args:
        records: A list of telemetry records (dictionaries) to display.
        title: The title of the table. Defaults to "Telemetry Records".
    """
    if not records:
        console.print("[yellow]No records to display.[/yellow]")
        return

    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold magenta"
    )
    
    # Use keys from the first record as headers
    headers = records[0].keys()
    for header in headers:
        table.add_column(header.capitalize(), style="cyan")

    for r in records:
        row = [str(r.get(h, "N/A")) for h in headers]
        table.add_row(*row)

    console.print(table)

def print_status(message: str, style: str = "yellow"):
    """Prints a simple status message.

    Args:
        message: The status message to print.
        style: The color style for the message. Defaults to "yellow".
    """
    console.print(f"[{style}] {message}[/{style}]")

def print_error(message: str):
    """Prints a standardized error message.

    Args:
        message: The error message to print.
    """
    console.print(f"[bold red]Error:[/bold red] {message}")

def print_success(message: str):
    """Prints a standardized success message.

    Args:
        message: The success message to print.
    """
    console.print(f"[bold green]Success:[/bold green] {message}")