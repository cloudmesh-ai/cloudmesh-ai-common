import collections
import csv
import glob
import inspect
import os
import platform
import random
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Mapping, Iterable
from contextlib import contextmanager
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

import requests
from cloudmesh.ai.common.io import console as Console, path_expand, banner


@contextmanager
def tempdir(*args, **kwargs) -> Path:
    """A contextmanager to work in an auto-removed temporary directory

    Arguments are passed through to tempfile.mkdtemp
    """
    d = Path(tempfile.mkdtemp(*args, **kwargs))
    try:
        yield d
    finally:
        shutil.rmtree(d)


def check_root(dryrun: bool = False, terminate: bool = True) -> None:
    """check if I am the root user. If not, simply exits the program.

    Args:
        dryrun (bool): if set to true, does not terminate if not root user
        terminate (bool): terminates if not root user and dryrun is False
    """
    try:
        uid = os.getuid()
    except AttributeError:
        uid = -1  # Not on a POSIX system

    if uid == 0:
        Console.ok("You are executing as a root user")
    else:
        Console.error("You do not run as root")
        if terminate and not dryrun:
            sys.exit()


def exponential_backoff(fn, sleeptime_s_max: int = 30 * 60) -> bool:
    """Calls `fn` until it returns True, with an exponentially increasing wait time between calls

    Args:
        fn (callable): the function to be called that returns True or False
        sleeptime_s_max (int): the maximum sleep time in seconds

    Returns:
        bool: True if fn() returned True, False if max sleep time was reached
    """
    sleeptime_ms = 500
    while True:
        if fn():
            return True
        else:
            print(f"Sleeping {sleeptime_ms} ms")
            time.sleep(sleeptime_ms / 1000.0)
            sleeptime_ms *= 2

        if sleeptime_ms / 1000.0 > sleeptime_s_max:
            return False


def download(source: str, destination: Union[str, Path], force: bool = False) -> None:
    """Downloads the file from source to destination

    Args:
        source: The http source
        destination: The destination in the file system
        force: If True the file will be downloaded even if it already exists
    """
    dest_path = Path(destination)
    if dest_path.exists() and not force:
        Console.warning(f"File {dest_path} already exists. Skipping download ...")
    else:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(source, allow_redirects=True)
        dest_path.write_bytes(r.content)


def csv_to_list(csv_string: str, sep: str = ",") -> List[List[str]]:
    """Converts a CSV table from a string to a list of lists

    Args:
        csv_string (string): The CSV table
        sep (string): The separator

    Returns:
        list: list of lists
    """
    reader = csv.reader(csv_string.splitlines(), delimiter=sep)
    return list(reader)


def search(lines: List[str], pattern: str) -> List[str]:
    """return all lines that match the pattern

    Args:
        lines: list of strings to search
        pattern: the pattern to search for (supports * as wildcard)

    Returns:
        list: matching lines
    """
    p = pattern.replace("*", ".*")
    test = re.compile(p)
    return [l for l in lines if test.search(l)]


def grep(pattern: str, filename: Union[str, Path]) -> str:
    """Very simple grep that returns the first matching line in a file.

    Args:
        pattern: the pattern to search for
        filename: the file to search in

    Returns:
        str: the first matching line or empty string
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return next((L for L in f if pattern in L), "")
    except (StopIteration, OSError):
        return ""


def is_local(host: str) -> bool:
    """Checks if the host is the localhost

    Args:
        host: The hostname or ip

    Returns:
        bool: True if local, False otherwise
    """
    return host in [
        "127.0.0.1",
        "localhost",
        socket.gethostname(),
        platform.node(),
    ]


def is_gitbash() -> bool:
    """returns True if you run in a Windows gitbash"""
    try:
        return "Git" in os.environ.get("EXEPATH", "")
    except Exception:
        return False


def is_powershell() -> bool:
    """True if you run in powershell"""
    if platform.system() == "Windows":
        try:
            import psutil
            return psutil.Process(os.getppid()).name() == "powershell.exe"
        except ImportError:
            return False
    return False


def is_cmd_exe() -> bool:
    """return True if you run in a Windows CMD"""
    if is_gitbash():
        return False
    return os.environ.get("OS") == "Windows_NT"




def convert_from_unicode(data: Any) -> Any:
    """Converts unicode data to a string"""
    if isinstance(data, str):
        return str(data)
    elif isinstance(data, Mapping):
        return {k: convert_from_unicode(v) for k, v in data.items()}
    elif isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
        return type(data)(map(convert_from_unicode, data))
    else:
        return data


def yn_choice(message: str, default: str = "y", tries: Optional[int] = None) -> bool:
    """asks for a yes/no question.

    Args:
        message: the message containing the question
        default: the default answer
        tries: the number of tries
    """
    choices = "Y/n" if default.lower() in ("y", "yes") else "y/N"
    if tries is None:
        choice = input(f"{message} ({choices}) ")
        values = ("y", "yes", "") if default == "y" else ("y", "yes")
        return choice.strip().lower() in values
    else:
        while tries > 0:
            choice = input(f"{message} ({choices}) ('q' to discard)").strip().lower()
            if choice in ("y", "yes"):
                return True
            elif choice in ("n", "no", "q"):
                return False
            print("Invalid input...")
            tries -= 1
        return False




def HEADING(txt: Optional[str] = None, c: str = "#", color: str = "magenta") -> None:
    """Prints a message to stdout with #### surrounding it."""
    frame = inspect.getouterframes(inspect.currentframe())
    filename = frame[1][1].replace(os.getcwd(), "")
    line = frame[1][2] - 1
    method = frame[1][3]
    
    if txt is None:
        msg = f"{method} {filename} {line}"
    else:
        msg = f"{txt}\n {method} {filename} {line}"

    print()
    banner(msg, c=c, color=color)


def FUNCTIONNAME() -> str:
    """Returns the name of a function."""
    frame = inspect.getouterframes(inspect.currentframe())
    return frame[1][3]


def backup_name(filename: Union[str, Path]) -> str:
    """creates a backup name of the form filename.bak.1"""
    location = Path(path_expand(str(filename)))
    n = 0
    while True:
        n += 1
        backup = location.with_suffix(f"{location.suffix}.bak.{n}")
        if not backup.exists():
            return str(backup)


def auto_create_version(class_name: str, version: str, filename: str = "__init__.py") -> None:
    """creates a version number in the __init__.py file."""
    version_filename = Path(class_name) / filename
    if version_filename.exists():
        content = version_filename.read_text()
        if content != f'__version__ = "{version}"':
            banner(f"Updating version to {version}")
            version_filename.write_text(f'__version__ = "{version}"')


def auto_create_requirements(requirements: List[str]) -> None:
    """creates a requirement.txt file from the requirements in the list."""
    banner("Creating requirements.txt file")
    req_file = Path("requirements.txt")
    file_content = req_file.read_text() if req_file.exists() else ""
    setup_requirements = "\n".join(requirements)

    if setup_requirements != file_content:
        req_file.write_text(setup_requirements)


def copy_files(files_glob: str, source_dir: Union[str, Path], dest_dir: Union[str, Path]) -> None:
    """copies the files to the destination"""
    src = Path(source_dir)
    dst = Path(dest_dir)
    dst.mkdir(parents=True, exist_ok=True)
    for filename in src.glob(files_glob):
        shutil.copy2(filename, dst)




def writefd(filename: str, content: str, mode: str = "w", flags: int = os.O_RDWR | os.O_CREAT, mask: int = 0o600) -> None:
    """writes the content into the file and control permissions"""
    if mode not in ("w", "wb"):
        Console.error(f"incorrect mode : expected 'w' or 'wb' given {mode}")

    with os.fdopen(os.open(filename, flags, mask), mode) as outfile:
        outfile.write(content)
        outfile.truncate()




def generate_password(length: int = 8, lower: bool = True, upper: bool = True, number: bool = True) -> str:
    """generates a simple password."""
    lletters = "abcdefghijklmnopqrstuvwxyz"
    uletters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    alphabet = lletters + uletters if lower and upper else (lletters if lower else uletters)
    digit = "0123456789"
    mypw = ""

    for i in range(length):
        if number and i >= int(length / 2):
            mypw += random.choice(digit)
        else:
            mypw += random.choice(alphabet)
    return mypw


def str_bool(value: Any) -> bool:
    return str(value).lower() in ("yes", "1", "y", "true", "t")


def get_password(prompt: str) -> str:
    """gets a password from the user securely"""
    from cloudmesh.ai.common.sys import os_is_windows

    try:
        if os_is_windows() and is_gitbash():
            while True:
                sys.stdout.write(prompt)
                sys.stdout.flush()
                subprocess.check_call(["stty", "-echo"])
                password = input()
                subprocess.check_call(["stty", "echo"])
                sys.stdout.write("Please retype the password:\n")
                sys.stdout.flush()
                subprocess.check_call(["stty", "-echo"])
                password2 = input()
                subprocess.check_call(["stty", "echo"])
                if password == password2:
                    return password
                Console.error("Passwords do not match\n")
        else:
            while True:
                password = getpass(prompt)
                password2 = getpass("Please retype the password:\n")
                if password == password2:
                    return password
                Console.error("Passwords do not match\n")
    except KeyboardInterrupt:
        if is_gitbash():
            subprocess.check_call(["stty", "-echo"])
        raise ValueError("Detected Ctrl + C. Quitting...")


