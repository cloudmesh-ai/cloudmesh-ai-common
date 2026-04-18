from tzlocal import get_localzone_name
import locale
from typing import Optional

def timezone(default: str = "America/New_York") -> str:
    try:
        return get_localzone_name()
    except Exception:
        return default

def locale_name() -> str:
    """Detects system locale (e.g., 'en_us')."""
    try:
        # Returns a tuple like ('en_US', 'UTF-8')
        lang_code, _ = locale.getlocale()
        return lang_code.split('_')[0].lower() if lang_code else "us"
    except Exception:
        return "us"
