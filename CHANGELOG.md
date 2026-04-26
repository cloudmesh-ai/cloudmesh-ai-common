# Changelog

All notable changes to `cloudmesh-ai-common` will be documented in this file.

## [7.0.4.dev1] - 2026-04-26

### Added
- **Unified Remote Execution**: Introduced `cloudmesh.ai.common.remote.RemoteExecutor` for standardized SSH and SFTP operations.
    - Support for command execution with exit status capture.
    - Simplified file upload and download.
    - Direct remote file writing (`write_remote_file`).
- **Console Enhancements**: Added semantic helpers to the `Console` class: `ok()`, `error()`, `warning()`, and `ynchoice()`.
- **Remote Testing**: Added `tests/test_remote.py` with comprehensive mocks for verifying remote operations.

### Changed
- **I/O Utilities**: Removed redundant `SSHClient` from `cloudmesh.ai.common.io` in favor of `RemoteExecutor`.

## [7.0.3.dev1] - 2026-04-25

### Added
- **Enhanced DotDict**: Implemented `DotDict` in `cloudmesh.ai.common.util` supporting recursive nested attribute access (e.g., `d.a.b`).
- **Debug Utilities**: Added `HEADING` in `cloudmesh.ai.common.debug` for formatted output with automatic caller context.
- **I/O Utilities**: Added `readfile` to `cloudmesh.ai.common.io` for standardized file reading.
- **Common Tests**: Added `tests/test_common_utils.py` to verify new shared utilities.

### Changed
- **Config System**: Refactored `cloudmesh.ai.common.Config` to use `DotDict` for internal data management, simplifying dot-path access and updates.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.0.2.dev1] - 2026-04-19

### Added
- **Telemetry Module**: Introduced a standardized telemetry system for recording performance metrics and events.
    - Support for multiple backends including JSONL and SQLite.
    - Automatic capture of system context (CPU, GPU, RAM).
    - Async-ready design for AI service integration.
- **System Diagnostics**: Added `cloudmesh.ai.common.sys` for GPU detection and system state monitoring.
- **Performance Utilities**: 
    - Implemented thread-safe `Stopwatch` for precise timing of AI workloads.
    - Added `time` utilities for standardized time handling.
- **I/O & Logging**: 
    - Specialized `io` utilities for AI data handling.
    - AI-focused `logging` module for better traceability of model interactions.
- **Data Aggregation**: Added `aggregation` module to handle the combining of AI responses.
- **User Context**: Implemented `user` module to manage user-specific AI context and preferences.
- **Comprehensive Documentation**: Added detailed user manuals for telemetry, system, time, and I/O modules.
- **Test Suite**: Added integration and unit tests for all core common utilities.

### Changed
- Initial project structure established to provide a shared foundation for all `cloudmesh-ai` extensions.
- **I/O Utilities**: Updated `console` to use semantic methods (`console.error`, `console.msg`) instead of color-coded `console.print` for improved consistency.

### Fixed
- **StopWatch**: Fixed `TypeError` in `progress` function by ensuring the progress value is handled as a string and corrected keyword arguments for `progress` and `time`.
