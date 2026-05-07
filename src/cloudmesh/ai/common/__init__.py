"""
Unified entry point for cloudmesh-ai-common.
Exports the most commonly used utilities for easier access.
"""

from cloudmesh.ai.common.io import console, Console, readfile, writefile, path_expand, banner
from cloudmesh.ai.common.flatdict import flatten
from cloudmesh.ai.common.util import backup_name, yn_choice, HEADING
from cloudmesh.ai.common.dotdict import DotDict
from cloudmesh.ai.common.sys import systeminfo as SystemInfo
from cloudmesh.ai.common.DateTime import DateTime
time = DateTime
from cloudmesh.ai.common.Shell import Shell
from cloudmesh.ai.common.debug import VERBOSE

__all__ = [
    "console",
    "Console",
    "readfile",
    "writefile",
    "path_expand",
    "banner",
    "flatten",
    "backup_name",
    "yn_choice",
    "HEADING",
    "DotDict",
    "SystemInfo",
    "DateTime",
    "time",
    "Shell",
    "VERBOSE",
]