# ----------------------------------------------------------------------
# Imports & helpers
# ----------------------------------------------------------------------
import os, sys, time, select, logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Union, Callable

import paramiko
from cloudmesh.ai.common.io import console   # keep for backward compatibility

log = logging.getLogger(__name__)

# ---------- configuration singleton ----------
class _GlobalConfig:
    _instance: Optional["_GlobalConfig"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cfg_path = Path(os.path.expanduser("~/.cloudmesh/ai.json"))
            data = {}
            if cfg_path.is_file():
                try:
                    import json
                    data = json.loads(cfg_path.read_text())
                except Exception:   # pragma: no cover
                    pass
            cls._instance.monitor_output = bool(data.get("monitor_output", False))
            cls._instance.trust_host_key = bool(data.get("trust_host_key", False))
        return cls._instance


# ---------- custom exception hierarchy ----------
class RemoteError(RuntimeError):
    def __init__(self, host: str, msg: str, cause: Exception | None = None):
        super().__init__(f"[{host}] {msg}")
        self.host = host
        self.__cause__ = cause


class RemoteCommandError(RemoteError):
    def __init__(self, host: str, command: str, exit_code: int,
                 stdout: str, stderr: str):
        super().__init__(host,
                         f"Command '{command}' failed (exit={exit_code})")
        self.command = command
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


class RemoteCommandTimeout(RemoteError, TimeoutError):
    pass


# ---------- result dataclass ----------
@dataclass(frozen=True)
class ExecResult:
    exit_code: int
    stdout: str
    stderr: str


# ----------------------------------------------------------------------
class RemoteExecutor:
    """
    High‑level SSH helper supporting live streaming, file transfer
    and safe configuration.

    Streaming modes (controlled by ``stream`` argument or the global
    ``monitor_output`` flag):
        * ``False`` – silent, only return buffers (default)
        * ``True``  – live stream **and** return buffers
        * ``"only"`` – live stream only, return ``None``
    """
    # --------------------------------------------------------------
    # Construction
    # --------------------------------------------------------------
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        key_filename: Optional[str] = None,
        *,
        monitor_output: Optional[bool] = None,
        trust_host_key: Optional[bool] = None,
        ssh_client_factory: Callable[[], paramiko.SSHClient] = paramiko.SSHClient,
    ):
        self.host = host
        self.username = username
        self.key_filename = key_filename
        self.client: Optional[paramiko.SSHClient] = None
        self._ssh_factory = ssh_client_factory

        cfg = _GlobalConfig()
        self.monitor_output = (monitor_output
                               if monitor_output is not None
                               else cfg.monitor_output)

        self.trust_host_key = (trust_host_key
                               if trust_host_key is not None
                               else cfg.trust_host_key)

    # --------------------------------------------------------------
    # Context manager – connection handling
    # --------------------------------------------------------------
    def __enter__(self):
        try:
            self.client = self._ssh_factory()
            self.client.load_system_host_keys()
            if self.trust_host_key:
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            else:
                self.client.set_missing_host_key_policy(paramiko.RejectPolicy())

            # ---- read ~/.ssh/config once per process ----------------
            ssh_cfg = self._load_ssh_config()
            host_cfg = ssh_cfg.lookup(self.host)

            connect_kwargs = {
                "hostname": host_cfg.get("hostname", self.host),
                "username": host_cfg.get("user", self.username),
                "key_filename": host_cfg.get("identityfile", self.key_filename),
                "port": int(host_cfg.get("port", 22)),
                "allow_agent": True,
                "look_for_keys": True,
            }

            log.debug("Connecting to %s with %s", self.host, connect_kwargs)
            self.client.connect(**connect_kwargs)
            return self
        except Exception as exc:
            log.exception("Failed to connect to %s", self.host)
            raise RemoteError(self.host, "SSH connection failed", exc) from exc

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
            self.client = None

    # --------------------------------------------------------------
    # Cached ssh config loader
    # --------------------------------------------------------------
    _cached_ssh_config: Optional[paramiko.SSHConfig] = None

    @classmethod
    def _load_ssh_config(cls) -> paramiko.SSHConfig:
        if cls._cached_ssh_config is None:
            cfg = paramiko.SSHConfig()
            cfg_path = os.path.expanduser("~/.ssh/config")
            if os.path.isfile(cfg_path):
                with open(cfg_path) as f:
                    cfg.parse(f)
            cls._cached_ssh_config = cfg
        return cls._cached_ssh_config

    # --------------------------------------------------------------
    # Helper – safe SFTP context manager
    # --------------------------------------------------------------
    from contextlib import contextmanager

    @contextmanager
    def _sftp(self):
        if not self.client:
            raise RemoteError(self.host, "SSH client not connected")
        sftp = self.client.open_sftp()
        try:
            yield sftp
        finally:
            sftp.close()

    # --------------------------------------------------------------
    # Core command execution (stream‑aware)
    # --------------------------------------------------------------
    def execute(
        self,
        command: str,
        timeout: int = 60,
        *,
        stream: Union[bool, str, None] = None,
        chunk_size: int = 64 * 1024,
        idle_sleep: float = 0.01,
    ) -> Union[ExecResult, None]:
        if not self.client:
            raise RemoteError(self.host, "SSH client not connected")

        # Resolve streaming mode -------------------------------------------------
        if stream is None:
            stream = self.monitor_output
        if isinstance(stream, str):
            stream = stream.lower()

        log.debug("Executing %r on %s (stream=%s, timeout=%s)",
                  command, self.host, stream, timeout)

        try:
            stdin, stdout, stderr = self.client.exec_command(
                command, timeout=timeout
            )
        except Exception as exc:                               # pragma: no cover
            log.exception("exec_command failed")
            raise RemoteError(self.host, f"Failed to start command: {command}", exc)

        channel = stdout.channel
        channel.settimeout(0.5)   # keep select() responsive

        out_buf = []
        err_buf = []

        def _write(chunk: bytes, to_err: bool = False):
            if to_err:
                sys.stderr.buffer.write(chunk)
                sys.stderr.flush()
            else:
                sys.stdout.buffer.write(chunk)
                sys.stdout.flush()

        start = time.time()
        while not channel.exit_status_ready():
            # ----- timeout handling -------------------------------------------------
            if timeout and (time.time() - start) > timeout:
                # attempt a graceful interrupt, then hard close
                try:
                    channel.send("\x03")   # SIGINT
                finally:
                    channel.close()
                raise RemoteCommandTimeout(
                    self.host,
                    f"Command timed out after {timeout}s: {command}"
                )

            # ----- non‑blocking read ------------------------------------------------
            # Note: both stdout & stderr share the same underlying socket,
            # so we only need to select on the channel itself.
            r, _, _ = select.select([channel], [], [], 0.5)
            if not r:
                # no data ready – small idle sleep to avoid busy‑loop
                time.sleep(idle_sleep)
                continue

            if channel.recv_ready():
                data = channel.recv(chunk_size)
                out_buf.append(data)
                if stream is True or stream == "only":
                    _write(data, to_err=False)

            if channel.recv_stderr_ready():
                data = channel.recv_stderr(chunk_size)
                err_buf.append(data)
                if stream is True or stream == "only":
                    _write(data, to_err=True)

        # Drain any remaining data -------------------------------------------------
        while channel.recv_ready():
            data = channel.recv(chunk_size)
            out_buf.append(data)
            if stream is True or stream == "only":
                _write(data, to_err=False)

        while channel.recv_stderr_ready():
            data = channel.recv_stderr(chunk_size)
            err_buf.append(data)
            if stream is True or stream == "only":
                _write(data, to_err=True)

        exit_code = channel.recv_exit_status()
        stdout_str = b"".join(out_buf).decode("utf-8", errors="replace")
        stderr_str = b"".join(err_buf).decode("utf-8", errors="replace")

        if exit_code != 0:
            raise RemoteCommandError(
                self.host, command, exit_code, stdout_str, stderr_str
            )

        if stream == "only":
            return None
        return ExecResult(exit_code, stdout_str, stderr_str)

    # --------------------------------------------------------------
    # File transfer helpers (now using the _sftp context manager)
    # --------------------------------------------------------------
    def upload(self, local_path: Path | str, remote_path: Path | str):
        local_path = Path(local_path)
        remote_path = str(remote_path)
        with self._sftp() as sftp:
            log.debug("Uploading %s → %s", local_path, remote_path)
            sftp.put(str(local_path), remote_path)

    def download(self, remote_path: Path | str, local_path: Path | str):
        remote_path = str(remote_path)
        local_path = Path(local_path)
        with self._sftp() as sftp:
            log.debug("Downloading %s → %s", remote_path, local_path)
            sftp.get(remote_path, str(local_path))

    def write_remote_file(self, content: str, remote_path: Path | str,
                          mode: int = 0o600):
        remote_path = str(remote_path)
        # Basic safety – prevent absolute paths that escape the user’s home
        if remote_path.startswith("/") and not remote_path.startswith("/home"):
            raise ValueError("Absolute remote_path must be within the user's home directory")
        with self._sftp() as sftp:
            log.debug("Writing remote file %s (mode %o)", remote_path, mode)
            with sftp.file(remote_path, "w") as f:
                f.write(content)
            sftp.chmod(remote_path, mode)

    # --------------------------------------------------------------
    # Pickle support (optional)
    # --------------------------------------------------------------
    def __getstate__(self):
        state = self.__dict__.copy()
        state["client"] = None           # SSHClient is not picklable
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.client = None