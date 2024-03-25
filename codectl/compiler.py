"""Compiler module
"""

import json
import os
import shutil
import copy
from pathlib import Path
from typing import Tuple
import click
from jinja2 import Environment, FileSystemLoader
from codectl import utils
from codectl import jinja
from codectl.schema import recursive_resolve


def load_associated_schema(tmpl_path: Path) -> Tuple[dict, Path]:
    """Load the associated JSON schema for a given template file.

    Args:
        tmpl_path (Path): The path to the template file.

    Returns:
        dict: A dictionary representing the loaded JSON schema.
    """
    schema_path = tmpl_path.with_suffix(".schema")
    schema = json.loads(schema_path.read_text()) if schema_path.is_file() else {}
    return schema, schema_path


def get_output_dir(tmpl_path: Path, tmpl_root_dir: Path, output: Path) -> Path:
    """Determine the output directory for the rendered template based on the template path,
    template directory.

    Args:
        tmpl_path (Path): The path to the template file.
        tmpl_dir (Path): The root directory of the template files.

    Returns:
        Path: The path to the output directory.
    """
    rel_path = tmpl_path.parent.relative_to(tmpl_root_dir)
    return output / rel_path


def copy_file(source: Path, dest: Path):
    """Copy a file from the source path to the destination path.

    Args:
        source (Path): The path to the source file.
        dest (Path): The path to the destination file.
    """
    if source == dest:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, dest)


def process_file(
    env: Environment,
    loader: FileSystemLoader,
    tmpl_path: Path,
    schemas: dict,
    output: Path,
):
    """Process a single file template, render it with the provided schemas,
    and save the output to the designated directory.

    Args:
        env (Environment): The Jinja2 environment.
        loader (FileSystemLoader): The Jinja2 loader.
        tmpl_path (Path): The path to the template file.
        schemas (dict): A dictionary containing data to be used in the template rendering.
    """
    schema, schema_path = load_associated_schema(tmpl_path)
    schemas.update(schema)

    searchpath = loader.searchpath[0]
    searchpath = Path(searchpath)
    tmpl_fullname = tmpl_path.relative_to(searchpath)
    tmpl = env.get_template(str(tmpl_fullname))
    content = tmpl.render(**schemas)

    output_dir = get_output_dir(tmpl_path, searchpath, output)

    tmpl_ = jinja.create_string_template(tmpl_path.stem)
    filename = tmpl_.render(schemas)
    filepath = output_dir / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    update = schemas.get("_update", False)
    if filepath.is_file() and not update:
        click.secho(
            f"The {filepath.relative_to(output)} file already exists and will be ignored.",
            fg="yellow",
        )
        return
    filepath.write_text(content)


def process_files(
    env: Environment,
    loader: FileSystemLoader,
    tmpl_path: Path,
    schemas: dict,
    output: Path,
):
    """Process files with an iterator, rendering each element with the template and
    saving the outputs to the designated directory.

    Args:
        env (Environment): The Jinja2 environment.
        loader (FileSystemLoader): The Jinja2 loader.
        tmpl_path (Path): The path to the template file.
        schemas (dict): A dictionary containing data to be used in the template rendering.
    """
    schema, schema_path = load_associated_schema(tmpl_path)
    schemas.update(schema)

    searchpath = loader.searchpath[0]
    searchpath = Path(searchpath)

    output_dir = get_output_dir(tmpl_path, searchpath, output)

    iter_key = schemas.get("_iter")
    if iter_key:
        elements = utils.retrieve_nested_value(schemas, iter_key) or []
        _iter_filter = schemas.get("_iter_filter")
        if _iter_filter and _iter_filter in env.filters:
            elements = env.filters[_iter_filter](elements)

    for elem in elements:
        schemas_copy = {"_": elem, **schemas}
        tmpl_ = jinja.create_string_template(tmpl_path.stem)
        filename = tmpl_.render(schemas_copy)
        filepath = output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        process_file(env, loader, tmpl_path, schemas_copy, output)


def merge_and_export_schemas(
    tmpl_root_dir: Path, output: Path, schemas: dict = {}
) -> dict:
    """
    Merges schemas found in the template root directory with the provided schemas
    dictionary and exports the merged schema to the output directory.

    Args:
        tmpl_root_dir (Path): The root directory containing schema files.
        output (Path): The directory to export the merged schema.
        schemas (dict): A dictionary containing existing schemas.

    Returns:
        dict: The updated schemas dictionary after merging.

    """
    filename = "schema.schema"
    schema_path = tmpl_root_dir / filename

    if schema_path.is_file():
        # Load schema from the schema file
        schema = recursive_resolve(schema_path.parent, schema_path)

        # Update schemas with the loaded schema
        schemas.update(schema)

    return schemas


def process_directory(tmpl_root_dir: Path, output: Path, schemas: dict = {}):
    """Process a directory of templates, including single file templates,
    multi-file templates with iterators, and static files.

    Args:
        tmpl_dir (Path): The path to the directory containing the template files.
        schemas (dict): A dictionary containing global data to be used across all templates.
    """
    env, loader = jinja.create_filesys_env(tmpl_root_dir)
    schemas = merge_and_export_schemas(tmpl_root_dir, output, schemas)
    env.globals.update(schemas)

    handlers_py = tmpl_root_dir / "handlers.py"
    if handlers_py.is_file():
        for name, filter_ in utils.load_jinja_filters(handlers_py):
            env.filters[name] = filter_
        for name, global_ in utils.load_jinja_globals(handlers_py):
            env.globals[name] = global_

    for root, _, files in os.walk(tmpl_root_dir):
        root = Path(root)

        for file in files:
            file = root / file
            if file.name == "types.schema":
                pass
            schemas_copy = copy.deepcopy(schemas)
            if file.suffix == ".tpl":
                process_file(env, loader, file, schemas_copy, output)
            elif file.suffix == ".mtpl":
                process_files(env, loader, file, schemas_copy, output)
            dest = get_output_dir(file, tmpl_root_dir, output) / file.name
            copy_file(file, dest)
