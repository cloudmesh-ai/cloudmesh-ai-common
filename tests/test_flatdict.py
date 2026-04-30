import os
import pytest
import yaml
from cloudmesh.ai.common.flatdict import flatten, FlatDict, FlatDict2, expand_config_parameters

def test_flatten():
    d = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": 3
            }
        },
        "f": [1, 2]
    }
    expected = {
        "a": 1,
        "b__c": 2,
        "b__d__e": 3,
        "f": [1, 2]
    }
    assert flatten(d) == expected
    assert flatten(d, sep=".") == {"a": 1, "b.c": 2, "b.d.e": 3, "f": [1, 2]}

def test_flatdict_basic():
    d = {"a": 1, "b": {"c": 2}}
    fd = FlatDict(d)
    assert fd["a"] == 1
    assert fd["b__c"] == 2
    
    fd["d"] = 4
    assert fd["d"] == 4
    assert "d" in fd._data
    
    del fd["a"]
    assert "a" not in fd
    assert "a" not in fd._data

def test_flatdict_search():
    d = {
        "cloud.aws.region": "us-east-1",
        "cloud.azure.region": "eastus",
        "cloud.gcp.region": "us-central1",
        "user.name": "gregor"
    }
    fd = FlatDict(d, sep=".")
    
    # Search for all regions
    regions = fd.search(r"cloud\..*\.region")
    assert set(regions) == {"cloud.aws.region", "cloud.azure.region", "cloud.gcp.region"}
    
    # Search for specific value
    east_regions = fd.search(r"cloud\..*\.region", "us-east-1")
    assert east_regions == ["cloud.aws.region"]

def test_flatdict_unflatten():
    d = {"a__b__c": 1, "a__d": 2, "e": 3}
    fd = FlatDict(d)
    unflattened = fd.unflatten()
    assert unflattened == {"a": {"b": {"c": 1}, "d": 2}, "e": 3}

def test_flatdict_load(tmp_path):
    # Test loads (string)
    yaml_str = "person:\n  name: Gregor\n  age: 40"
    fd = FlatDict()
    fd.loads(yaml_str)
    assert fd["person__name"] == "Gregor"
    
    # Test loadd (dict)
    d = {"person": {"name": "Alice"}}
    fd.loadd(d)
    assert fd["person__name"] == "Alice"
    
    # Test loadf (file)
    f = tmp_path / "config.yaml"
    f.write_text("app:\n  port: 8080")
    fd.loadf(str(f))
    assert fd["app__port"] == 8080

def test_expand_config_parameters(monkeypatch):
    # Setup environment variable
    monkeypatch.setenv("TEST_VAR", "env_value")
    
    flat = {
        "name": "Gregor",
        "greeting": "Hello {name}",
        "env": "{os.TEST_VAR}",
        "math": "eval(1 + 1)",
        "nested": "{greeting}!"
    }
    
    expanded = expand_config_parameters(flat)
    
    assert expanded["greeting"] == "Hello Gregor"
    assert expanded["env"] == "env_value"
    assert expanded["math"] == 2
    assert expanded["nested"] == "Hello Gregor!"

def test_expand_config_security():
    # Test that ast.literal_eval prevents arbitrary code execution
    # This should fail to evaluate and return the original string or handle the error
    flat = {
        "danger": "eval(__import__('os').system('ls'))"
    }
    expanded = expand_config_parameters(flat)
    # It should not have executed the command, and since literal_eval fails on __import__,
    # it should remain as the original string or be handled by the try-except.
    assert expanded["danger"] == "eval(__import__('os').system('ls'))"

def test_flatdict2_convert():
    class User:
        def __init__(self, name, age):
            self.name = name
            self.age = age

    user = User("Gregor", 40)
    converted = FlatDict2.convert(user, flatten=True)
    
    assert isinstance(converted, FlatDict)
    assert converted["name"] == "Gregor"
    assert converted["age"] == 40

def test_flatdict2_complex_object():
    class Company:
        def __init__(self, name, employees):
            self.name = name
            self.employees = employees

    class Employee:
        def __init__(self, name):
            self.name = name

    emp1 = Employee("Alice")
    emp2 = Employee("Bob")
    comp = Company("Cloudmesh", [emp1, emp2])
    
    converted = FlatDict2.object_to_dict(comp)
    assert converted["name"] == "Cloudmesh"
    assert len(converted["employees"]) == 2
    assert converted["employees"][0]["name"] == "Alice"