"""Debug utilities for cloudmesh-ai."""

import os
import inspect
from cloudmesh.ai.common.io import banner

def HEADING(txt=None, c="#", color="HEADER"):
    """Prints a message to stdout with #### surrounding it. This is useful for
    pytests to better distinguish them.

    Args:
        txt (str, optional): a text message to be printed. Defaults to None.
        c (str): uses the given char to wrap the header. Defaults to "#".
        color (str): color for the banner. Defaults to "HEADER".
    """
    frame = inspect.getouterframes(inspect.currentframe())

    # frame[0] is this function, frame[1] is the caller
    caller_frame = frame[1]
    filename = caller_frame[1].replace(os.getcwd(), "")
    line = caller_frame[2] - 1
    method = caller_frame[3]

    if txt is None:
        msg = "{} {} {}".format(method, filename, line)
    else:
        msg = "{}\n {} {} {}".format(txt, method, filename, line)

    print()
    # Use the banner utility from io.py
    # Note: the original cloudmesh-common banner might have had different args,
    # but we use the current cloudmesh-ai-common.io.banner implementation.
    banner(msg)