# Changelog

All notable changes to `cloudmesh-ai-common` will be documented in this file.

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