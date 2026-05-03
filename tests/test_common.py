import pytest
import os
import asyncio
from pathlib import Path
from cloudmesh.ai.common.io import Console, readfile, writefile, async_readfile, async_writefile
from cloudmesh.ai.common.util import flatten, backup_name, path_expand
from cloudmesh.ai.common.systeminfo import os_is_windows, os_is_linux, os_is_mac
from cloudmesh.ai.common.debug import Debug, trace

# --- Tests for util.py ---

def test_flatten():
    d = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
    expected = {"a": 1, "b__c": 2, "b__d__e": 3}
    assert flatten(d) == expected

    d_list = [{"a": 1}, {"a": 2}]
    expected_list = [{"a": 1}, {"a": 2}]
    assert flatten(d_list) == expected_list

def test_backup_name(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
    bak = backup_name(f)
    assert "test.txt.bak.1" in bak
    Path(bak).exists() # This is just to check it doesn't crash

def test_path_expand():
    # Test basic expansion
    assert path_expand("~") == str(Path("~").expanduser().resolve().as_posix())

# --- Tests for io.py ---

def test_console_styled_output(capsys):
    console = Console()
    console.ok("Success")
    captured = capsys.readouterr()
    assert "OK: Success" in captured.out

def test_ynchoice(monkeypatch):
    console = Console()
    # Simulate user typing 'y'
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    assert console.ynchoice("Continue?") is True
    
    # Simulate user typing 'n'
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    assert console.ynchoice("Continue?") is False

def test_print_attributes_formats(capsys):
    console = Console()
    data = {"name": "test", "value": 100}
    
    console.print_attributes(data, output="json")
    captured = capsys.readouterr()
    assert '"name": "test"' in captured.out
    
    console.print_attributes(data, output="yaml")
    captured = capsys.readouterr()
    assert "name: test" in captured.out

@pytest.mark.asyncio
async def test_async_io(tmp_path):
    f = tmp_path / "async_test.txt"
    content = "hello async"
    
    await async_writefile(str(f), content)
    assert f.read_text() == content
    
    read_content = await async_readfile(str(f))
    assert read_content == content

# --- Tests for systeminfo.py ---

def test_os_detection():
    # These are basic checks to ensure they return booleans
    assert isinstance(os_is_windows(), bool)
    assert isinstance(os_is_linux(), bool)
    assert isinstance(os_is_mac(), bool)

# --- Tests for debug.py ---

def test_debug_logging(capsys):
    Debug.enable(False)
    Debug.log("Hidden message")
    captured = capsys.readouterr()
    assert "Hidden message" not in captured.out
    
    Debug.enable(True)
    Debug.log("Visible message")
    captured = capsys.readouterr()
    assert "DEBUG: Visible message" in captured.out

def test_trace_decorator(capsys):
    @trace
    def add(a, b):
        return a + b
    
    Debug.enable(True)
    add(1, 2)
    captured = capsys.readouterr()
    assert "Entering add(1, 2)" in captured.out
    assert "Exiting add -> 3" in captured.out