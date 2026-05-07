# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

class CommonAIError(Exception):
    """Base exception for all cloudmesh-ai-common errors."""
    pass

class SSHError(CommonAIError):
    """Base exception for SSH related errors."""
    pass

class SSHConnectionError(SSHError):
    """Raised when a connection to a remote host fails."""
    pass

class SSHAuthenticationError(SSHError):
    """Raised when authentication fails."""
    pass

class IOErrorBase(CommonAIError):
    """Base exception for IO related errors."""
    pass

class IOReadError(IOErrorBase):
    """Raised when reading a file or stream fails."""
    pass

class IOWriteError(IOErrorBase):
    """Raised when writing to a file or stream fails."""
    pass

class SecurityError(CommonAIError):
    """Base exception for security and privilege escalation errors."""
    pass

class SecurityAuthError(SecurityError):
    """Raised when privilege escalation (sudo) fails."""
    pass