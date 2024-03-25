"""Built-in configurations."""

from pathlib import Path

BASE_DIR = Path.home() / ".codectl"

CONFIG_PATH = BASE_DIR / "config.json"

CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
