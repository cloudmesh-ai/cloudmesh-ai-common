"""Class for starting and stopping named timers.
Provides a simple way to benchmark code execution and track events.
"""

import datetime
import os
import sys
import time
import inspect
import threading
from contextlib import contextmanager
from typing import Union, Optional, Dict, List, Any, Generator

from cloudmesh.ai.common import sys as ai_sys

def rename(newname):
    """Decorator to rename a function.

    Args:
        newname: The new name to assign to the function.

    Returns:
        A decorator function.
    """
    def decorator(f):
        f.__name__ = newname
        return f
    return decorator

def benchmark(func):
    """Decorator to benchmark a function.

    Args:
        func: The function to be benchmarked.

    Returns:
        A wrapper function that starts and stops a StopWatch timer.
    """
    @rename(func.__name__)
    def wrapper(*args, **kwargs):
        StopWatch.start(func.__name__)
        result = func(*args, **kwargs)
        StopWatch.stop(func.__name__)
        return result
    return wrapper

class StopWatch:
    """A class to measure times between events."""

    debug = False
    verbose = True
    _local = threading.local()

    @classmethod
    def _get_local(cls):
        """Ensures thread-local storage is initialized for the current thread.

        Returns:
            The thread-local storage object.
        """
        if not hasattr(cls._local, "timer_start"):
            cls._local.timer_start = {}
            cls._local.timer_end = {}
            cls._local.timer_elapsed = {}
            cls._local.timer_status = {}
            cls._local.timer_sum = {}
            cls._local.timer_msg = {}
            cls._local.timer_values = {}
        return cls._local

    @classmethod
    def debug_mode(cls, value: bool = True):
        """Enables or disables debug mode for timers.

        Args:
            value: True to enable debug mode, False to disable it. Defaults to True.
        """
        cls.debug = value
        if value:
            print("StopWatch: Debug mode enabled.")
        else:
            print("StopWatch: Debug mode disabled.")

    @classmethod
    def _get_caller_name(cls, with_class: bool = True) -> str:
        """Retrieves the name of the calling method.

        Args:
            with_class: If True, includes the class name in the returned string. 
                Defaults to True.

        Returns:
            The name of the calling method.
        """
        # frame[0] is this method, frame[1] is the caller of this method, 
        # frame[2] is the caller of the StopWatch method (Start/Stop/etc)
        frame = inspect.getouterframes(inspect.currentframe())
        method = frame[2][3]

        if with_class:
            classname = os.path.basename(frame[2].filename).replace(".py", "")
            method = f"{classname}/{method}"
        return method

    @classmethod
    @contextmanager
    def timer(cls, name: Optional[str] = None, values: Any = None) -> Generator[Optional[float], None, None]:
        """Context manager to time a block of code.
        
        Example:
            with StopWatch.timer("my_operation"):
                do_work()

        Args:
            name: The name of the timer. If None, it is automatically detected.
            values: Optional values to associate with the timer.
        """
        cls.start(name, values=values)
        try:
            yield None
        finally:
            cls.stop(name)
    @classmethod
    def keys(cls) -> List[str]:
        """Returns the names of the timers.

        Returns:
            A list of timer names.
        """
        return list(cls._get_local().timer_end.keys())

    @classmethod
    def status(cls, name: str, value: Any):
        """Records a status for the timer.

        Args:
            name: The name of the timer.
            value: The status value to record.
        """
        if cls.debug:
            print(f"Timer {name} status {value}")
        cls._get_local().timer_status[name] = value

    @classmethod
    def get_message(cls, name: str) -> Optional[str]:
        """Returns the message of the timer.

        Args:
            name: The name of the timer.

        Returns:
            The message associated with the timer, or None if not set.
        """
        return cls._get_local().timer_msg.get(name)

    @classmethod
    def message(cls, name: str, value: str):
        """Records a message for the timer.

        Args:
            name: The name of the timer.
            value: The message string to record.
        """
        cls._get_local().timer_msg[name] = value

    @classmethod
    def event(cls, name: str, msg: Optional[str] = None, values: Any = None):
        """Adds an event with a given name, where start and stop is the same time.

        Args:
            name: The name of the event.
            msg: Optional message to associate with the event.
            values: Optional values to associate with the event.
        """
        cls.start(name, values=values)
        cls.stop(name)
        local = cls._get_local()
        local.timer_end[name] = local.timer_start[name]
        if values:
            local.timer_values[name] = values
        if msg is not None:
            cls.message(name, str(msg))
        if cls.debug:
            print(f"Timer {name} event ...")

    @classmethod
    def start(cls, name: Optional[str] = None, values: Any = None):
        """Starts a timer with the given name.

        If name is None, it is automatically detected from the caller.

        Args:
            name: The name of the timer.
            values: Optional values to associate with the timer.
        """
        if name is None:
            name = cls._get_caller_name()
            
        local = cls._get_local()
        if cls.debug:
            print(f"Timer {name} started ...")
        if name not in local.timer_sum:
            local.timer_sum[name] = 0.0
        local.timer_start[name] = time.time()
        local.timer_end[name] = None
        local.timer_status[name] = None
        local.timer_msg[name] = None
        if values:
            local.timer_values[name] = values

    @classmethod
    def stop(cls, name: Optional[str] = None, state: Any = True, values: Any = None):
        """Stops the timer with a given name.

        If name is None, it is automatically detected from the caller.

        Args:
            name: The name of the timer.
            state: The final state of the timer (e.g., True for success).
            values: Optional values to associate with the timer.
        """
        if name is None:
            name = cls._get_caller_name()
            
        local = cls._get_local()
        local.timer_end[name] = time.time()
        local.timer_sum[name] = (
            local.timer_sum[name] + local.timer_end[name] - local.timer_start[name]
        )
        local.timer_status[name] = state
        if values:
            local.timer_values[name] = values
        if cls.debug:
            print(f"Timer {name} stopped ...")

    @classmethod
    def get_status(cls, name: str) -> Any:
        """Returns the status of the timer.

        Args:
            name: The name of the timer.

        Returns:
            The status value associated with the timer.
        """
        return cls._get_local().timer_status.get(name)

    @classmethod
    def get(cls, name: str, digits: int = 4) -> Union[float, str, None]:
        """Returns the elapsed time of the timer.

        Args:
            name: The name of the timer.
            digits: Number of decimal places to round to. Defaults to 4.

        Returns:
            The elapsed time as a float, "undefined" if not found, or None on error.
        """
        local = cls._get_local()
        if name in local.timer_end and local.timer_end[name] is not None:
            try:
                diff = local.timer_end[name] - local.timer_start[name]
                local.timer_elapsed[name] = round(diff, digits)
                return local.timer_elapsed[name]
            except Exception:
                return None
        return "undefined"

    @classmethod
    def sum(cls, name: str, digits: int = 4) -> Union[float, str, None]:
        """Returns the sum of the timer if used multiple times.

        Args:
            name: The name of the timer.
            digits: Number of decimal places to round to. Defaults to 4.

        Returns:
            The total elapsed time as a float, "undefined" if not found, or None on error.
        """
        local = cls._get_local()
        if name in local.timer_end:
            try:
                diff = local.timer_sum[name]
                return round(diff, digits)
            except Exception:
                return None
        return "undefined"

    @classmethod
    def clear(cls):
        """Clears all timers in the current thread."""
        local = cls._get_local()
        local.timer_start.clear()
        local.timer_end.clear()
        local.timer_sum.clear()
        local.timer_status.clear()
        local.timer_elapsed.clear()
        local.timer_msg.clear()
        local.timer_values.clear()

    @classmethod
    def print(cls, label: str, name: str):
        """Prints a timer with a label.

        Args:
            label: The label to print before the timer value.
            name: The name of the timer to print.
        """
        if cls.verbose:
            val = cls.get(name)
            if isinstance(val, float):
                print(f"{label} {val:.2f} s")
            else:
                print(f"{label} {val}")

    @classmethod
    def benchmark(cls, sysinfo: bool = True, tag: Optional[str] = None, filename: Optional[str] = None):
        """Prints out all timers in a convenient benchmark format for the current thread.

        Args:
            sysinfo: If True, includes system information in the output. Defaults to True.
            tag: Optional tag to include in the benchmark.
            filename: Optional file path to write the benchmark results to.
        """
        content = "\n--- Benchmark Results (Current Thread) ---\n"
        
        if sysinfo:
            info = ai_sys.systeminfo()
            content += "System Info:\n"
            for k, v in info.items():
                content += f"  {k}: {v}\n"
            content += "\n"

        timers = cls.keys()
        if not timers:
            content += "No timers found.\n"
        else:
            content += f"{'Timer':<30} {'Status':<10} {'Time (s)':<10} {'Sum (s)':<10} {'Msg'}\n"
            content += "-" * 70 + "\n"
            for t in timers:
                status = cls.get_status(t)
                status_str = "ok" if status is True else ("failed" if status is False else "unknown")
                msg = cls.get_message(t) or ""
                content += f"{t:<30} {status_str:<10} {cls.get(t, 3):<10} {cls.sum(t, 3):<10} {msg}\n"
        
        print(content)
        if filename:
            with open(filename, "w") as f:
                f.write(content)

class StopWatchBlock:
    """Context manager for StopWatch.

    Attributes:
        name: The name of the timer.
        data: Optional data to associate with the timer.
        log: The log destination (file path or stream).
        is_file: Boolean indicating if the log is a file.
        start_time: The time when the block was entered.
    """
    def __init__(self, name: str, data: Any = None, log=sys.stdout, mode: str = "w"):
        """Initializes the StopWatchBlock.

        Args:
            name: The name of the timer.
            data: Optional data to associate with the timer.
            log: The log destination. Defaults to sys.stdout.
            mode: The mode to open the log file in. Defaults to "w".
        """
        self.name = name
        self.data = data
        self.log = log
        self.is_file = False
        self.start_time = None
        if isinstance(log, str):
            self.is_file = True
            self.log = open(log, mode)

    def __enter__(self):
        """Starts the timer and returns the current elapsed time.

        Returns:
            The current elapsed time of the timer.
        """
        StopWatch.start(self.name)
        self.start_time = datetime.datetime.now()
        return StopWatch.get(self.name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stops the timer and logs the result.

        Args:
            exc_type: The type of the exception that occurred.
            exc_val: The instance of the exception that occurred.
            exc_tb: The traceback of the exception that occurred.
        """
        self.stop_time = datetime.datetime.now()
        StopWatch.stop(self.name)
        entry = StopWatch.get(self.name)
        
        msg = f"# {self.name}, {entry}, {self.start_time}, {self.stop_time}"
        if self.data:
            msg += f", {self.data}"
            
        print(msg, file=self.log)
        if self.is_file:
            self.log.close()