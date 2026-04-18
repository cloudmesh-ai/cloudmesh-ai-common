import pytest
import logging
from pathlib import Path
from cloudmesh.ai.common import logging as ai_logging

def test_get_logger():
    script_name = "test_logger_func"
    logger = ai_logging.get_logger(script_name)
    
    # Verify logger instance
    assert isinstance(logger, logging.Logger)
    assert logger.name == script_name
    
    # Verify handlers are attached
    assert len(logger.handlers) >= 2  # FileHandler and StreamHandler
    
    # Verify log file creation
    log_file = ai_logging.get_log_file_path(script_name)
    # Since get_log_file_path generates a new timestamped name, 
    # we check if any file starting with script_name exists in the log dir
    log_dir = ai_logging.get_log_dir()
    files = list(log_dir.glob(f"{script_name}_*.log"))
    assert len(files) > 0

def test_logger_singleton():
    script_name = "singleton_test"
    logger1 = ai_logging.get_logger(script_name)
    logger2 = ai_logging.get_logger(script_name)
    
    # Verify it's the same instance
    assert logger1 is logger2