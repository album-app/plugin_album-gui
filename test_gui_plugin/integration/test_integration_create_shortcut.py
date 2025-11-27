import configparser
import os
import platform
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from album.api import Album

from album.gui.create_shortcut import create_shortcut
from album.gui.include.pyshortcuts import UserFolders


class TestIntegrationCreateShortcut(unittest.TestCase):

    @unittest.skipIf(platform.system() != "Linux", "Only runs on Linux")
    @patch("album.gui.include.pyshortcuts.linux.get_folders")
    def test_create_shortcut_linux(self, get_folders):

        with tempfile.TemporaryDirectory() as temp_dir:

            album = Album.Builder().base_cache_path(Path(temp_dir).joinpath("album")).build()

            temp_dir = Path(temp_dir)

            folders = UserFolders(temp_dir.joinpath("home"), temp_dir.joinpath("desktop"), temp_dir.joinpath("task_menu"))
            get_folders.return_value = folders

            create_shortcut(album, command="album gui --help")

            desktop_file = folders.desktop.joinpath("Album.desktop")
            self.assertTrue(desktop_file.exists())

            config = configparser.ConfigParser(strict=False)
            config.read(desktop_file)

            exec_command = config.get('Desktop Entry', 'Exec', fallback='')

            self.assertIsNotNone(exec_command)
            result = subprocess.run(shlex.split(exec_command), capture_output=True, text=True, check=True, env={})
            stdout = result.stdout
            self.assertIn("usage: album gui", stdout)

            solution_path = str(Path(__file__).parent.parent / 'resources' / 'test_solution.py')

            exec_command = exec_command.replace("gui --help", " install %s" % solution_path)
            result = subprocess.run(shlex.split(exec_command), capture_output=True, text=True, check=True, env={})
            stdout = result.stdout
            self.assertIn("Installed name!", stdout)

    @staticmethod
    def print_directory_contents(path):
        for dirpath, dirnames, filenames in os.walk(path):
            print(f"Found directory: {dirpath}")
            for dirname in dirnames:
                print(f"Subdirectory: {os.path.join(dirpath, dirname)}")
            for filename in filenames:
                print(f"File: {os.path.join(dirpath, filename)}")

    @unittest.skipIf(platform.system() != "Windows", "Only runs on Windows")
    @patch("album.gui.include.pyshortcuts.windows.get_folders")
    def test__create_shortcut_from_environment_and_executable_windows(self, get_folders):

        with tempfile.TemporaryDirectory() as temp_dir:

            base_cache_path = Path(temp_dir).joinpath("album")
            album = Album.Builder().base_cache_path(base_cache_path).build()

            temp_dir = Path(temp_dir)

            folders = UserFolders(str(temp_dir.joinpath("home")), str(temp_dir.joinpath("desktop")), str(temp_dir.joinpath("task_menu")))
            get_folders.return_value = folders

            create_shortcut(album, command="album gui --help")

            self.print_directory_contents(temp_dir)
            bat_file = Path(base_cache_path).joinpath("Album.bat")
            self.assertTrue(bat_file.exists())

            # make sure that the variables are not set already to ensure they are correctly set in the bat file
            env_copy = os.environ.copy()
            for var in ['ALBUM_CONDA_PATH', 'ALBUM_BASE_CACHE_PATH', 'MAMBA_ROOT_PREFIX']:
                env_copy.pop(var, None)

            try:
                result = subprocess.run(['cmd', '/c', str(bat_file)], shell=True, check=True, capture_output=True, text=True, env=env_copy)
            except subprocess.CalledProcessError as e:
                self.fail('Error: %s' % e)

            stdout = result.stdout
            # "usage: album gui [...]"" is now "usage: album python.exe [<temp path>] album gui [...] 
            # -> checking for a another part of the output 
            self.assertIn("[-h] [--log LOG] [--json] [--version] [solution]", stdout) 

            desktop_file = Path(folders.desktop).joinpath("Album.lnk")
            self.assertTrue(desktop_file.exists())

            solution_path = str(Path(__file__).parent.parent / 'resources' / 'test_solution.py')

            create_shortcut(album, command="album install %s" % solution_path)

            try:
                result = subprocess.run(['cmd', '/c', str(bat_file)], shell=True, check=True, capture_output=True, text=True, env=env_copy)
            except subprocess.CalledProcessError as e:
                self.fail('Error: %s' % e)
            stdout = result.stdout
            self.assertIn("Installed name!", stdout)

    @unittest.skipIf(platform.system() != "Darwin", "Only runs on macOS")
    @patch("album.gui.include.pyshortcuts.darwin.get_folders")
    def test__create_shortcut_from_environment_and_executable_macos(self, get_folders):

        with tempfile.TemporaryDirectory() as temp_dir:

            album = Album.Builder().base_cache_path(Path(temp_dir).joinpath("album")).build()

            temp_dir = Path(temp_dir)

            folders = UserFolders(str(temp_dir.joinpath("home")), str(temp_dir.joinpath("desktop")), str(temp_dir.joinpath("task_menu")))
            get_folders.return_value = folders

            create_shortcut(album, command="album gui --help")


            app_path = Path(folders.desktop).joinpath("Album.app")
            self.assertTrue(app_path.exists())
            startup_script_path = app_path.joinpath('Contents', 'MacOS', 'Album')
            self.assertTrue(startup_script_path.exists())

            with open(str(startup_script_path), 'r') as file:
                startup_script = file.read()

            script_path = str(temp_dir.joinpath('script.sh'))
            with open(script_path, 'w') as file:
                file.write(startup_script)

            Path(script_path).chmod(Path(script_path).stat().st_mode | 0o111)
            try:
                result = subprocess.run(['bash', script_path], capture_output=True, text=True, check=True, env={})
            except subprocess.CalledProcessError as e:
                error_message = f"Command {e.cmd} failed with error code {e.returncode}\nStandard Error Output: {e.stderr}"
                self.fail(error_message)

            stdout = result.stdout
            self.assertIn("usage: album gui", stdout)

            solution_path = str(Path(__file__).parent.parent / 'resources' / 'test_solution.py')

            modified_script = startup_script.replace("album gui --help", "album install %s" % solution_path)
            with open(script_path, 'w') as file:
                file.write(modified_script)

            try:
                result = subprocess.run(['bash', script_path], capture_output=True, text=True, check=True, env={})
            except subprocess.CalledProcessError as e:
                error_message = f"Command {e.cmd} failed with error code {e.returncode}\nStandard Error Output: {e.stderr}"
                self.fail(error_message)
            stdout = result.stdout
            self.assertIn("Installed name!", stdout)
