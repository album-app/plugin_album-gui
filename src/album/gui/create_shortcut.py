import platform
import sys
from pathlib import Path

from album.api import Album

from album.gui.include.pyshortcuts import make_shortcut


def get_icon_path():
    if platform.system() == 'Windows':
        return str(Path(__file__).parent / 'resources' / 'album_icon_windows.ico')
    elif platform.system() == 'Darwin':
        return str(Path(__file__).parent / 'resources' / 'album_icon_macos.icns')
    elif platform.system() == 'Linux':
        return str(Path(__file__).parent / 'resources' / 'album_icon_linux.png')


def create_shortcut(album_instance: Album, args=None, command="album gui"):
    album_base_path = album_instance.configuration().base_cache_path()
    album_environment_path = album_base_path.joinpath('envs', 'album')
    if not Path(album_environment_path).exists():
        # if album is installed at a different place, this should catch it
        album_environment_path = sys.prefix
    micromamba_executable = album_instance.configuration().micromamba_executable()
    if micromamba_executable:
        package_manager = micromamba_executable
    else:
        package_manager = album_instance.configuration().conda_executable()
    solution_environments_path = album_instance.configuration().environments_path()
    _create_shortcut_from_environment_and_executable(album_base_path, album_environment_path, solution_environments_path, package_manager, command)


def _create_shortcut_from_environment_and_executable(album_base_path, album_environment_path, environments_location, package_manager, command):
    env_vars = {
        "ALBUM_CONDA_PATH": str(package_manager),
        "ALBUM_BASE_CACHE_PATH": str(album_base_path),
    }
    if "micromamba" in str(package_manager).lower():
        env_vars["MAMBA_ROOT_PREFIX"] = str(environments_location)

    icon_path = get_icon_path()

    if platform.system() == 'Windows':
        script_command = f"{package_manager} run -p \"{album_environment_path}\" {command}"
        script_file_path = Path(album_base_path).joinpath("Album.bat")
        with open(script_file_path, 'w') as f:
            for var, value in env_vars.items():
                f.write(f"set {var}={value}\n")
            f.write(script_command + "\n")
        make_shortcut(str(script_file_path), name='Album', icon=icon_path, terminal=False, executable="C:\\Windows\\System32\\cmd.exe")
    else:  # For MacOS and Linux, keep as it is
        script_command = f"run -p {album_environment_path} {command}"
        envs = ["env"]
        envs += [f"{var}={value}" for var, value in env_vars.items()]
        exec = " ".join(envs + [str(package_manager)])
        if platform.system() == 'Darwin':
            exec = "\'%s\'" % exec
            script_command = "\'%s\'" % script_command
        make_shortcut(script_command, name='Album', icon=icon_path, terminal=False, executable=exec)


def write_batch_file(batch_file_path, env_vars, command):
    with open(batch_file_path, 'w') as f:
        for var, value in env_vars.items():
            f.write(f"set {var}={value}\n")
        f.write(command + "\n")
