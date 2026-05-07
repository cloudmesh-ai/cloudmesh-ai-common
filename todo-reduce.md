# Redundancy Reduction Todo List

## System Information
- [x] Merge `systeminfo.py` (remove) into `sys.py` (keep)

## Sudo Utilities
- [x] Merge `sudo.py` (remove) into `security.py` (keep)

## IO & Utilities
- [x] Consolidate `path_expand()` and `banner()`: `util.py` (remove) $\rightarrow$ `io.py` (keep)
- [x] Consolidate `appendfile()` and `writefile()`: `util.py` (remove) $\rightarrow$ `io.py` (keep)
- [x] Consolidate `sudo_readfile()`: `util.py` (remove) $\rightarrow$ `security.py` (keep)

## Dictionary Flattening
- [x] Remove `flatten()`: `util.py` (remove) $\rightarrow$ `flatdict.py` (keep)

## SSH Configuration
- [x] Consolidate SSH config: `ssh.py` (remove) $\rightarrow$ `ssh/ssh_config.py` (keep)

## Time/Date
- [x] Merge `time.py` (remove) into `DateTime.py` (keep)

## UI/Console
- [x] Consolidate UI functions: `ui.py` (remove) $\rightarrow$ `io.py` (keep)
