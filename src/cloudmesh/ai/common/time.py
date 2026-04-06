from tzlocal import get_localzone_name
import locale

@staticmethod
def timezone(default="America/New_York"):
    try:
        return get_localzone_name()
    except Exception:
        return default

@staticmethod
def locale_name():
    """Detects system locale (e.g., 'en_us')."""
    try:
        # Returns a tuple like ('en_US', 'UTF-8')
        lang_code, _ = locale.getdefaultlocale()
        return lang_code.split('_')[0].lower() if lang_code else "us"
    except Exception:
        return "us"