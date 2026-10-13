import os
import platform
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication
from album.runner.album_logging import get_active_logger

from album.gui.dialog.update_album_dialog import LINUX_TERMINALS, UpdateAlbumDialog, get_installer_download, \
    get_installer_launch_commands

# see the installer build jobs in the .gitlab-ci.yml of album-package and the installation instructions in album-docs
ARTIFACTS = "https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/main/raw/installer/"
WINDOWS_URL = ARTIFACTS + "album_installer.exe?job=windows_installer_build"
LINUX_URL = ARTIFACTS + "album_installer?job=linux_installer_build"
MACOS_ARM64_URL = ARTIFACTS + "arm64/album_installer.app?job=macos_installer_build_arm64"
MACOS_X86_64_URL = ARTIFACTS + "x86_64/album_installer.app?job=macos_installer_build_x86_64"


class TestUnitUpdateAlbumDialog(unittest.TestCase):

    def test_get_installer_download(self):
        self.assertEqual((WINDOWS_URL, "album_installer.exe"), get_installer_download("main", "Windows", "AMD64"))
        self.assertEqual((LINUX_URL, "album_installer"), get_installer_download("main", "Linux", "x86_64"))
        self.assertEqual((MACOS_ARM64_URL, "album_installer"), get_installer_download("main", "Darwin", "arm64"))
        self.assertEqual((MACOS_X86_64_URL, "album_installer"), get_installer_download("main", "Darwin", "x86_64"))

    def test_get_installer_download_branch(self):
        # other branches than main build their installers in the <name>_installer_build_test jobs
        url, _ = get_installer_download("dev", "Darwin", "arm64")
        self.assertEqual(
            "https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/dev/raw/installer/"
            "arm64/album_installer.app?job=macos_installer_build_arm64_test", url)
        branch = "https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/my-feature/raw/installer/"
        self.assertEqual((branch + "album_installer.exe?job=windows_installer_build_test", "album_installer.exe"),
                         get_installer_download("my-feature", "Windows", "AMD64"))
        self.assertEqual((branch + "album_installer?job=linux_installer_build_test", "album_installer"),
                         get_installer_download("my-feature", "Linux", "x86_64"))
        self.assertEqual((branch + "x86_64/album_installer.app?job=macos_installer_build_x86_64_test", "album_installer"),
                         get_installer_download("my-feature", "Darwin", "x86_64"))

    @patch("album.gui.dialog.update_album_dialog.platform.machine", return_value="arm64")
    @patch("album.gui.dialog.update_album_dialog.platform.system", return_value="Darwin")
    def test_get_installer_download_current_platform(self, _, __):
        self.assertEqual((MACOS_ARM64_URL, "album_installer"), get_installer_download("main"))

    def test_get_installer_download_unsupported(self):
        with self.assertRaises(NotImplementedError):
            get_installer_download("main", "FreeBSD", "amd64")


def _parse_applescript_string(literal):
    """Return the text of the content of an AppleScript string literal, fail on an unescaped double quote."""
    text, i = "", 0
    while i < len(literal):
        if literal[i] == "\\":
            text += literal[i + 1]
            i += 2
            continue
        if literal[i] == '"':
            raise ValueError("unescaped double quote at %s in %s" % (i, literal))
        text += literal[i]
        i += 1
    return text


def _get_terminal_script(command):
    prefix = 'tell application "Terminal" to do script "'
    osascript, option, script = command
    assert [osascript, option] == ["osascript", "-e"], command
    assert script.startswith(prefix) and script.endswith('"'), script
    return _parse_applescript_string(script[len(prefix):-1])


class TestUnitInstallerLaunchCommands(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

    def _create_fake_installer(self, folder_name, file_name):
        folder = Path(self.tmp_dir).joinpath(folder_name)
        folder.mkdir()
        installer = folder.joinpath(file_name)
        marker = Path(self.tmp_dir).joinpath("installer_ran")
        return installer, marker

    def test_windows(self):
        installer = "C:\\Users\\John Doe & Co (x)\\.album\\album_installer.exe"
        self.assertEqual(['cmd.exe /k ""%s""' % installer], get_installer_launch_commands(installer, "Windows"))

    def test_macos(self):
        for installer in ["/Users/john/.album/album_installer",
                          "/Users/John Doe/it's \"q\" $HOME `x` \\ & (y)/.album/album_installer"]:
            with self.subTest(installer=installer):
                commands = get_installer_launch_commands(installer, "Darwin")
                self.assertEqual(1, len(commands))
                # Terminal runs the text in the shell of the user
                self.assertEqual([installer], shlex.split(_get_terminal_script(commands[0])))

    def test_linux(self):
        installer = "/home/John Doe/it's $HOME/.album/album_installer"
        commands = get_installer_launch_commands(installer, "Linux")
        self.assertEqual(LINUX_TERMINALS, [command[0] for command in commands])
        for command in commands:
            self.assertEqual(["--", "bash", "-c"], command[1:4])
            self.assertEqual([installer], shlex.split(command[4]))

    @patch("album.gui.dialog.update_album_dialog.platform.system", return_value="Darwin")
    def test_current_platform(self, _):
        self.assertEqual(get_installer_launch_commands("/a/b", "Darwin"), get_installer_launch_commands("/a/b"))

    @unittest.skipIf(platform.system() != "Windows", "Only runs on Windows")
    def test_windows_execution(self):
        installer, marker = self._create_fake_installer("John Doe & Co (x) 100%", "album_installer.cmd")
        installer.write_text('@echo off\necho ran> "%s"\n' % marker)
        command = get_installer_launch_commands(installer, "Windows")[0]
        # /c instead of /k, so that cmd exits
        self.assertTrue(command.startswith("cmd.exe /k "))
        result = subprocess.run(command.replace("cmd.exe /k ", "cmd.exe /c ", 1), capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertTrue(marker.exists(), result.stdout + result.stderr)

    @unittest.skipIf(platform.system() == "Windows", "Only runs on Linux and macOS")
    def test_posix_execution(self):
        installer, marker = self._create_fake_installer("John Doe's \"$HOME\" `x` & (y)", "album_installer")
        installer.write_text('#!/bin/sh\necho ran > %s\n' % shlex.quote(str(marker)))
        installer.chmod(0o755)
        for system in ["Linux", "Darwin"]:
            with self.subTest(system=system):
                command = get_installer_launch_commands(installer, system)[0]
                # the shell command the terminal runs
                shell_command = command[4] if system == "Linux" else _get_terminal_script(command)
                result = subprocess.run(["bash", "-c", shell_command], capture_output=True, text=True)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
                self.assertTrue(marker.exists(), result.stdout + result.stderr)
                marker.unlink()


@patch("album.gui.dialog.update_album_dialog.sys.exit")
@patch("album.gui.dialog.update_album_dialog.QCoreApplication.quit")
@patch("album.gui.dialog.update_album_dialog.subprocess.Popen")
class TestUnitUpdateAlbumDialogUpdate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        self.dialog = UpdateAlbumDialog(None, self.tmp_dir)
        self.dialog.save_path = Path(self.tmp_dir).joinpath("album_installer")
        self.dialog.save_path_tmp = Path(self.tmp_dir).joinpath("tmp_album_installer")
        self.dialog.save_path_tmp.write_text("installer")

    def _assert_installer_moved(self):
        self.assertTrue(self.dialog.save_path.exists())
        self.assertFalse(self.dialog.save_path_tmp.exists())

    def test_update(self, popen, _, exit_):
        for system in ["Windows", "Darwin", "Linux"]:
            with self.subTest(system=system):
                popen.reset_mock()
                exit_.reset_mock()
                self.dialog.save_path_tmp.write_text("installer")
                with patch("album.gui.dialog.update_album_dialog.platform.system", return_value=system):
                    self.dialog.update()
                popen.assert_called_once_with(get_installer_launch_commands(self.dialog.save_path, system)[0])
                self._assert_installer_moved()
                exit_.assert_called_once_with(0)

    @patch("album.gui.dialog.update_album_dialog.platform.system", return_value="Linux")
    def test_update_linux_next_terminal(self, _, popen, __, exit_):
        popen.side_effect = [FileNotFoundError(), None]
        self.dialog.update()
        self.assertEqual(2, popen.call_count)
        popen.assert_called_with(get_installer_launch_commands(self.dialog.save_path, "Linux")[1])
        self._assert_installer_moved()
        exit_.assert_called_once_with(0)

    @patch("album.gui.dialog.update_album_dialog.platform.system", return_value="Linux")
    def test_update_linux_no_terminal(self, _, popen, __, exit_):
        popen.side_effect = FileNotFoundError()
        with self.assertLogs(get_active_logger(), level="ERROR") as logs:
            self.dialog.update()
        self.assertEqual(len(LINUX_TERMINALS), popen.call_count)
        self.assertIn(str(self.dialog.save_path), "\n".join(logs.output))
        exit_.assert_called_once_with(0)


class TestUnitUpdateAlbumDialogWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # the unit tests also run on headless CI runners, render widgets offscreen unless told otherwise
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)

    @patch.object(UpdateAlbumDialog, "download")
    @patch("album.gui.dialog.update_album_dialog.platform.machine", return_value="x86_64")
    @patch("album.gui.dialog.update_album_dialog.platform.system", return_value="Darwin")
    def test_prepare_download(self, _, __, download):
        dialog = UpdateAlbumDialog(None, self.tmp_dir)
        dialog.prepare_download()
        download.assert_called_once_with(MACOS_X86_64_URL, Path(self.tmp_dir).joinpath("tmp_album_installer"))
        self.assertEqual(Path(self.tmp_dir).joinpath("album_installer"), dialog.save_path)

    @patch.object(UpdateAlbumDialog, "download")
    @patch("album.gui.dialog.update_album_dialog.platform.system", return_value="FreeBSD")
    def test_prepare_download_unsupported(self, _, download):
        dialog = UpdateAlbumDialog(None, self.tmp_dir)
        dialog.prepare_download()
        download.assert_not_called()
        self.assertFalse(dialog.yes_button.isEnabled())
        self.assertIn("not supported", dialog.info_label.text())


if __name__ == "__main__":
    unittest.main()
