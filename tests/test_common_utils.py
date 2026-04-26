import os
import pytest
import tempfile
from cloudmesh.ai.common import DotDict, readfile, HEADING

def test_dotdict_basic():
    d = DotDict({"a": 1, "b": "text"})
    assert d.a == 1
    assert d.b == "text"
    assert d["a"] == 1

def test_dotdict_nested():
    data = {"a": {"b": {"c": 100}}}
    d = DotDict(data)
    assert d.a.b.c == 100
    assert d["a"]["b"]["c"] == 100

def test_dotdict_set_nested():
    d = DotDict()
    d.a = {"b": 1}
    assert d.a.b == 1
    
    d.a.b = 2
    assert d.a.b == 2
    assert d["a"]["b"] == 2

def test_dotdict_del():
    d = DotDict({"a": 1, "b": 2})
    del d.a
    assert "a" not in d
    with pytest.raises(AttributeError):
        _ = d.a

def test_readfile():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tf:
        tf.write("hello world")
        temp_path = tf.name
    
    try:
        content = readfile(temp_path)
        assert content == "hello world"
    finally:
        os.remove(temp_path)

def test_heading():
    # HEADING primarily prints to stdout, we just verify it doesn't crash
    # and handles optional text.
    HEADING("Test Heading")
    HEADING()