import os
import platform
import re
import shlex
import sys
from pathlib import Path
from urllib.parse import urlsplit

from album.api import Album

from album.gui.include.pyshortcuts import make_shortcut
from album.gui.include.pyshortcuts.shortcut import fix_filename

DEFAULT_SHORTCUT_NAME = "Album"


def get_icon_path():
    if platform.system() == "Windows":
        return str(Path(__file__).parent / "resources" / "album_icon_windows.ico")
    elif platform.system() == "Darwin":
        return str(Path(__file__).parent / "resources" / "album_icon_macos.icns")
    elif platform.system() == "Linux":
        return str(Path(__file__).parent / "resources" / "album_icon_linux.png")


def get_shortcut_name(solution=None):
    """Return the name of the shortcut and of its launcher script: "Album" or "Album - <solution>"."""
    if not solution:
        return DEFAULT_SHORTCUT_NAME
    solution = str(solution)
    if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*://", solution):
        # a URL, its query (e.g. ?inline=false) and fragment are not part of the name
        url = urlsplit(solution)
        solution = url.netloc + url.path
    # paths and URLs are reduced to their last part, coordinates (group:name:version) are kept
    parts = [part for part in re.split(r"[\\/]", solution) if part]
    label = parts[-1] if parts else solution
    if label == "solution.py" and len(parts) > 1:
        # solution files are usually called solution.py, the folder name is more telling
        label = parts[-2]
    if label.endswith(".py"):
        label = label[:-3]
    return fix_filename("%s - %s" % (DEFAULT_SHORTCUT_NAME, label))


def create_shortcut(album_instance: Album, args=None, command="album gui"):
    solution = getattr(args, "solution", None)
    if solution and os.path.exists(solution):
        # the shortcut does not run in the current working directory, a relative path would not resolve
        solution = os.path.abspath(solution)
    album_base_path = album_instance.configuration().base_cache_path()
    album_environment_path = album_base_path.joinpath("envs", "album")
    if not Path(album_environment_path).exists():
        # if album is installed at a different place, this should catch it
        album_environment_path = sys.prefix
    package_manager = album_instance._controller.environment_manager().get_environment_handler().get_package_manager().get_install_environment_executable()
    solution_environments_path = album_instance.configuration().environments_path()
    _create_shortcut_from_environment_and_executable(
        album_base_path,
        album_environment_path,
        solution_environments_path,
        package_manager,
        command,
        solution,
    )


def _create_shortcut_from_environment_and_executable(
    album_base_path,
    album_environment_path,
    environments_location,
    package_manager,
    command,
    solution=None,
):
    env_vars = {
        "ALBUM_BASE_CACHE_PATH": str(album_base_path),
    }
    if "micromamba" in str(package_manager).lower():
        env_vars["MAMBA_ROOT_PREFIX"] = str(environments_location)

    icon_path = get_icon_path()
    name = get_shortcut_name(solution)

    if platform.system() == "Windows":
        script_command = " ".join(
            [_quote_batch(package_manager), "run", "-p", _quote_batch(album_environment_path), command]
            + ([_quote_batch(solution)] if solution else [])
        )
        script_file_path = Path(album_base_path).joinpath("%s.bat" % name)
        write_batch_file(script_file_path, env_vars, script_command)
        make_shortcut(
            # cmd.exe /C strips the outer quotes, the inner ones keep paths with spaces and special characters intact
            '""%s""' % script_file_path,
            name=name,
            icon=icon_path,
            terminal=False,
            executable="C:\\Windows\\System32\\cmd.exe",
        )
    else:  # MacOS and Linux
        if platform.system() == "Darwin":
            # the launcher of the .app runs: export EXE=<exec>; export SCRIPT=<script>; eval "$EXE $SCRIPT $ARGS"
            quote = shlex.quote
        else:
            # the .desktop file runs: Exec=<exec> <script>
            quote = _quote_desktop_exec_argument
        envs = ["env"]
        envs += [quote(f"{var}={value}") for var, value in env_vars.items()]
        exec = " ".join(envs + [quote(str(package_manager))])
        script_command = " ".join(
            ["run", "-p", quote(str(album_environment_path)), command] + ([quote(solution)] if solution else [])
        )
        if platform.system() == "Darwin":
            exec = shlex.quote(exec)
            script_command = shlex.quote(script_command)
        make_shortcut(
            script_command,
            name=name,
            icon=icon_path,
            terminal=False,
            executable=exec,
        )


def write_batch_file(batch_file_path, env_vars, command):
    with open(batch_file_path, "w") as f:
        for var, value in env_vars.items():
            # the quotes keep spaces and special characters like & in the value without becoming part of it
            f.write('set "%s=%s"\n' % (var, _escape_batch(value)))
        f.write(command + "\n")


def _escape_batch(value):
    # % starts a variable in batch files, %% is a literal %
    return str(value).replace("%", "%%")


def _quote_batch(value):
    return '"%s"' % _escape_batch(value)


def _quote_desktop_exec_argument(value):
    """Quote an argument for the Exec key of a .desktop file.

    See https://specifications.freedesktop.org/desktop-entry-spec/latest/exec-variables.html
    """
    value = str(value)
    for char in ("\\", '"', "`", "$"):
        value = value.replace(char, "\\" + char)
    # the general string escaping of the file format (\\ is a backslash) is applied before the quoting rules
    value = value.replace("\\", "\\\\")
    # % starts a field code, %% is a literal %
    return '"%s"' % value.replace("%", "%%")
