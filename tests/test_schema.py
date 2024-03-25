import json
from codectl.schema import recursive_resolve


def test_resolve_schema(tmp_path):
    schema_a_path = tmp_path / "a.json"
    schema_b_path = tmp_path / "b.json"
    schema_c_path = tmp_path / "c.json"

    schema_dirname = tmp_path.name

    schema_a = {
        "$ref": f"{schema_dirname}/b.json#/definitions/user",
        "properties": {
            "gender": {"type": "string", "enum": ["male", "female", "other"]}
        },
    }
    schema_b = {
        "definitions": {"user": {"$ref": f"{schema_dirname}/c.json#/definitions/user"}}
    }
    schema_c = {
        "definitions": {
            "user": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            }
        }
    }
    schema_a_path.write_text(json.dumps(schema_a))
    schema_b_path.write_text(json.dumps(schema_b))
    schema_c_path.write_text(json.dumps(schema_c))

    schema = recursive_resolve(tmp_path, schema_a_path)

    assert schema == {
        "properties": {
            "gender": {"type": "string", "enum": ["male", "female", "other"]},
            "name": {"type": "string"},
            "age": {"type": "number"},
        },
        "type": "object",
    }
