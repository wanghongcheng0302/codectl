import json
from jsonschema import RefResolver
from pathlib import Path
from typing import Union
from deepmerge import always_merger


def recursive_resolve(base_uri: Union[str, Path], schema_file: Path) -> dict:
    """Recursively resolves all references in a JSON Schema file and merges them into a complete schema object.

    Args:
        base_uri (Union[str, Path]): The base URI of the JSON Schema file for resolving relative paths.
        schema_file (Path): The path to the JSON Schema file to be resolved.

    Returns:
        dict: The resolved complete schema object.

    Raises:
        FileNotFoundError: If the specified schema file does not exist.
    """

    # Convert base_uri to string format
    if isinstance(base_uri, Path):
        base_uri = f"file://{base_uri.resolve()}"

    # Read the JSON Schema file
    schema = json.loads(schema_file.read_text())

    # Create a resolver for resolving references
    resolver = RefResolver(base_uri, schema)

    # Recursively resolve all references
    resolve_all_refs(base_uri, schema, resolver)

    return schema


def resolve_all_refs(base_uri: str, schema: dict, resolver: RefResolver):
    """Recursively resolves all references in a JSON Schema and merges them into the schema object.

    Args:
        base_uri (str): The base URI of the JSON Schema for resolving relative paths.
        schema (dict): The JSON Schema object to resolve references.
        resolver (RefResolver): The resolver object for resolving references.
    """

    def _resolve_refs(subschema):
        if isinstance(subschema, dict):
            if "$ref" in subschema:
                # Resolve the reference
                with resolver.resolving(subschema["$ref"]) as resolved:
                    # Recursively resolve the resolved schema
                    resolve_all_refs(
                        base_uri, resolved, RefResolver(base_uri, resolved)
                    )
                    # Merge the resolved schema into the current schema
                    subschema = always_merger.merge(subschema, resolved)
                # Remove the $ref key from the schema
                if isinstance(subschema, dict):
                    subschema.pop("$ref")
            # Recursively resolve references in nested objects
            if isinstance(subschema, list):
                _resolve_refs(subschema)
            else:
                for value in subschema.values():
                    _resolve_refs(value)
        elif isinstance(subschema, list):
            # Recursively resolve references in lists
            for item in subschema:
                _resolve_refs(item)

    _resolve_refs(schema)
