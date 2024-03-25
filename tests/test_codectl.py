import subprocess
from pathlib import Path
import json
import shutil


manage_py = (Path("codectl") / "manage.py").resolve()
template_dir = Path(".codectl") / "templates"


def set_template_dir():
    return subprocess.run(
        [
            "python",
            manage_py,
            "config",
            "--set",
            "-i",
            f"template_dir={template_dir}",
        ],
        capture_output=True,
        text=True,
    )


def test_config(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = subprocess.run(
        ["python", manage_py, "config", "--help"], capture_output=True, text=True
    )
    assert not result.stderr

    result = subprocess.run(
        ["python", manage_py, "config", "--show"], capture_output=True, text=True
    )
    assert result.stdout.strip() == "{}" and not result.stderr

    result = set_template_dir()
    assert (
        result.stdout.strip() == "Configuration updated successfully."
        and not result.stderr
    )

    result = subprocess.run(
        ["python", manage_py, "config", "--show"], capture_output=True, text=True
    )
    assert (
        json.loads(result.stdout) == {"template_dir": str(template_dir)}
        and not result.stderr
    )


def test_new(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = set_template_dir()
    assert (
        result.stdout.strip() == "Configuration updated successfully."
        and not result.stderr
    )

    result = subprocess.run(
        ["python", manage_py, "new", "--help"], capture_output=True, text=True
    )
    assert not result.stderr

    result = subprocess.run(
        ["python", manage_py, "new", "a"], capture_output=True, text=True
    )
    assert (
        result.stdout.strip()
        == "Template directory does not exist or is not configured. Please run `codectl config --set template_dir=<path>` to configure."
        and not result.stderr
    )

    shutil.copytree(Path("templates"), Path.home() / template_dir)

    result = subprocess.run(
        ["python", manage_py, "new", "a"], capture_output=True, text=True, cwd=tmp_path
    )
    assert (
        result.stdout.strip() == "Application instance created successfully."
        and not result.stderr
    )

    result = subprocess.run(
        ["python", manage_py, "new", "a", "-d", "system=centos"], capture_output=True, text=True, cwd=tmp_path
    )

    lines = result.stdout.splitlines()
    assert (
        len(lines) == 3
        and lines[0] == "The a2/a2.txt file already exists and will be ignored."
        and lines[1] == "The a1/a1.txt file already exists and will be ignored."
        and lines[2] == "Application instance created successfully."
    )
    assert (
        (tmp_path / "a.txt").read_text() == "V1.1.0\ncentos"
        and (tmp_path / "a1" / "a1.txt").read_text() == "V1.1.0"
        and (tmp_path / "a2" / "a2.txt").read_text() == "V1.1.0"
    )

    result = subprocess.run(
        ["python", manage_py, "new", "b"], capture_output=True, text=True, cwd=tmp_path
    )
    assert (
        result.stdout.strip() == "Application instance created successfully."
        and not result.stderr
    )

    assert (
        tmp_path / "apis" / "login.ts"
    ).read_text().strip() == "export const login = () => {\n\n}\n\nexport const logout = () => {\n\n}" and (
        tmp_path / "types" / "user_login_request.ts"
    ).read_text().strip() == "interface UserLoginRequest {\n    \n}\n\ninterface UserLoginResponse {\n    \n}"


def test_update(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = set_template_dir()
    assert (
        result.stdout.strip() == "Configuration updated successfully."
        and not result.stderr
    )

    shutil.copytree(Path("templates"), Path.home() / template_dir)

    result = subprocess.run(
        ["python", manage_py, "new", "a", "-o", "out"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert (
        result.stdout.strip() == "Application instance created successfully."
        and not result.stderr
    )

    result = subprocess.run(
        ["python", manage_py, "update", f"{tmp_path / 'out'}"],
        capture_output=True,
        text=True,
        cwd=tmp_path / "out",
    )

    lines = result.stdout.splitlines()
    assert (
        lines[0] == "The a2/a2.txt file already exists and will be ignored."
        and lines[1] == "The a1/a1.txt file already exists and will be ignored."
        and lines[2] == "Files have been updated successfully."
    )

