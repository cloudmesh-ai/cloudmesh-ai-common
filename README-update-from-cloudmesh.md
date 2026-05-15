# Migration Guide for Redundancy Reduction

This document tracks the changes made to reduce redundancies in `cloudmesh-ai-common`. For every improvement, the "Old Way" and "New Way" are documented here to guide programs that need to be updated.

## System Information
**Change**: Merge `systeminfo.py` into `sys.py`.
- **Old Way**: `from cloudmesh.ai.common import systeminfo`
- **New Way**: `from cloudmesh.ai.common import sys`

## Sudo Utilities
**Change**: Merge `sudo.py` into `security.py`.
- **Old Way**: `from cloudmesh.ai.common import sudo`
- **New Way**: `from cloudmesh.ai.common.security import Sudo`

## IO & Utilities
**Change**: Consolidate `path_expand()` and `banner()` into `io.py`.
- **Old Way**: `from cloudmesh.ai.common import util` $\rightarrow$ `util.path_expand()` / `util.banner()`
- **New Way**: `from cloudmesh.ai.common import io` $\rightarrow$ `io.path_expand()` / `io.console.banner()`

**Change**: Consolidate `appendfile()` and `writefile()` into `io.py`.
- **Old Way**: `util.appendfile()` / `util.writefile()`
- **New Way**: `from cloudmesh.ai.common import io` $\rightarrow$ `io.appendfile()` / `io.writefile()`

**Change**: Consolidate `sudo_readfile()` into `security.py`.
- **Old Way**: `util.sudo_readfile()`
- **New Way**: `Sudo().readfile()`

## Dictionary Flattening
**Change**: Remove `flatten()` from `util.py`.
- **Old Way**: `from cloudmesh.ai.common import util` $\rightarrow$ `util.flatten()`
- **New Way**: `from cloudmesh.ai.common import flatdict` $\rightarrow$ `flatdict.flatten()`

## SSH Configuration
**Change**: Consolidate `ssh.py` into `ssh/ssh_config.py` and introduce a package facade.
- **Old Way**: `from cloudmesh.ai.common import ssh` $\rightarrow$ `ssh.SSHConfig()`
- **New Way**: `from cloudmesh.ai.common.ssh import SSHConfig` $\rightarrow$ `SSHConfig()`

**Change**: Rename `ssh/encrypt.py` to `ssh/encryption.py` and `EncryptFile` to `SSHEncryption`.
- **Old Way**: `from cloudmesh.ai.common.ssh import encrypt` $\rightarrow$ `encrypt.EncryptFile()`
- **New Way**: `from cloudmesh.ai.common.ssh import SSHEncryption` $\rightarrow$ `SSHEncryption()`

## Time/Date
**Change**: Merge `time.py` into `DateTime.py`.
- **Old Way**: `from cloudmesh.ai.common import time`
- **New Way**: `from cloudmesh.ai.common import DateTime`

## UI/Console
**Change**: Consolidate `ui.py` functions into `io.py`'s `Console` class.
- **Old Way**: `from cloudmesh.ai.common import ui` $\rightarrow$ `ui.ai_response()` / `ui.print_error()`
- **New Way**: `from cloudmesh.ai.common.io import console` $\rightarrow$ `console.ai_response()` / `console.print_error()`
