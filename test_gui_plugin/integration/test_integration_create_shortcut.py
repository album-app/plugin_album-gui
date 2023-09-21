import configparser
import os
import platform
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from album.api import Album

from album.gui.create_shortcut import _create_shortcut_from_environment_and_executable
from album.gui.include.pyshortcuts import UserFolders


class TestIntegrationCreateShortcut(unittest.TestCase):

    @unittest.skipIf(platform.system() != "Linux", "Only runs on Linux")
    @patch("album.gui.include.pyshortcuts.linux.get_folders")
    def test__create_shortcut_from_environment_and_executable_linux(self, get_folders):

        with tempfile.TemporaryDirectory() as temp_dir:

            env_path = sys.prefix
            # print("Python environment path:", env_path)
            album = Album.Builder().base_cache_path(Path(temp_dir).joinpath("album")).build()
            micromamba_executable = album.configuration().micromamba_executable()
            if micromamba_executable:
                package_manager = micromamba_executable
            else:
                package_manager = album.configuration().conda_executable()

            executable = package_manager
            # print("Executable", executable)

            temp_dir = Path(temp_dir)

            folders = UserFolders(temp_dir.joinpath("home"), temp_dir.joinpath("desktop"), temp_dir.joinpath("task_menu"))
            get_folders.return_value = folders

            _create_shortcut_from_environment_and_executable(env_path, executable)

            # self.print_directory_contents(temp_dir)
            desktop_file = folders.desktop.joinpath("Album.desktop")
            self.assertTrue(desktop_file.exists())
            # with open(desktop_file, 'r') as file:
            #     file_content = file.readlines()

            # Print the content of the file
            # print("File content:")
            # print("".join(file_content))

            config = configparser.ConfigParser(strict=False)
            config.read(desktop_file)

            # Extract the Exec command
            exec_command = config.get('Desktop Entry', 'Exec', fallback='')

            self.assertIsNotNone(exec_command)
            exec_command += " --help"
            # print(exec_command)
            # Run the command and capture the output
            result = subprocess.run(shlex.split(exec_command), capture_output=True, text=True, check=True, env={})
            stdout = result.stdout
            # print('Command Output:', stdout)
            self.assertIn("usage: album gui", stdout)

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

            env_path = sys.prefix
            print("Python environment path:", env_path)
            album = Album.Builder().base_cache_path(Path(temp_dir).joinpath("album")).build()
            micromamba_executable = album.configuration().micromamba_executable()
            if micromamba_executable:
                package_manager = micromamba_executable
            else:
                package_manager = album.configuration().conda_executable()

            executable = package_manager
            print("Executable", executable)

            temp_dir = Path(temp_dir)

            folders = UserFolders(temp_dir.joinpath("home"), temp_dir.joinpath("desktop"), temp_dir.joinpath("task_menu"))
            get_folders.return_value = folders

            _create_shortcut_from_environment_and_executable(env_path, executable)

            self.print_directory_contents(temp_dir)
            desktop_file = folders.desktop.joinpath("Album.desktop")
            self.assertTrue(desktop_file.exists())
            # with open(desktop_file, 'r') as file:
            #     file_content = file.readlines()

            # Print the content of the file
            # print("File content:")
            # print("".join(file_content))

            config = configparser.ConfigParser(strict=False)
            config.read(desktop_file)

            # Extract the Exec command
            exec_command = config.get('Desktop Entry', 'Exec', fallback='')

            self.assertIsNotNone(exec_command)
            exec_command += " --help"
            # print(exec_command)
            # Run the command and capture the output
            result = subprocess.run(shlex.split(exec_command), capture_output=True, text=True, check=True, env={})
            stdout = result.stdout
            # print('Command Output:', stdout)
            self.assertIn("usage: album gui", stdout)

    @unittest.skipIf(platform.system() != "Darwin", "Only runs on macOS")
    @patch("album.gui.include.pyshortcuts.darwin.get_folders")
    def test__create_shortcut_from_environment_and_executable_macos(self, get_folders):

        with tempfile.TemporaryDirectory() as temp_dir:

            env_path = sys.prefix
            # print("Python environment path:", env_path)
            album = Album.Builder().base_cache_path(Path(temp_dir).joinpath("album")).build()
            micromamba_executable = album.configuration().micromamba_executable()
            if micromamba_executable:
                package_manager = micromamba_executable
            else:
                package_manager = album.configuration().conda_executable()

            executable = package_manager
            # print("Executable", executable)

            temp_dir = Path(temp_dir)

            folders = UserFolders(temp_dir.joinpath("home"), temp_dir.joinpath("desktop"), temp_dir.joinpath("task_menu"))
            get_folders.return_value = folders

            _create_shortcut_from_environment_and_executable(env_path, executable)

            self.print_directory_contents(temp_dir)
            desktop_file = folders.desktop.joinpath("Album.desktop")
            self.assertTrue(desktop_file.exists())
            # with open(desktop_file, 'r') as file:
            #     file_content = file.readlines()

            # Print the content of the file
            # print("File content:")
            # print("".join(file_content))

            config = configparser.ConfigParser(strict=False)
            config.read(desktop_file)

            # Extract the Exec command
            exec_command = config.get('Desktop Entry', 'Exec', fallback='')

            self.assertIsNotNone(exec_command)
            exec_command += " --help"
            # print(exec_command)
            # Run the command and capture the output
            result = subprocess.run(shlex.split(exec_command), capture_output=True, text=True, check=True, env={})
            stdout = result.stdout
            # print('Command Output:', stdout)
            self.assertIn("usage: album gui", stdout)