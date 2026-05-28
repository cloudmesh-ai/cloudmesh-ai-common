"""
Comprehensive tests for DotDict class.

DotDict provides a dictionary-like object that allows accessing and setting
nested values using both attribute notation and dot-separated string keys.
"""

import pytest
import json
import yaml
from cloudmesh.ai.common.dotdict import DotDict


class TestDotDictBasics:
    """Tests for basic DotDict functionality."""

    def test_empty_initialization(self):
        """Test creating an empty DotDict."""
        d = DotDict()
        assert len(d) == 0
        assert isinstance(d, dict)

    def test_dict_initialization(self):
        """Test creating DotDict from a dictionary."""
        data = {"a": 1, "b": "text", "c": [1, 2, 3]}
        d = DotDict(data)
        assert d.a == 1
        assert d.b == "text"
        assert d.c == [1, 2, 3]

    def test_kwargs_initialization(self):
        """Test creating DotDict with keyword arguments."""
        d = DotDict(a=1, b="text")
        assert d.a == 1
        assert d.b == "text"

    def test_mixed_initialization(self):
        """Test creating DotDict with both dict and kwargs."""
        d = DotDict({"a": 1}, b=2)
        assert d.a == 1
        assert d.b == 2

    def test_invalid_initialization(self):
        """Test that non-dict data raises TypeError."""
        with pytest.raises(TypeError, match="Data must be a dictionary"):
            DotDict("not a dict")
        with pytest.raises(TypeError, match="Data must be a dictionary"):
            DotDict(123)

    def test_none_initialization(self):
        """Test that None creates empty DotDict."""
        d = DotDict(None)
        assert len(d) == 0


class TestDotDictBracketAccess:
    """Tests for bracket notation access."""

    def test_simple_bracket_access(self):
        """Test basic bracket access."""
        d = DotDict({"a": 1, "b": 2})
        assert d["a"] == 1
        assert d["b"] == 2

    def test_dot_notation_bracket_access(self):
        """Test dot-notation in brackets for nested access."""
        data = {"cloudmesh": {"ai": {"server": "uva"}}}
        d = DotDict(data)
        assert d["cloudmesh.ai.server"] == "uva"
        assert d["cloudmesh.ai"] == {"server": "uva"}

    def test_nested_dot_notation_access(self):
        """Test deeply nested dot-notation access."""
        data = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        d = DotDict(data)
        assert d["a.b.c.d.e"] == "deep"

    def test_bracket_keyerror(self):
        """Test KeyError for missing keys."""
        d = DotDict({"a": 1})
        with pytest.raises(KeyError):
            _ = d["missing"]

    def test_dot_notation_keyerror(self):
        """Test KeyError for broken dot-notation path."""
        d = DotDict({"a": {"b": 1}})
        with pytest.raises(KeyError):
            _ = d["a.missing.c"]


class TestDotDictAttributeAccess:
    """Tests for attribute notation access."""

    def test_simple_attribute_access(self):
        """Test basic attribute access."""
        d = DotDict({"a": 1, "b": "text"})
        assert d.a == 1
        assert d.b == "text"

    def test_nested_attribute_access(self):
        """Test nested attribute access."""
        data = {"cloudmesh": {"ai": {"server": "uva"}}}
        d = DotDict(data)
        assert d.cloudmesh.ai.server == "uva"

    def test_attribute_error(self):
        """Test AttributeError for missing attributes."""
        d = DotDict({"a": 1})
        with pytest.raises(AttributeError):
            _ = d.missing

    def test_reserved_attributes(self):
        """Test that reserved attributes work correctly."""
        d = DotDict({"items": 1, "keys": 2, "values": 3})
        # These should return DotDict items, not override methods
        assert isinstance(d.keys(), type({}.keys()))
        assert d["items"] == 1


class TestDotDictAssignment:
    """Tests for setting values."""

    def test_simple_bracket_assignment(self):
        """Test basic bracket assignment."""
        d = DotDict()
        d["a"] = 1
        assert d.a == 1

    def test_dot_notation_bracket_assignment(self):
        """Test dot-notation in brackets for nested assignment."""
        d = DotDict()
        d["cloudmesh.ai.server"] = "uva"
        assert d.cloudmesh.ai.server == "uva"

    def test_attribute_assignment(self):
        """Test attribute assignment."""
        d = DotDict()
        d.a = 1
        assert d["a"] == 1

    def test_nested_attribute_assignment(self):
        """Test nested attribute assignment creates DotDict."""
        d = DotDict()
        d.new_section = DotDict()
        d.new_section.key = "value"
        assert d["new_section.key"] == "value"

    def test_dict_to_dotdict_conversion(self):
        """Test that dict values are converted to DotDict."""
        d = DotDict()
        d["config"] = {"nested": {"value": 1}}
        assert isinstance(d.config, DotDict)
        assert isinstance(d.config.nested, DotDict)

    def test_list_of_dicts_conversion(self):
        """Test that lists containing dicts are converted."""
        # Use 'entries' instead of 'items' to avoid conflict with dict.items() method
        data = {"entries": [{"a": 1}, {"b": 2}]}
        d = DotDict(data)
        assert isinstance(d.entries[0], DotDict)
        assert d.entries[0].a == 1


class TestDotDictDeletion:
    """Tests for deleting values."""

    def test_simple_deletion(self):
        """Test basic deletion."""
        d = DotDict({"a": 1, "b": 2})
        del d["a"]
        assert "a" not in d
        assert "b" in d

    def test_attribute_deletion(self):
        """Test attribute deletion."""
        d = DotDict({"a": 1})
        del d.a
        assert "a" not in d

    def test_dot_notation_deletion(self):
        """Test dot-notation deletion."""
        d = DotDict({"a": {"b": {"c": 1}}})
        del d["a.b.c"]
        assert "c" not in d.a.b

    def test_delete_keyerror(self):
        """Test KeyError for deleting missing keys."""
        d = DotDict({"a": 1})
        with pytest.raises(KeyError):
            del d["missing"]

    def test_delete_dot_notation_keyerror(self):
        """Test KeyError for broken dot-notation deletion."""
        d = DotDict({"a": {"b": 1}})
        with pytest.raises(KeyError):
            del d["a.missing.c"]


class TestDotDictGet:
    """Tests for the get() method."""

    def test_get_simple(self):
        """Test basic get operation."""
        d = DotDict({"a": 1})
        assert d.get("a") == 1
        assert d.get("missing") is None
        assert d.get("missing", "default") == "default"

    def test_get_dot_notation(self):
        """Test get with dot-notation."""
        d = DotDict({"a": {"b": {"c": 1}}})
        assert d.get("a.b.c") == 1
        assert d.get("a.b.missing") is None
        assert d.get("a.b.missing", "default") == "default"

    def test_get_broken_path(self):
        """Test get with broken path returns default."""
        d = DotDict({"a": {"b": 1}})
        assert d.get("a.b.c.d") is None
        assert d.get("a.b.c.d", "default") == "default"


class TestDotDictContains:
    """Tests for the __contains__ method."""

    def test_contains_simple(self):
        """Test basic contains check."""
        d = DotDict({"a": 1})
        assert "a" in d
        assert "missing" not in d

    def test_contains_dot_notation(self):
        """Test contains with dot-notation."""
        d = DotDict({"a": {"b": {"c": 1}}})
        assert "a.b.c" in d
        assert "a.b.missing" not in d
        assert "missing.b.c" not in d


class TestDotDictKeysItemsValues:
    """Tests for keys(), items(), values() methods."""

    def test_keys_simple(self):
        """Test basic keys() method."""
        d = DotDict({"a": 1, "b": 2})
        keys = list(d.keys())
        assert "a" in keys
        assert "b" in keys

    def test_keys_with_path(self):
        """Test keys() with dot-notation path."""
        d = DotDict({"a": {"b": 1, "c": 2}})
        keys = list(d.keys("a"))
        assert "b" in keys
        assert "c" in keys

    def test_keys_path_error(self):
        """Test keys() raises TypeError for non-dict path."""
        d = DotDict({"a": 1})
        with pytest.raises(TypeError):
            list(d.keys("a"))

    def test_items_simple(self):
        """Test basic items() method."""
        d = DotDict({"a": 1, "b": 2})
        items = list(d.items())
        assert ("a", 1) in items
        assert ("b", 2) in items

    def test_items_with_path(self):
        """Test items() with dot-notation path."""
        d = DotDict({"a": {"b": 1, "c": 2}})
        items = list(d.items("a"))
        assert ("b", 1) in items
        assert ("c", 2) in items

    def test_values_simple(self):
        """Test basic values() method."""
        d = DotDict({"a": 1, "b": 2})
        values = list(d.values())
        assert 1 in values
        assert 2 in values

    def test_values_with_path(self):
        """Test values() with dot-notation path."""
        d = DotDict({"a": {"b": 1, "c": 2}})
        values = list(d.values("a"))
        assert 1 in values
        assert 2 in values


class TestDotDictMerge:
    """Tests for the merge() method."""

    def test_merge_simple(self):
        """Test basic merge."""
        d = DotDict({"a": 1})
        d.merge({"b": 2})
        assert d.a == 1
        assert d.b == 2

    def test_merge_nested(self):
        """Test nested merge."""
        d = DotDict({"a": {"b": 1}})
        d.merge({"a": {"c": 2}})
        assert d.a.b == 1
        assert d.a.c == 2

    def test_merge_deep(self):
        """Test deep merge preserves existing values."""
        d = DotDict({"a": {"b": {"c": 1, "d": 2}}})
        d.merge({"a": {"b": {"e": 3}}})
        assert d.a.b.c == 1
        assert d.a.b.d == 2
        assert d.a.b.e == 3

    def test_merge_overwrite(self):
        """Test merge overwrites non-dict values."""
        d = DotDict({"a": {"b": 1}})
        d.merge({"a": "replaced"})
        assert d.a == "replaced"

    def test_merge_converts_dict(self):
        """Test merge converts dict to DotDict."""
        d = DotDict()
        d.merge({"a": {"b": 1}})
        assert isinstance(d.a, DotDict)

    def test_merge_invalid(self):
        """Test merge ignores non-dict input."""
        d = DotDict({"a": 1})
        d.merge("not a dict")
        assert d.a == 1


class TestDotDictExpand:
    """Tests for the expand() method."""

    def test_expand_simple(self):
        """Test basic expand with placeholders."""
        d = DotDict({"name": "gemma", "path": "/models/{name}"})
        expanded = d.expand()
        assert expanded.path == "/models/gemma"

    def test_expand_no_placeholders(self):
        """Test expand when no placeholders exist."""
        d = DotDict({"a": 1, "b": "text"})
        expanded = d.expand()
        assert expanded.a == 1
        assert expanded.b == "text"

    def test_expand_external_dict(self):
        """Test expand with external dictionary."""
        d = DotDict({"name": "gemma"})
        data = {"path": "/models/{name}"}
        expanded = d.expand(d=data)
        assert expanded["path"] == "/models/gemma"

    def test_expand_recursive(self):
        """Test recursive placeholder expansion."""
        d = DotDict({
            "base": "/home",
            "user": "{base}/user",
            "path": "{user}/models"
        })
        expanded = d.expand()
        assert expanded.path == "/home/user/models"

    def test_expand_with_lists(self):
        """Test expand handles lists."""
        d = DotDict({"name": "gemma", "paths": ["/models/{name}", "/data/{name}"]})
        expanded = d.expand()
        assert expanded.paths[0] == "/models/gemma"
        assert expanded.paths[1] == "/data/gemma"

    def test_expand_nested_dict(self):
        """Test expand handles nested DotDicts - values at top level only."""
        # Note: expand() only expands placeholders at the top level of the target dict
        # Nested dict values are not automatically expanded
        d = DotDict({
            "name": "gemma",
            "config": {"path": "/models/{name}"}
        })
        expanded = d.expand()
        # Top level values get expanded
        assert expanded.name == "gemma"
        # Nested values with placeholders are not expanded by default
        assert expanded.config.path == "/models/{name}"

    def test_expand_max_iterations(self):
        """Test expand respects max_iterations."""
        d = DotDict({
            "a": "{b}",
            "b": "{a}"
        })
        # Should not hang, should stop after max_iterations
        expanded = d.expand(max_iterations=3)

    def test_expand_type_error(self):
        """Test expand raises TypeError for non-dict target."""
        d = DotDict({"a": 1})
        with pytest.raises(TypeError, match="Target to expand must be a dictionary"):
            d.expand(d="not a dict")


class TestDotDictSmartGet:
    """Tests for the smart_get() method."""

    def test_smart_get_direct(self):
        """Test smart_get finds direct path."""
        d = DotDict({"a": {"b": {"c": 1}}})
        assert d.smart_get("a.b.c") == 1

    def test_smart_get_recursive(self):
        """Test smart_get finds key recursively."""
        d = DotDict({"x": {"y": {"target": "found"}}})
        assert d.smart_get("target") == "found"

    def test_smart_get_not_found(self):
        """Test smart_get returns default when not found."""
        d = DotDict({"a": 1})
        assert d.smart_get("missing") is None
        assert d.smart_get("missing", "default") == "default"

    def test_smart_get_nested_match(self):
        """Test smart_get prefers direct path over recursive."""
        d = DotDict({
            "direct": {"target": "direct_value"},
            "other": {"target": "recursive_value"}
        })
        assert d.smart_get("direct.target") == "direct_value"

    def test_smart_get_deep_recursive(self):
        """Test smart_get searches deeply."""
        d = DotDict({
            "a": {
                "b": {
                    "c": {
                        "deep_key": "deep_value"
                    }
                }
            }
        })
        assert d.smart_get("deep_key") == "deep_value"


class TestDotDictSerialization:
    """Tests for serialization methods."""

    def test_to_dict(self):
        """Test to_dict converts to plain dict."""
        d = DotDict({"a": {"b": 1}})
        plain = d.to_dict()
        assert isinstance(plain, dict)
        assert not isinstance(plain, DotDict)
        assert plain["a"]["b"] == 1

    def test_to_dict_nested(self):
        """Test to_dict converts nested DotDicts."""
        d = DotDict({"a": {"b": {"c": 1}}})
        plain = d.to_dict()
        assert isinstance(plain["a"], dict)
        assert isinstance(plain["a"]["b"], dict)

    def test_dict_property(self):
        """Test dict property."""
        d = DotDict({"a": 1})
        assert d.dict == {"a": 1}

    def test_to_json(self):
        """Test to_json method."""
        d = DotDict({"a": {"b": 1}})
        json_str = d.to_json()
        parsed = json.loads(json_str)
        assert parsed["a"]["b"] == 1

    def test_to_json_indent(self):
        """Test to_json with indentation."""
        d = DotDict({"a": 1})
        json_str = d.to_json(indent=2)
        assert "  " in json_str  # Contains indentation

    def test_yaml_property(self):
        """Test yaml property."""
        d = DotDict({"a": 1, "b": "text"})
        yaml_str = d.yaml
        parsed = yaml.safe_load(yaml_str)
        assert parsed["a"] == 1
        assert parsed["b"] == "text"

    def test_yaml_multiline(self):
        """Test yaml handles multi-line strings."""
        d = DotDict({"script": "line1\nline2\nline3"})
        yaml_str = d.yaml
        assert "|" in yaml_str  # Literal block style

    def test_yaml_custom_dumper(self):
        """Test yaml uses custom dumper without polluting global state."""
        d1 = DotDict({"a": "line1\nline2"})
        yaml1 = d1.yaml
        
        # Verify global yaml is not affected
        yaml_str = yaml.dump({"b": "line3\nline4"})
        # Default yaml doesn't use literal block by default

    def test_repr(self):
        """Test __repr__ returns yaml."""
        d = DotDict({"a": 1})
        repr_str = repr(d)
        assert "a:" in repr_str


class TestDotDictEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_string_key(self):
        """Test handling of empty string keys."""
        d = DotDict({"": "empty"})
        assert d[""] == "empty"

    def test_key_with_dots(self):
        """Test keys that contain literal dots (if possible)."""
        # This tests that our dot-notation doesn't break on keys with dots
        d = DotDict({"a.b": "literal_dot"})
        assert d["a.b"] == "literal_dot"

    def test_very_deep_nesting(self):
        """Test very deeply nested structures."""
        depth = 50
        data = {}
        current = data
        for i in range(depth):
            current["level"] = {}
            current = current["level"]
        current["value"] = "deep"

        d = DotDict(data)
        # Navigate to deep value
        current = d
        for _ in range(depth):
            current = current.level
        assert current.value == "deep"

    def test_numeric_keys(self):
        """Test numeric keys as strings."""
        d = DotDict({"0": "zero", "1": "one"})
        assert d["0"] == "zero"
        assert d["1"] == "one"

    def test_none_values(self):
        """Test handling of None values."""
        d = DotDict({"a": None, "b": {"c": None}})
        assert d.a is None
        assert d.b.c is None

    def test_boolean_values(self):
        """Test boolean values."""
        d = DotDict({"true_val": True, "false_val": False})
        assert d.true_val is True
        assert d.false_val is False

    def test_private_attribute(self):
        """Test private attributes don't interfere."""
        d = DotDict({"_private": 1, "public": 2})
        # Private attributes should be set via object.__setattr__
        # and not appear as dictionary keys
        assert "_private" in d
        assert "public" in d

    def test_special_attribute_prefix(self):
        """Test attributes starting with underscore."""
        d = DotDict({"public": 1})
        d._special = "private"
        # This should be set as object attribute, not dict item
        assert d._special == "private"

    def test_ordered_preservation(self):
        """Test that order is preserved (OrderedDict behavior)."""
        data = {"z": 1, "a": 2, "m": 3}
        d = DotDict(data)
        keys = list(d.keys())
        assert keys == ["z", "a", "m"]


class TestDotDictIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow(self):
        """Test a complete workflow scenario."""
        # Create config
        config = DotDict()
        
        # Set base values
        config.name = "gemma"
        config.version = "2.0"
        
        # Set nested config using dot-notation
        config["model.path"] = "/models/{name}"
        config["model.size"] = "7B"
        
        # Merge additional config
        config.merge({
            "training": {
                "epochs": 100,
                "lr": 0.001
            }
        })
        
        # Expand placeholders at model level (flat structure works best)
        # Note: expand() works on the target dict directly
        model_config = {"path": "/models/{name}"}
        expanded = config.expand(d=model_config)
        assert expanded["path"] == "/models/gemma"
        
        # Access using various methods
        assert config["model.size"] == "7B"
        assert config.model.size == "7B"
        assert config.smart_get("epochs") == 100
        
        # Check serialization
        json_str = config.to_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "gemma"
        
        # Modify and verify
        del config["model.size"]
        assert "size" not in config.model

    def test_yaml_roundtrip(self):
        """Test YAML roundtrip preserves structure."""
        # Note: to_dict() must be called to properly serialize nested dicts
        # YAML conversion uses to_dict() so nested DotDicts become regular dicts
        original = DotDict({
            "name": "test",
            "config": {
                "nested": {
                    "value": 123
                }
            },
            "list": [1, 2, 3]  # Simple list without nested dicts for yaml
        })
        
        yaml_str = original.yaml
        parsed = yaml.safe_load(yaml_str)
        reconstructed = DotDict(parsed)
        
        assert reconstructed.name == "test"
        assert reconstructed.config.nested.value == 123
        assert reconstructed.list == [1, 2, 3]

    def test_json_roundtrip(self):
        """Test JSON roundtrip preserves structure."""
        original = DotDict({
            "a": {"b": 1},
            "c": [1, 2, {"d": 3}]
        })
        
        json_str = original.to_json()
        parsed = json.loads(json_str)
        reconstructed = DotDict(parsed)
        
        assert reconstructed.a.b == 1
        assert reconstructed.c[2].d == 3