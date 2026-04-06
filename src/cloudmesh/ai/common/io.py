import os
from pathlib import Path

def path_expand(text: str, slashreplace: bool = True) -> str:
    """
    Expands a path string by resolving '~', environment variables, and relative links.

    Args:
        text (str): The path to be expanded (e.g., "~/$PROJECT/./file.txt").
        slashreplace (bool): If True, returns backslashes on Windows. Defaults to True.

    Returns:
        str: The fully expanded and absolute path.
    """
    if not text:
        return ""

    # 1. Expand ~ and Environment Variables
    expanded = os.path.expandvars(os.path.expanduser(text))
    
    # 2. Convert to a Path object and make it absolute
    # .resolve() handles the "./" and "../" logic correctly
    path_obj = Path(expanded).resolve()

    # 3. Handle string conversion and slash preference
    if slashreplace and os.name == 'nt':
        # On Windows, this automatically uses backslashes
        return str(path_obj)
    
    # .as_posix() forces forward slashes (/) regardless of OS
    return path_obj.as_posix()