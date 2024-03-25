"""A command-line tool for generating code based on templates."""

from pathlib import Path
import json
from typing import Union, Optional, Tuple
import click
from codectl import compiler, settings
from codectl import utils


@click.group()
def cli():
    """
    Base command group for the CLI application.
    """
    pass


@cli.command()
@click.option(
    "--set",
    is_flag=True,
    help="Enables the configuration setting mode. Use in conjunction with --items to specify key-value pairs to update the configuration.",
)
@click.option(
    "--show",
    is_flag=True,
    help="Displays the current configuration in a JSON format. Enabled by default if no other option is specified.",
)
@click.option(
    "--items",
    "-i",
    multiple=True,
    type=str,
    help="Specifies the configuration items to set or update, formatted as key=value. This option requires --set to be effective. Multiple items can be specified by using -i multiple times.",
)
def config(set: bool, show: bool, items: Tuple[str]):
    """
    Manages user configuration settings.

    This command allows users to set, update, and display their configuration settings.
    The settings are stored in a JSON format and can be modified by specifying key-value
    pairs. The current configuration can be displayed by using the --show option.

    Args:
        set (bool): If True, enables the mode to set or update configuration items. Must be used in conjunction with --items.
        show (bool): If True, displays the current configuration. This is the default action if no other option is provided.
        items (Tuple[str]): A tuple of strings representing the configuration items to be set or updated, formatted as key=value. Required if --set is used.

    Examples:
        - codectl config --set -i template_dir=~/.codectl/templates

        - codectl config --show # Display the current configuration:  

    Note:
        - The configuration is saved to a JSON file specified by `settings.CONFIG_PATH`.
        - Ensure the key names provided in --items are valid and recognized by the application.
    """
    user_config = utils.get_user_config()

    if set:
        for item in items:
            key, value = item.split("=")
            user_config[key] = value

        settings.CONFIG_PATH.write_text(
            json.dumps(user_config, indent=2, ensure_ascii=False)
        )

        if not show:
            click.secho("Configuration updated successfully.", fg="green")

    if show or not set:
        click.secho(json.dumps(user_config, indent=2), fg="green")


@cli.command()
@click.argument("app", type=str)
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=False, file_okay=False),
    help="Specify the directory where the new application instance should be created. Defaults to the current working directory if not provided.",
)
@click.option(
    "--data",
    "-d",
    multiple=True,
    type=str,
    help="Key-value pairs for template data substitution, formatted as key=value. For example, 'author=Jane Doe'. Multiple -d options can be specified.",
)
def new(app: str, output: str | Path, data: tuple):
    """
    Creates a new application instance from a specified template.

    This command takes an application template name and generates a new application instance from it. The new instance is created in the specified output directory (or the current working directory if not specified). The command allows for dynamic data substitution in the template files based on the provided key-value pairs.

    Args:
        app (str): The name of the application template to use. This name should match a directory within the configured template directory.
        output (str | Path): The path to the directory where the new application instance will be created. If omitted, the current working directory is used.
        data (tuple): A collection of key-value pairs (as strings) to be used for data substitution in the template. Each pair should be formatted as 'key=value'.

    Examples:

        - codectl new myapp --output ~/projects/myapp -d name=MyApp

    Note:
        Before using this command, ensure that the template directory is configured correctly with `codectl config --set template_dir=<path>`.
    """
    user_config = utils.get_user_config()
    template_dir = Path(user_config.get("template_dir", "")).expanduser().resolve()
    if not template_dir.exists():
        click.secho(
            "Template directory does not exist or is not configured. Please run `codectl config --set template_dir=<path>` to configure.",
            fg="red",
        )
        return

    output = Path(output) if output else Path.cwd()
    output.mkdir(parents=True, exist_ok=True)

    app_template_dir = template_dir / app
    if not app_template_dir.exists():
        click.secho(
            f"App template directory ({app}) does not exist in the template directory.",
            fg="red",
        )
        return

    schemas = dict((item.split("=") for item in data))
    compiler.process_directory(app_template_dir, output=output, schemas=schemas)
    click.secho("Application instance created successfully.", fg="green")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option(
    "--data",
    "-d",
    multiple=True,
    type=str,
    help="Key-value pairs for data substitution within the specified directory, formatted as key=value. For example, 'title=New Title'. Multiple -d options can be specified for different substitutions.",
)
def update(directory: Path, data: tuple):
    """
    Updates files in the specified directory based on the provided key-value pairs.

    This command applies data substitutions to files within a given directory, according to the specified key-value pairs. It's designed to update template-based files by replacing placeholder tags with actual data values.

    Args:
        directory (Path): The path to the directory containing the files to be updated. The directory must exist.
        data (tuple): A collection of key-value pairs (as strings) for data substitution. Each pair should be formatted as 'key=value'.

    Examples:

        - codectl update ~/projects/myapp -d version=2.0.0
    """
    directory = Path(directory)
    schemas = dict(item.split("=") for item in data)
    compiler.process_directory(directory, output=directory, schemas=schemas)
    click.secho("Files have been updated successfully.", fg="green")


if __name__ == "__main__":
    cli()

"""debug cases
python codectl/manage.py --help

python codectl/manage.py config --help
python codectl/manage.py config --show
python codectl/manage.py config --set -i template_dir=~/workspace/code/codectl/templates

python codectl/manage.py new --help
python codectl/manage.py new a -o ./out -d system=centos
python codectl/manage.py new b -o ./out

python codectl/manage.py update --help
python codectl/manage.py update ./out

python -m pytest tests

"""
