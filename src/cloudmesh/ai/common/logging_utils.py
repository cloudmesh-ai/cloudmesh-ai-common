# Copyright 2026 Gregor von Laszewski
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

import logging
from typing import Any, Dict, Optional

class ContextualLogger(logging.LoggerAdapter):
    """Logger adapter that adds contextual information to log messages.
    
    This is particularly useful for parallel operations where you need to 
    distinguish logs by host, user, or operation ID.
    """

    def process(self, msg: Any, kwargs: Optional[Dict[str, Any]] = None) -> tuple:
        """Inject context into the log message.
        
        Args:
            msg: The log message.
            kwargs: The log arguments.
            
        Returns:
            tuple: (msg, kwargs)
        """
        if kwargs is None:
            kwargs = {}
            
        context = self.extra
        if context:
            # Format context as [key=value] pairs
            ctx_str = " ".join([f"[{k}={v}]" for k, v in context.items()])
            msg = f"{ctx_str} {msg}"
            
        return msg, kwargs

def get_contextual_logger(name: str, initial_context: Optional[Dict[str, Any]] = None) -> ContextualLogger:
    """Factory function to create a ContextualLogger.
    
    Args:
        name: The name of the logger.
        initial_context: Initial context to associate with the logger.
        
    Returns:
        ContextualLogger: A logger adapter with the specified context.
    """
    logger = logging.getLogger(name)
    return ContextualLogger(logger, initial_context or {})