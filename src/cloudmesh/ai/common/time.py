"""
Time and locale utility functions for cloudmesh-ai.
Provides tools for timezone detection and system locale identification.
"""

from tzlocal import get_localzone_name
import locale
from typing import Optional

def timezone(default: str = "America/New_York") -> str:
    """Returns the local timezone name.

    Args:
        default: The timezone to return if detection fails. Defaults to "America/New_York".

    Returns:
        The detected local timezone name or the default value.
    """
    try:
        return get_localzone_name()
    except Exception:
        return default

def locale_name() -> str:
    """Detects system locale (e.g., 'en_us').

    Returns:
        The detected locale language code in lowercase, or "us" if detection fails.
    """
    try:
        # Returns a tuple like ('en_US', 'UTF-8')
        lang_code, _ = locale.getlocale()
        return lang_code.split('_')[0].lower() if lang_code else "us"
    except Exception:
        return "us"
