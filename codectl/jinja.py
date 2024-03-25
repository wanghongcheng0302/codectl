"""Jinja2 Utility Functions"""

from pathlib import Path
from typing import Tuple
from jinja2.environment import Environment
from jinja2.loaders import FileSystemLoader
from jinja2 import Template
from case_convert import snake_case, camel_case, pascal_case


def create_filesys_env(searchpath: Path) -> Tuple[Environment, FileSystemLoader]:
    """Sets up a Jinja2 Environment with custom filters and loop controls.

    Initializes a Jinja2 Environment for rendering templates, equipped with a
    FileSystemLoader based on the provided search path. Adds loop control extensions
    and filters for string case conversion (snake_case, camel_case, pascal_case),
    enhancing template text manipulation capabilities.

    Args:
        searchpath (Path): The directory path used to locate templates.

    Returns:
        A tuple containing the configured Jinja2 Environment and FileSystemLoader,
        ready for template loading and rendering.

    Example:
        >>> env, loader = create_filesys_env(Path("/path/to/templates"))
        >>> template = env.get_template("my_template.html")
        >>> print(template.render(my_data))
    """

    loader = FileSystemLoader(searchpath)
    env = Environment(loader=loader)
    env.add_extension("jinja2.ext.loopcontrols")
    env.filters["snake_case"] = snake_case
    env.filters["camel_case"] = camel_case
    env.filters["pascal_case"] = pascal_case
    return env, loader


def create_string_template(source: str) -> Template:
    """
    Creates a Jinja2 Template object from a string source.

    This function instantiates a Jinja2 Environment without a specific loader and
    uses it to create a Template object directly from the provided string source.
    This is useful for cases where template content is dynamically defined or
    obtained from non-file sources.

    Args:
        source (str): The string containing the Jinja2 template code.

    Returns:
        A Jinja2 Template object ready for rendering with context data.

    Example:
        >>> template = create_string_template("Hello, {{ name }}!")
        >>> print(template.render({"name": "World"}))
        Hello, World!
    """

    env = Environment()
    return env.from_string(source)
