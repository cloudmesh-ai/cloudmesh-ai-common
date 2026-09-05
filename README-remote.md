
# RemoteExecutor – Unified SSH Utility for **cloudmesh‑ai**

A lightweight, high‑level wrapper around **Paramiko** that makes remote command execution, file transfer and on‑the‑fly file creation simple, safe and *stream‑aware*.  
It is part of the **cloudmesh‑ai** ecosystem but can be used as a stand‑alone helper in any Python project.

---

## Table of Contents
1. [Overview](#overview)  
2. [Features](#features)  
3. [Installation](#installation)  
4. [Quick‑Start Example](#quick-start-example)  
5. [Configuration (JSON & SSH config)](#configuration)  
6. [API Reference](#api-reference)  
7. [Streaming Modes](#streaming-modes)  
8. [Error handling & custom exceptions](#error‑handling)  
9. [Connection pooling & reuse](#connection‑pooling)  
10. [Async helper](#async-usage)  
11. [Testing & Mocking](#testing)  
12. [Contributing](#contributing)  
13. [License](#license)  

---  

## Overview<a name="overview"></a>

`RemoteExecutor` supplies a **context‑manager** that:

* Opens an SSH connection (honouring `~/.ssh/config` and a global JSON config).  
* Executes commands **with optional live streaming** of `stdout` / `stderr`.  
* Returns a typed `ExecResult` (`exit_code`, `stdout`, `stderr`) **or** streams only.  
* Provides simple SFTP helpers (`upload`, `download`, `write_remote_file`).  
* Offers a small runtime‑config system and sane defaults (host‑key verification, timeout handling, logging).  

---

## Features<a name="features"></a>

| ✅ | Feature |
|----|---------|
| **Live streaming** | `stdout` / `stderr` can be echoed to the local console while the remote process runs. |
| **Typed result** | `ExecResult` (dataclass) replaces the old ambiguous tuple. |
| **Global + per‑call control** | A JSON config flag (`monitor_output`) and a `stream` argument let you switch behavior globally or per command. |
| **Config‑driven host‑key policy** | Optional `trust_host_key` to auto‑accept unknown keys or reject them (safer default). |
| **Connection pooling** | Re‑use TCP sessions across multiple `RemoteExecutor` instances. |
| **Async wrapper** | Minimal `AsyncRemoteExecutor` that runs `execute` in an executor without blocking the event loop. |
| **Robust error handling** | Custom exception hierarchy (`RemoteError`, `RemoteCommandError`, `RemoteCommandTimeout`). |
| **Built‑in logging** | Uses the standard `logging` module – no more `print` statements. |
| **Test‑friendly** | Inject a mock `SSHClient` via the `ssh_client_factory` argument. |
| **Pythonic file arguments** | Accept `pathlib.Path` objects for all file‑related parameters. |
| **Safety checks** | Optional chmod, path sanitisation for `write_remote_file`. |

---

## Installation<a name="installation"></a>

```bash
# Install the cloudmesh‑ai package (which includes RemoteExecutor)
pip install cloudmesh-ai

# Or, if you only need this utility, install its direct dependency:
pip install paramiko
```

> **Note** – `RemoteExecutor` lives in `cloudmesh.ai.common.remote`.  
> After installation you can import it with:

```python
from cloudmesh.ai.common.remote import RemoteExecutor
```

---

## Quick‑Start Example<a name="quick-start-example"></a>

```python
from cloudmesh.ai.common.remote import RemoteExecutor

# 1️⃣  Use the default configuration (reads ~/.cloudmesh/ai.json)
with RemoteExecutor("my.remote.host", username="alice") as exe:
    # Live stream output **and** capture it
    result = exe.execute("uname -a", stream=True)

    print("\n--- Finished ---")
    print(f"rc  = {result.exit_code}")
    print(f"out = {result.stdout.strip()}")
    print(f"err = {result.stderr.strip()}")
```

### Streaming‑only (fire‑and‑forget)

```python
with RemoteExecutor("my.remote.host") as exe:
    exe.execute("tail -f /var/log/syslog", stream="only")
    # The method returns None; the log is streamed to your console in real time.
```

### Silent (classic) mode

```python
with RemoteExecutor("my.remote.host") as exe:
    rc, out, err = exe.execute("ls -l /tmp")   # uses the default (no streaming)
```

### File transfer

```python
with RemoteExecutor("my.remote.host") as exe:
    exe.upload("local_script.sh", "/home/alice/script.sh")
    exe.execute("chmod +x /home/alice/script.sh && /home/alice/script.sh")
    exe.download("/home/alice/output.txt", "output.txt")
```

### Write a temporary config file on the remote side

```python
script = """#!/bin/bash
echo "Hello from the remote host!"
"""

with RemoteExecutor("my.remote.host") as exe:
    exe.write_remote_file(script, "/tmp/hello.sh", mode=0o755)
    exe.execute("bash /tmp/hello.sh")
```

---

## Configuration<a name="configuration"></a>

### Global JSON config (`~/.cloudmesh/ai.json`)

```json
{
  "monitor_output": true,          // stream by default (can be overridden per call)
  "trust_host_key": false          // reject unknown host keys unless explicitly allowed
}
```

*If the file does not exist, default values (`monitor_output=False`, `trust_host_key=False`) are used.*

### SSH config (`~/.ssh/config`)

`RemoteExecutor` automatically reads the standard OpenSSH config file, so you can define host aliases, custom ports, identity files, etc.:

```ssh
Host myremote
    HostName 10.0.2.15
    User alice
    IdentityFile ~/.ssh/id_ed25519
    Port 2222
```

You can still override any of those values by passing arguments to `RemoteExecutor`.

---

## API Reference<a name="api-reference"></a>

### Class: `RemoteExecutor`

```python
RemoteExecutor(
    host: str,
    username: Optional[str] = None,
    key_filename: Optional[str] = None,
    *,
    monitor_output: Optional[bool] = None,
    trust_host_key: Optional[bool] = None,
    ssh_client_factory: Callable[[], paramiko.SSHClient] = paramiko.SSHClient,
)
```

| Method | Description | Return |
|--------|-------------|--------|
| `__enter__()` / `__exit__()` | Open/close the SSH connection (use as a context manager). | `self` |
| `execute(command: str, timeout: int = 60, *, stream: Union[bool, str, None] = None, chunk_size: int = 65536, idle_sleep: float = 0.01) → ExecResult \| None` | Run a remote command. Streaming behavior is controlled by `stream` or the global `monitor_output` flag. | `ExecResult` (or `None` when `stream="only"`) |
| `upload(local_path: Path|str, remote_path: Path|str) → None` | SFTP upload. |
| `download(remote_path: Path|str, local_path: Path|str) → None` | SFTP download. |
| `write_remote_file(content: str, remote_path: Path|str, mode: int = 0o600) → None` | Create/overwrite a file on the remote host. |
| `_sftp()` *(private)* | Context manager that yields a ready‑to‑use `paramiko.SFTPClient`. |
| `close_all()` *(class method, optional)* | Shut down every client kept in the internal pool. |

### Dataclass: `ExecResult`

```python
@dataclass(frozen=True)
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str
```

### Exceptions

| Exception | When raised |
|-----------|--------------|
| `RemoteError` | Base class for any remote‑related failure (connection, config, etc.). |
| `RemoteCommandError` | Remote command finished with a non‑zero exit status. Provides `command`, `stdout`, `stderr`. |
| `RemoteCommandTimeout` | Command exceeded the supplied `timeout`. |
| `ValueError` | Invalid arguments (e.g., malicious `remote_path` in `write_remote_file`). |

All custom exceptions inherit from `RuntimeError` and contain the host name for easier debugging.

---

## Streaming Modes<a name="streaming-modes"></a>

| `stream` argument | Behaviour | Return value |
|-------------------|-----------|--------------|
| `None` (default) | Uses `self.monitor_output` (global flag). | `ExecResult` |
| `False` | No live output, classic silent mode. | `ExecResult` |
| `True` | **Live stream** to local `stdout`/`stderr` **and** return `ExecResult`. | `ExecResult` |
| `"only"` | **Live stream only** – nothing is returned (`None`). | `None` |

> **Why a flag instead of separate methods?**  
> It keeps the API surface tiny while giving you per‑command control. The global config lets you turn streaming on for an entire session (e.g., during interactive debugging) without changing any call sites.

---

## Error Handling<a name="error-handling"></a>

```python
try:
    with RemoteExecutor("host") as exe:
        result = exe.execute("some-failing-cmd", stream=True)
except RemoteCommandError as e:
    log.error("Command failed: %s", e.stderr)
except RemoteCommandTimeout as e:
    log.error("Command timed out")
except RemoteError as e:
    log.error("SSH problem: %s", e)
```

* `RemoteCommandError` gives you full access to `e.stdout` and `e.stderr`.  
* `RemoteError` is the catch‑all for connection failures, config parsing problems, etc.  

All custom exceptions preserve the original traceback (`__cause__`) for deep debugging.

---

## Connection Pooling & Reuse<a name="connection-pooling"></a>

The class maintains a **module‑level pool** keyed by `(host, port, username)`.  
When you re‑enter a `RemoteExecutor` that points to a host already in the pool, the existing `SSHClient` is reused, saving the SSH handshake.

```python
with RemoteExecutor("host") as exe:
    exe.execute("date")
# client stays in the internal pool

# Later in the same process
with RemoteExecutor("host") as exe2:   # re‑uses the same TCP session
    exe2.upload("local.txt", "/tmp/remote.txt")
```

If you need to shut everything down (e.g., at program exit) call:

```python
RemoteExecutor.close_all()
```

---

## Async Usage<a name="async-usage"></a>

A tiny subclass ships with the module:

```python
from cloudmesh.ai.common.remote import AsyncRemoteExecutor

async def run():
    async with AsyncRemoteExecutor("host") as exe:
        result = await exe.execute_async("sleep 2 && echo done", stream=True)
        print(result.stdout)

# In an asyncio program
import asyncio
asyncio.run(run())
```

`AsyncRemoteExecutor` simply runs the synchronous `execute` in a thread pool (`loop.run_in_executor`).  
You can similarly wrap `upload`, `download`, and `write_remote_file` if needed.

---

## Testing & Mocking<a name="testing"></a>

The constructor accepts a **factory** that returns a `paramiko.SSHClient`.  
In unit tests you can inject a mock client to avoid real network traffic.

```python
from unittest.mock import MagicMock
import pytest
from cloudmesh.ai.common.remote import RemoteExecutor

def make_fake_client():
    mock = MagicMock()
    # configure exec_command, open_sftp, etc. on the mock as needed
    return mock

def test_execute_success():
    with RemoteExecutor("dummy", ssh_client_factory=make_fake_client) as exe:
        result = exe.execute("echo hi", stream=False)
    assert result.exit_code == 0
    assert "hi" in result.stdout
```

The SFTP helper `_sftp` is also a context manager, so you can mock `open_sftp` and verify calls.

---

## Contributing<a name="contributing"></a>

1. **Fork** the repository.  
2. Create a feature branch (`git checkout -b my‑feature`).  
3. Make changes and **add tests** in `tests/`.  
4. Run the full suite:

   ```bash
   pip install -r requirements-dev.txt
   pytest -v
   ```

5. Ensure **type hints** pass `mypy` and formatting passes `black`/`ruff`.  
6. Submit a **Pull Request** with a clear description and reference to any open issue.

See `CONTRIBUTING.md` (in the repo) for detailed guidelines, commit‑message style, and code‑review process.

---

## License<a name="license"></a>

`RemoteExecutor` is released under the **Apache License 2.0**.  
See the `LICENSE` file in the repository for the full text.

---  

### Happy remote hacking! 🚀

If you have any questions or encounter a bug, please open an issue on the GitHub repository.