import platform
import shutil
from pathlib import Path

from album.api import Album
from album.core.api.controller.environment_manager import IEnvironmentManager

from album.gui.include.pyshortcuts import make_shortcut


def get_icon_path():
    if platform.system() == 'Windows':
        return str(Path(__file__).parent / 'resources' / 'album_icon_windows.ico')
    elif platform.system() == 'Darwin':
        return str(Path(__file__).parent / 'resources' / 'album_icon_macos.icns')
    elif platform.system() == 'Linux':
        return str(Path(__file__).parent / 'resources' / 'album_icon_linux.png')


def create_shortcut(album_instance: Album, args):
    # FIXME determine where current album environment is located
    album_base_path = album_instance.configuration().base_cache_path()
    album_environment_path = album_base_path.joinpath('envs', 'album')
    micromamba_executable = album_instance.configuration().micromamba_executable()
    if micromamba_executable:
        package_manager = micromamba_executable
    else:
        package_manager = album_instance.configuration().conda_executable()
    _create_shortcut_from_environment_and_executable(album_environment_path, package_manager)


def _create_shortcut_from_environment_and_executable(album_environment_path, package_manager):
    script_path = " ".join(['run', '-p', str(album_environment_path), 'album', 'gui'])
    envs = ["env", "ALBUM_CONDA_PATH=%s" % package_manager]
    if "micromamba" in str(package_manager).lower():
        envs.append("MAMBA_ROOT_PREFIX=%s" % Path(album_environment_path).parent)
    exec = " ".join(envs + [package_manager])
    icon_path = get_icon_path()
    make_shortcut(script_path, name='Album', icon=icon_path, executable=exec, terminal=False)
