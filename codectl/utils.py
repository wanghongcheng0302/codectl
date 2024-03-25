from pathlib import Path
import sys
import inspect
import importlib
import json
from typing import Iterable, Callable, Tuple
from functools import reduce
from operator import getitem
from codectl import settings


def retrieve_nested_value(dictionary: dict, key_path: str):
    """
    Retrieve a nested value from a dictionary using a dot-separated key path.

    Args:
        dictionary (dict): The dictionary to retrieve the value from.
        key_path (str): The dot-separated key path to the nested value.

    Returns:
        The value retrieved from the dictionary using the provided key path.

    Example:
        >>> data = {'a': {'b': {'c': 42}}}
        >>> value = retrieve_nested_value(data, 'a.b.c')
        >>> print(value)
        42
    """

    return reduce(getitem, key_path.split("."), dictionary)


def get_user_config() -> dict:
    """
    Retrieve the user configuration settings.

    Loads the configuration from the JSON file specified by `settings.CONFIG_PATH`.
    If the configuration file does not exist, it creates an empty JSON file at that location.

    Returns:
        dict: A dictionary containing the configuration settings. Returns an empty dictionary
              if the configuration file is newly created or contains no settings.

    Example:
        >>> config = get_user_config()
        >>> print(config)
        {'setting1': 'value1', 'setting2': 'value2'}
    """

    config = {}

    if settings.CONFIG_PATH.is_file():
        config.update(json.loads(settings.CONFIG_PATH.read_text()))
    else:
        settings.CONFIG_PATH.write_text("{}")

    return config


def load_priv_funcs_from_mod(module_path: Path) -> Iterable[Tuple[str, Callable]]:
    """
    Load private functions from a Python module.

    Imports a module by file path and returns private functions (functions with names starting with "_").
    Modifies `sys.path` if necessary for import.

    Args:
        module_path (Path): The path to the Python module file.

    Returns:
        Iterable of (str, Callable) tuples for each private function found in the module.

    Example:
        >>> funcs = load_priv_funcs_from_mod(Path('/path/to/module.py'))
        >>> for name, func in funcs:
        ...     print(name, func)
    """

    if module_path.parent not in sys.path:
        sys.path.append(str(module_path.parent))

    module = importlib.import_module(module_path.stem)

    return inspect.getmembers(module)


def load_jinja_filters(module_path: Path) -> Iterable[Tuple[str, Callable]]:
    """
    Load Jinja2 filter functions from a Python module.

    Args:
        module_path (Path): The path to the Python module containing filter functions.

    Returns:
        Iterable of (str, Callable) tuples for each Jinja2 filter function found in the module.

    Example:
        >>> filters = load_jinja_filters(Path('/path/to/filters.py'))
        >>> for name, func in filters:
        ...     print(name, func)
    """

    members = load_priv_funcs_from_mod(module_path)
    return (mem for mem in members if mem[0].startswith("filter_"))


def load_jinja_globals(module_path: Path) -> Iterable[Tuple[str, Callable]]:
    """
    Load Jinja2 global functions from a Python module.

    Args:
        module_path (Path): The path to the Python module containing global functions.

    Returns:
        Iterable of (str, Callable) tuples for each Jinja2 global function found in the module.

    Example:
        >>> globals = load_jinja_globals(Path('/path/to/globals.py'))
        >>> for name, func in globals:
        ...     print(name, func)
    """

    members = load_priv_funcs_from_mod(module_path)
    return (mem for mem in members if mem[0].startswith("global_"))
