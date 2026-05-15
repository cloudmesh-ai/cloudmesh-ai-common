# Migration Guide for Redundancy Reduction

This document tracks the changes made to transition smoothly from `cloudmesh-common` to `cloudmesh-ai-common`. We have significantly improved the import paths for several packages. Common transitions are documented here using the labels "Old: common:" and "New: common-ai:" to guide updates for existing programs.

Please not if needed you can still use `cloudmesh.common`, but you shoudl upgrade to `cloudmesh-ai-common`.

## System Information

**Change**: Merge `systeminfo.py` into `sys.py`.

- **Old: common**: `from cloudmesh.ai.common import systeminfo`
- **New: common-ai:**: `from cloudmesh.ai.common import sys`

## Sudo Utilities
**Change**: Merge `sudo.py` into `security.py`.

- **Old: common**: `from cloudmesh.ai.common import sudo`
- **New: common-ai:**: `from cloudmesh.ai.common.security import Sudo`

## IO & Utilities
**Change**: Consolidate `path_expand()` and `banner()` into `io.py`.

- **Old: common**: `from cloudmesh.ai.common import util` $\rightarrow$ `util.path_expand()` / `util.banner()`
- **New: common-ai:**: `from cloudmesh.ai.common import io` $\rightarrow$ `io.path_expand()` / `io.console.banner()`

**Change**: Consolidate `appendfile()` and `writefile()` into `io.py`.

- **Old: common**: `util.appendfile()` / `util.writefile()`
- **New: common-ai:**: `from cloudmesh.ai.common import io` $\rightarrow$ `io.appendfile()` / `io.writefile()`

**Change**: Consolidate `sudo_readfile()` into `security.py`.

- **Old: common**: `util.sudo_readfile()`
- **New: common-ai:**: `Sudo().readfile()`

## Dictionary Flattening
**Change**: Remove `flatten()` from `util.py`.

- **Old: common**: `from cloudmesh.ai.common import util` $\rightarrow$ `util.flatten()`
- **New: common-ai:**: `from cloudmesh.ai.common import flatdict` $\rightarrow$ `flatdict.flatten()`

## SSH Configuration
**Change**: Consolidate `ssh.py` into `ssh/ssh_config.py` and introduce a package facade.

- **Old: common**: `from cloudmesh.ai.common import ssh` $\rightarrow$ `ssh.SSHConfig()`
- **New: common-ai:**: `from cloudmesh.ai.common.ssh import SSHConfig` $\rightarrow$ `SSHConfig()`

**Change**: Rename `ssh/encrypt.py` to `ssh/encryption.py` and `EncryptFile` to `SSHEncryption`.

- **Old: common**: `from cloudmesh.ai.common.ssh import encrypt` $\rightarrow$ `encrypt.EncryptFile()`
- **New: common-ai:**: `from cloudmesh.ai.common.ssh import SSHEncryption` $\rightarrow$ `SSHEncryption()`

## Time/Date
**Change**: Merge `time.py` into `DateTime.py`.

- **Old: common**: `from cloudmesh.ai.common import time`
- **New: common-ai:**: `from cloudmesh.ai.common import DateTime`

## UI/Console
**Change**: Consolidate `ui.py` functions into `io.py`'s `Console` class.

- **Old: common**: `from cloudmesh.ai.common import ui` $\rightarrow$ `ui.ai_response()` / `ui.print_error()`
- **New: commons-ai**: `from cloudmesh.ai.common.io import console` $\rightarrow$ `console.ai_response()` / `console.print_error()`
