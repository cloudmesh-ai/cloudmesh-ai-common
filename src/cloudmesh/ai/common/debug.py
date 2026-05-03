import functools
import inspect
from typing import Any, Callable
from cloudmesh.ai.common.io import console

class Debug:
    """Utility class for enhanced debugging and tracing in cloudmesh-ai."""

    _enabled = False

    @classmethod
    def enable(cls, value: bool = True):
        """Enables or disables debug output."""
        cls._enabled = value

    @classmethod
    def is_enabled(cls) -> bool:
        """Returns whether debug output is enabled."""
        return cls._enabled

    @classmethod
    def log(cls, message: str, level: str = "debug"):
        """Logs a message using the unified console if debug is enabled."""
        if not cls._enabled:
            return

        if level == "debug":
            console.print(f"[dim blue]DEBUG: {message}[/dim blue]")
        elif level == "trace":
            console.print(f"[dim cyan]TRACE: {message}[/dim cyan]")
        else:
            console.print(f"[bold blue]{level.upper()}: {message}[/bold blue]")

def trace(fn: Callable):
    """Decorator that logs the entry and exit of a function, including arguments and return value.
    
    Only logs if Debug.is_enabled() is True.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if not Debug.is_enabled():
            return fn(*args, **kwargs)

        # Get function name and module
        fn_name = fn.__qualname__
        
        # Format arguments
        arg_str = ", ".join([repr(a) for a in args])
        kwarg_str = ", ".join([f"{k}={v!r}" for k, v in kwargs.items()])
        params = ", ".join(filter(None, [arg_str, kwarg_str]))

        Debug.log(f"Entering {fn_name}({params})", level="trace")
        
        try:
            result = fn(*args, **kwargs)
            Debug.log(f"Exiting {fn_name} -> {result!r}", level="trace")
            return result
        except Exception as e:
            Debug.log(f"Exception in {fn_name}: {type(e).__name__}: {e}", level="error")
            raise

    return wrapper

def VERBOSE(arguments: Any):
    """Prints the arguments if debug is enabled.
    
    Maintains backward compatibility with the original VERBOSE function.
    """
    if arguments and getattr(arguments, "verbose", False):
        Debug.enable(True)
        console.print(f"[dim blue]VERBOSE: {arguments}[/dim blue]")