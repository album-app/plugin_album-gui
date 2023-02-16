import platform
import shutil
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


def create_shortcut(album_instance: Album, args):
    # FIXME determine where current album environment is located
    album_base_path = album_instance.configuration().base_cache_path()
    album_environment_path = album_base_path.joinpath('envs', 'album')
    micromamba_executable = album_instance.configuration().micromamba_executable()
    if micromamba_executable:
        package_manager = micromamba_executable
    else:
        package_manager = album_instance.configuration().conda_executable()
    script_path = " ".join(['run', '-p', str(album_environment_path), 'album', 'gui'])
    exec = " ".join([package_manager])
    icon_path = get_icon_path()
    make_shortcut(script_path, name='Album', icon=icon_path, executable=exec, terminal=False)
