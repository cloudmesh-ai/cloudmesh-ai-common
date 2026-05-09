"""A convenient method to execute shell commands and return their output."""
import os
import platform as os_platform
import subprocess
import sys
import textwrap
import webbrowser
import shutil
from pathlib import Path
from sys import platform

import psutil
import requests
from cloudmesh.ai.common.io import Console
from cloudmesh.ai.common.dotdict import DotDict
from cloudmesh.ai.common.sys import get_platform, os_is_linux, os_is_mac, os_is_windows
from cloudmesh.ai.common.util import is_gitbash
from cloudmesh.ai.common.io import path_expand
from cloudmesh.ai.common.io import readfile, writefile

import shlex
import re
from shlex import quote


def windows_not_supported(f):
    """
    This is a decorator function that checks if the current platform is Windows.
    If it is, it prints an error message and returns an empty string.
    """
    def wrapper(*args, **kwargs):
        host = get_platform()
        if host == "windows":
            Console.error("Not supported on windows")
            return ""
        else:
            return f(*args, **kwargs)
    return wrapper


class SubprocessError(Exception):
    """Manages the formatting of the error and stdout."""
    def __init__(self, cmd, returncode, stderr, stdout):
        self.cmd = cmd
        self.returncode = returncode
        self.stderr = stderr
        self.stdout = stdout

    def __str__(self):
        def indent(lines, amount, ch=" "):
            padding = amount * ch
            return padding + ("\n" + padding).join(lines.split("\n"))

        cmd = " ".join(map(quote, self.cmd))
        s = ""
        s += "Command: %s\n" % cmd
        s += "Exit code: %s\n" % self.returncode

        if self.stderr:
            s += "Stderr:\n" + indent(self.stderr, 4)
        if self.stdout:
            s += "Stdout:\n" + indent(self.stdout, 4)
        return s


class Shell(object):
    """The shell class allowing us to conveniently access many operating system commands."""

    @staticmethod
    def _filter_noise(text: str) -> str:
        """Filters out common SSH noise and warnings from the output."""
        if not text:
            return ""
        
        noise_patterns = {
            "** WARNING: connection is not using a post-quantum key exchange algorithm.",
            "** This session may be vulnerable to \"store now, decrypt later\" attacks.",
            "** The server may need to be upgraded. See https://openssh.com/pq.html"
        }
        
        lines = text.splitlines()
        filtered_lines = []
        
        for line in lines:
            if line.strip() in noise_patterns:
                continue
            filtered_lines.append(line)
        
        return "\n".join(filtered_lines).strip()

    @staticmethod
    def run(command, exitcode="", encoding="utf-8", replace=True, timeout=None):
        """executes the command and returns the output as string"""
        if sys.platform == "win32":
            if replace:
                c = "&"
            else:
                c = ";"
            command = f"{command}".replace(";", c)
        elif exitcode:
            command = f"{command} {exitcode}"

        try:
            if timeout is not None:
                r = subprocess.check_output(
                    command, stderr=subprocess.STDOUT, shell=True, timeout=timeout
                )
            else:
                r = subprocess.check_output(
                    command, stderr=subprocess.STDOUT, shell=True
                )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"{e.returncode} {e.output.decode()}")
        
        if encoding is None or encoding == "utf-8":
            result = str(r, "utf-8")
            return Shell._filter_noise(result)
        else:
            return r

    @classmethod
    def execute(
        cls, cmd, arguments="", shell=False, cwd=None, traceflag=True, witherror=True
    ):
        """Run Shell command"""
        result = None
        os_command = [cmd]
        
        if isinstance(arguments, list):
            os_command = os_command + arguments
        elif isinstance(arguments, tuple):
            os_command = os_command + list(arguments)
        elif isinstance(arguments, str):
            os_command = os_command + arguments.split()
        
        if cwd is None:
            cwd = os.getcwd()
            
        try:
            if shell:
                result = subprocess.check_output(
                    os_command, stderr=subprocess.STDOUT, shell=True, cwd=cwd
                )
            else:
                result = subprocess.check_output(
                    os_command, stderr=subprocess.STDOUT, cwd=cwd,
                )
        except Exception:
            if witherror:
                Console.error("problem executing subprocess", traceflag=traceflag)
        
        if result is not None:
            result = result.strip().decode()
        return result

    @staticmethod
    def live(command):
        """Executes a command and prints output in real time"""
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        output = []
        for line in process.stdout:
            print(line, end="")
            output.append(line)
        process.wait()
        return "".join(output)

    @staticmethod
    def browser(filename=None):
        """Opens a file or URL in the browser"""
        if not os.path.isabs(filename) and "http" not in filename:
            # Minimal map_filename implementation
            filename = os.path.abspath(filename)
        webbrowser.open(filename, new=2, autoraise=False)

    @staticmethod
    def rm(top):
        """Removes a directory tree"""
        p = Path(top)
        if not p.exists():
            return
        try:
            shutil.rmtree(p)
        except Exception as e:
            print(e)

    @staticmethod
    def install_chocolatey():
        """Install chocolatey windows package manager"""
        if not os_is_windows():
            Console.error("chocolatey can only be installed in Windows")
            return False
        try:
            Shell.run("choco --version")
            Console.ok("Chocolatey already installed")
            return True
        except RuntimeError:
            Console.msg("Installing chocolatey...")
            # Minimal implementation: assume user has admin or handles it
            url = "https://raw.githubusercontent.com/cloudmesh/cloudmesh-common/main/src/cloudmesh/common/bin/win-setup.bat"
            response = requests.get(url)
            if response.status_code == 200:
                bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bin")
                os.makedirs(bin_dir, exist_ok=True)
                with open(os.path.join(bin_dir, "win-setup.bat"), "w") as f:
                    f.write(response.text)
                subprocess.run(f"powershell Start-Process -Wait -FilePath '{os.path.join(bin_dir, 'win-setup.bat')}'", shell=True)
                Console.ok("Chocolatey installed")
                return True
            return False

    @staticmethod
    def install_brew():
        """Installs Homebrew on macOS"""
        if not os_is_mac():
            Console.error("Homebrew can only be installed on mac")
            return False
        try:
            subprocess.check_output("brew --version", stderr=subprocess.STDOUT, shell=True)
            Console.ok("Homebrew already installed")
            return True
        except subprocess.CalledProcessError:
            Console.info("Installing Homebrew...")
            command = 'osascript -e \'tell application "Terminal" to do script "/bin/bash -c \\"export NONINTERACTIVE=1 ; $(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\\""\''
            subprocess.run(command, shell=True, check=True)
            return True