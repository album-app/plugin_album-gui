import os
import platform
import posixpath
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

from album import argument_parsing

from album.gui.create_shortcut import _create_shortcut_from_environment_and_executable, \
    _quote_desktop_exec_argument, create_shortcut, get_shortcut_name
from album.gui.include.pyshortcuts import UserFolders, darwin

# paths of a user whose home directory contains spaces
POSIX_BASE = "/home/John Doe/.album"
POSIX_MAMBA = "/home/John Doe/.album/micromamba/bin/micromamba"
POSIX_ENV = "/home/John Doe/.album/envs/album"
POSIX_ENVS = "/home/John Doe/.album/envs"


def _parse_desktop_exec(exec_value):
    """Split the Exec value of a .desktop file into arguments following the desktop entry specification."""
    # the general string escape rules of the file format are applied first (GLib rejects unknown escapes) ...
    escapes = {"s": " ", "n": "\n", "t": "\t", "r": "\r", "\\": "\\"}

    def unescape(match):
        if match.group(1) not in escapes:
            raise ValueError("invalid escape sequence \\%s in %s" % (match.group(1), exec_value))
        return escapes[match.group(1)]

    value = re.sub(r"\\(.)", unescape, exec_value)
    # ... then the quoting rules of the Exec key
    args, current, in_arg, quoted, i = [], "", False, False, 0
    while i < len(value):
        char = value[i]
        if quoted and char == "\\" and i + 1 < len(value) and value[i + 1] in '"`$\\':
            current += value[i + 1]
            i += 1
        elif char == '"':
            quoted = not quoted
            in_arg = True
        elif char == " " and not quoted:
            if in_arg:
                args.append(current)
            current, in_arg = "", False
        else:
            current += char
            in_arg = True
        i += 1
    if quoted:
        raise ValueError("unterminated quote in %s" % exec_value)
    if in_arg:
        args.append(current)
    # % starts a field code, %% is a literal %
    return [arg.replace("%%", "%") for arg in args]


def _parse_darwin_launcher(executable, script):
    """Split the command of the macOS launcher: export EXE=<exe>; export SCRIPT=<script>; eval "$EXE $SCRIPT $ARGS"."""
    exe_value = shlex.split(posixpath.normpath(executable))  # darwin.make_shortcut normalizes the executable
    script_value = shlex.split(script)
    assert len(exe_value) == 1 and len(script_value) == 1, "EXE and SCRIPT have to be a single shell word"
    return shlex.split("%s %s " % (exe_value[0], script_value[0]))


class TestUnitCreateShortcut(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_get_shortcut_name(self):
        self.assertEqual("Album", get_shortcut_name())
        self.assertEqual("Album", get_shortcut_name(None))
        self.assertEqual("Album", get_shortcut_name(""))
        self.assertEqual("Album - album_template-python_0.1.0", get_shortcut_name("album:template-python:0.1.0"))
        self.assertEqual("Album - group_name_0.1.0", get_shortcut_name("group:name:0.1.0"))
        self.assertEqual("Album - catalog_group_name_0.1.0", get_shortcut_name("catalog:group:name:0.1.0"))
        self.assertEqual("Album - denoise", get_shortcut_name("/home/John Doe/solutions/denoise/solution.py"))
        self.assertEqual("Album - denoise", get_shortcut_name("C:\\Users\\John Doe\\denoise\\solution.py"))
        self.assertEqual("Album - denoise", get_shortcut_name("/home/John Doe/solutions/denoise/"))
        self.assertEqual("Album - my_tool", get_shortcut_name("/home/John Doe/my_tool.py"))
        self.assertEqual("Album - solution.zip", get_shortcut_name("https://example.org/files/solution.zip"))
        # query and fragment of a URL are ignored
        self.assertEqual("Album - denoise", get_shortcut_name(
            "https://gitlab.com/group/project/-/raw/main/denoise/solution.py?inline=false"))
        self.assertEqual("Album - my_tool", get_shortcut_name("https://example.org/my_tool.py#L10"))
        self.assertEqual("Album - solution.zip", get_shortcut_name("https://example.org/solution.zip?ref=main&x=1"))
        self.assertEqual("Album - example.org", get_shortcut_name("https://example.org?x=1"))

    def test_create_parser(self):
        parser = argument_parsing.create_parser()

        args = parser.parse_known_args(["add-shortcut", "group:name:0.1.0"])[0]
        self.assertEqual(create_shortcut, args.func)
        self.assertEqual("group:name:0.1.0", args.solution)

        args = parser.parse_known_args(["add-shortcut"])[0]
        self.assertEqual(create_shortcut, args.func)
        self.assertIsNone(args.solution)

    def _album_instance(self, package_manager):
        album_instance = MagicMock()
        album_instance.configuration().base_cache_path.return_value = self.tmp_dir
        album_instance.configuration().environments_path.return_value = self.tmp_dir.joinpath("envs")
        album_instance._controller.environment_manager().get_environment_handler().get_package_manager() \
            .get_install_environment_executable.return_value = package_manager
        self.tmp_dir.joinpath("envs", "album").mkdir(parents=True)
        return album_instance

    @patch("album.gui.create_shortcut._create_shortcut_from_environment_and_executable")
    def test_create_shortcut_passes_solution(self, create_mock):
        album_instance = self._album_instance("/opt/micromamba/bin/micromamba")

        # album add-shortcut (as run by the album-package installer)
        create_shortcut(album_instance, Namespace(solution=None))
        # direct calls of the function
        create_shortcut(album_instance)
        create_shortcut(album_instance, command="album gui --help")
        # album add-shortcut <solution>
        create_shortcut(album_instance, Namespace(solution="group:name:0.1.0"))

        envs = self.tmp_dir.joinpath("envs")
        env = self.tmp_dir.joinpath("envs", "album")
        pm = "/opt/micromamba/bin/micromamba"
        self.assertEqual([
            ((self.tmp_dir, env, envs, pm, "album gui", None),),
            ((self.tmp_dir, env, envs, pm, "album gui", None),),
            ((self.tmp_dir, env, envs, pm, "album gui --help", None),),
            ((self.tmp_dir, env, envs, pm, "album gui", "group:name:0.1.0"),),
        ], [(call.args,) for call in create_mock.call_args_list])

    @patch("album.gui.create_shortcut._create_shortcut_from_environment_and_executable")
    def test_create_shortcut_makes_existing_solution_path_absolute(self, create_mock):
        album_instance = self._album_instance("/opt/micromamba/bin/micromamba")
        solution_file = self.tmp_dir.joinpath("my solution", "solution.py")
        solution_file.parent.mkdir()
        solution_file.touch()

        cwd = os.getcwd()
        os.chdir(self.tmp_dir)
        try:
            create_shortcut(album_instance, Namespace(solution=os.path.join("my solution", "solution.py")))
        finally:
            os.chdir(cwd)

        self.assertEqual(str(solution_file.resolve()), str(Path(create_mock.call_args.args[5]).resolve()))
        self.assertTrue(os.path.isabs(create_mock.call_args.args[5]))

    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Windows")
    def test_windows_generic_shortcut(self, _, make_shortcut):
        base = self.tmp_dir.joinpath("John Doe", ".album")
        base.mkdir(parents=True)
        package_manager = str(base.joinpath("micromamba", "Library", "bin", "micromamba.exe"))
        env = base.joinpath("envs", "album")

        _create_shortcut_from_environment_and_executable(
            base, env, base.joinpath("envs"), package_manager, "album gui"
        )

        bat_file = base.joinpath("Album.bat")
        self.assertEqual([
            'set "ALBUM_BASE_CACHE_PATH=%s"' % base,
            'set "MAMBA_ROOT_PREFIX=%s"' % base.joinpath("envs"),
            '"%s" run -p "%s" album gui' % (package_manager, env),
        ], bat_file.read_text().splitlines())
        make_shortcut.assert_called_once()
        self.assertEqual(('""%s""' % bat_file,), make_shortcut.call_args.args)
        self.assertEqual("Album", make_shortcut.call_args.kwargs["name"])
        self.assertEqual("C:\\Windows\\System32\\cmd.exe", make_shortcut.call_args.kwargs["executable"])

    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Windows")
    def test_windows_solution_shortcut(self, _, make_shortcut):
        base = self.tmp_dir.joinpath("John Doe 100%", ".album")
        base.mkdir(parents=True)
        package_manager = str(base.joinpath("micromamba", "Library", "bin", "micromamba.exe"))
        env = base.joinpath("envs", "album")

        _create_shortcut_from_environment_and_executable(
            base, env, base.joinpath("envs"), package_manager, "album gui", solution="group:name:0.1.0"
        )

        bat_file = base.joinpath("Album - group_name_0.1.0.bat")
        self.assertTrue(bat_file.exists())
        self.assertFalse(base.joinpath("Album.bat").exists())
        escaped_base = str(base).replace("%", "%%")
        self.assertEqual([
            'set "ALBUM_BASE_CACHE_PATH=%s"' % escaped_base,
            'set "MAMBA_ROOT_PREFIX=%s"' % str(base.joinpath("envs")).replace("%", "%%"),
            '"%s" run -p "%s" album gui "group:name:0.1.0"' % (
                package_manager.replace("%", "%%"), str(env).replace("%", "%%")),
        ], bat_file.read_text().splitlines())
        self.assertEqual(('""%s""' % bat_file,), make_shortcut.call_args.args)
        self.assertEqual("Album - group_name_0.1.0", make_shortcut.call_args.kwargs["name"])

    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Windows")
    def test_windows_without_micromamba(self, _, make_shortcut):
        _create_shortcut_from_environment_and_executable(
            self.tmp_dir, self.tmp_dir.joinpath("env"), self.tmp_dir.joinpath("envs"), "C:\\conda\\conda.exe",
            "album gui"
        )
        content = self.tmp_dir.joinpath("Album.bat").read_text().splitlines()
        self.assertEqual(['set "ALBUM_BASE_CACHE_PATH=%s"' % self.tmp_dir,
                          '"C:\\conda\\conda.exe" run -p "%s" album gui' % self.tmp_dir.joinpath("env")], content)

    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Linux")
    def test_linux_shortcut(self, _, make_shortcut):
        _create_shortcut_from_environment_and_executable(POSIX_BASE, POSIX_ENV, POSIX_ENVS, POSIX_MAMBA, "album gui")
        make_shortcut.assert_called_once()
        self.assertEqual("Album", make_shortcut.call_args.kwargs["name"])
        exec_value = "%s %s " % (posixpath.normpath(make_shortcut.call_args.kwargs["executable"]),
                                 make_shortcut.call_args.args[0])
        self.assertEqual([
            "env", "ALBUM_BASE_CACHE_PATH=%s" % POSIX_BASE, "MAMBA_ROOT_PREFIX=%s" % POSIX_ENVS, POSIX_MAMBA,
            "run", "-p", POSIX_ENV, "album", "gui"
        ], _parse_desktop_exec(exec_value))

        make_shortcut.reset_mock()
        _create_shortcut_from_environment_and_executable(
            POSIX_BASE, POSIX_ENV, POSIX_ENVS, POSIX_MAMBA, "album gui", solution="/home/John Doe/sol $1/solution.py"
        )
        self.assertEqual("Album - sol _1", make_shortcut.call_args.kwargs["name"])
        exec_value = "%s %s " % (posixpath.normpath(make_shortcut.call_args.kwargs["executable"]),
                                 make_shortcut.call_args.args[0])
        self.assertEqual([
            "env", "ALBUM_BASE_CACHE_PATH=%s" % POSIX_BASE, "MAMBA_ROOT_PREFIX=%s" % POSIX_ENVS, POSIX_MAMBA,
            "run", "-p", POSIX_ENV, "album", "gui", "/home/John Doe/sol $1/solution.py"
        ], _parse_desktop_exec(exec_value))

    def test_quote_desktop_exec_argument(self):
        for value in ["plain", "/home/John Doe/.album", 'a "quoted" `cmd` $HOME \\ 100%', "group:name:0.1.0"]:
            with self.subTest(value=value):
                quoted = _quote_desktop_exec_argument(value)
                self.assertTrue(quoted.startswith('"') and quoted.endswith('"'))
                self.assertEqual([value], _parse_desktop_exec(quoted))

    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Darwin")
    def test_macos_shortcut(self, _, make_shortcut):
        base = POSIX_BASE.replace("/home/", "/Users/")
        mamba = POSIX_MAMBA.replace("/home/", "/Users/")
        env = POSIX_ENV.replace("/home/", "/Users/")
        envs = POSIX_ENVS.replace("/home/", "/Users/")
        _create_shortcut_from_environment_and_executable(base, env, envs, mamba, "album gui")
        self.assertEqual("Album", make_shortcut.call_args.kwargs["name"])
        self.assertEqual([
            "env", "ALBUM_BASE_CACHE_PATH=%s" % base, "MAMBA_ROOT_PREFIX=%s" % envs, mamba,
            "run", "-p", env, "album", "gui"
        ], _parse_darwin_launcher(make_shortcut.call_args.kwargs["executable"], make_shortcut.call_args.args[0]))

        make_shortcut.reset_mock()
        _create_shortcut_from_environment_and_executable(
            base, env, envs, mamba, "album gui", solution="group:name:0.1.0"
        )
        self.assertEqual("Album - group_name_0.1.0", make_shortcut.call_args.kwargs["name"])
        self.assertEqual([
            "env", "ALBUM_BASE_CACHE_PATH=%s" % base, "MAMBA_ROOT_PREFIX=%s" % envs, mamba,
            "run", "-p", env, "album", "gui", "group:name:0.1.0"
        ], _parse_darwin_launcher(make_shortcut.call_args.kwargs["executable"], make_shortcut.call_args.args[0]))

    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Darwin")
    def test_macos_shortcut_without_spaces_unchanged(self, _, make_shortcut):
        # paths without special characters produce the same launcher as before
        _create_shortcut_from_environment_and_executable(
            "/Users/jd/.album", "/Users/jd/.album/envs/album", "/Users/jd/.album/envs",
            "/Users/jd/.album/micromamba/bin/micromamba", "album gui"
        )
        self.assertEqual(
            "'env ALBUM_BASE_CACHE_PATH=/Users/jd/.album MAMBA_ROOT_PREFIX=/Users/jd/.album/envs "
            "/Users/jd/.album/micromamba/bin/micromamba'",
            make_shortcut.call_args.kwargs["executable"])
        self.assertEqual("'run -p /Users/jd/.album/envs/album album gui'", make_shortcut.call_args.args[0])


class TestUnitCreateShortcutExecution(unittest.TestCase):
    """Runs the generated launchers with a fake package manager in a directory with spaces and special characters."""

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @unittest.skipIf(platform.system() != "Windows", "Only runs on Windows")
    @patch("album.gui.create_shortcut.make_shortcut")
    def test_windows_batch_file(self, make_shortcut):
        base = self.tmp_dir.joinpath("John Doe & Co (x) 100%", ".album")
        bin_dir = base.joinpath("micromamba", "Library", "bin")
        bin_dir.mkdir(parents=True)
        package_manager = bin_dir.joinpath("micromamba.cmd")
        package_manager.write_text(
            "@echo off\n"
            "set ALBUM_BASE_CACHE_PATH\n"
            "set MAMBA_ROOT_PREFIX\n"
            ":loop\n"
            "if \"%~1\"==\"\" goto end\n"
            "echo ARG=%1\n"
            "shift\n"
            "goto loop\n"
            ":end\n"
        )
        solution = self.tmp_dir.joinpath("my solution & more", "solution.py")
        env = base.joinpath("envs", "album")

        _create_shortcut_from_environment_and_executable(
            base, env, base.joinpath("envs"), str(package_manager), "album gui", solution=str(solution)
        )

        # this is what the shortcut runs
        command_line = "C:\\Windows\\System32\\cmd.exe /C " + make_shortcut.call_args.args[0]
        env_copy = os.environ.copy()
        for var in ["ALBUM_BASE_CACHE_PATH", "MAMBA_ROOT_PREFIX"]:
            env_copy.pop(var, None)
        result = subprocess.run(command_line, capture_output=True, text=True, env=env_copy)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        # the batch file echoes its commands, only compare the output of the fake package manager
        output = [line for line in result.stdout.splitlines()
                  if line.startswith(("ALBUM_BASE_CACHE_PATH=", "MAMBA_ROOT_PREFIX=", "ARG="))]
        self.assertEqual([
            "ALBUM_BASE_CACHE_PATH=%s" % base,
            "MAMBA_ROOT_PREFIX=%s" % base.joinpath("envs"),
            "ARG=run", "ARG=-p", 'ARG="%s"' % env, "ARG=album", "ARG=gui", 'ARG="%s"' % solution,
        ], output)

    def _write_posix_package_manager(self, base):
        bin_dir = base.joinpath("micromamba", "bin")
        bin_dir.mkdir(parents=True)
        package_manager = bin_dir.joinpath("micromamba")
        package_manager.write_text(
            "#!/bin/sh\n"
            "echo \"ALBUM_BASE_CACHE_PATH=$ALBUM_BASE_CACHE_PATH\"\n"
            "echo \"MAMBA_ROOT_PREFIX=$MAMBA_ROOT_PREFIX\"\n"
            "for arg in \"$@\"; do echo \"ARG=$arg\"; done\n"
        )
        package_manager.chmod(0o755)
        return package_manager

    def _expected_posix_output(self, base, env, solution):
        return [
            "ALBUM_BASE_CACHE_PATH=%s" % base,
            "MAMBA_ROOT_PREFIX=%s" % base.joinpath("envs"),
            "ARG=run", "ARG=-p", "ARG=%s" % env, "ARG=album", "ARG=gui", "ARG=%s" % solution,
        ]

    @unittest.skipIf(platform.system() == "Windows", "Only runs on Linux and macOS")
    @patch("album.gui.create_shortcut.make_shortcut")
    @patch("album.gui.create_shortcut.platform.system", return_value="Linux")
    def test_linux_desktop_exec(self, _, make_shortcut):
        base = self.tmp_dir.joinpath("John Doe's $HOME", ".album")
        package_manager = self._write_posix_package_manager(base)
        env = base.joinpath("envs", "album")
        solution = "/data/my solution/solution.py"

        _create_shortcut_from_environment_and_executable(
            base, env, base.joinpath("envs"), str(package_manager), "album gui", solution=solution
        )

        exec_value = "%s %s " % (os.path.normpath(make_shortcut.call_args.kwargs["executable"]),
                                 make_shortcut.call_args.args[0])
        env_copy = os.environ.copy()
        for var in ["ALBUM_BASE_CACHE_PATH", "MAMBA_ROOT_PREFIX"]:
            env_copy.pop(var, None)
        result = subprocess.run(_parse_desktop_exec(exec_value), capture_output=True, text=True, env=env_copy)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(self._expected_posix_output(base, env, solution), result.stdout.splitlines())

    @unittest.skipIf(platform.system() != "Linux" or shutil.which("gio") is None, "Needs Linux and gio (GLib)")
    @patch("album.gui.include.pyshortcuts.linux.get_folders")
    @patch("album.gui.create_shortcut.platform.system", return_value="Linux")
    def test_linux_desktop_file_launched_by_gio(self, _, get_folders):
        # cross-check of the Exec quoting with GLib, an independent implementation of the desktop entry specification,
        # using the .desktop file written by the vendored pyshortcuts
        base = self.tmp_dir.joinpath("John Doe's $HOME", ".album")
        package_manager = self._write_posix_package_manager(base)
        # gio launch neither waits for the process nor passes its output on, so the output goes to a file
        output = shlex.quote(str(self.tmp_dir.joinpath("output.txt")))
        package_manager.write_text(
            "#!/bin/sh\n{\n%s\n} > %s.tmp && mv %s.tmp %s\n"
            % (package_manager.read_text().replace("#!/bin/sh\n", "").strip(), output, output, output)
        )
        env = base.joinpath("envs", "album")
        solution = "/data/my solution/it's \"$x\" `y` 100% back\\slash/solution.py"
        folders = UserFolders(str(self.tmp_dir.joinpath("home")), str(self.tmp_dir.joinpath("desktop")),
                              str(self.tmp_dir.joinpath("menu")))
        get_folders.return_value = folders

        _create_shortcut_from_environment_and_executable(
            base, env, base.joinpath("envs"), str(package_manager), "album gui", solution=solution
        )

        desktop_files = list(Path(folders.desktop).glob("*.desktop"))
        self.assertEqual(1, len(desktop_files))
        env_copy = os.environ.copy()
        for var in ["ALBUM_BASE_CACHE_PATH", "MAMBA_ROOT_PREFIX"]:
            env_copy.pop(var, None)
        result = subprocess.run(["gio", "launch", str(desktop_files[0])], capture_output=True, text=True, env=env_copy,
                                timeout=60)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        output_file = self.tmp_dir.joinpath("output.txt")
        deadline = time.time() + 30
        while not output_file.exists() and time.time() < deadline:
            time.sleep(0.1)
        self.assertTrue(output_file.exists(), result.stdout + result.stderr)
        self.assertEqual(self._expected_posix_output(base, env, solution), output_file.read_text().splitlines())

    @unittest.skipIf(platform.system() == "Windows" or shutil.which("bash") is None, "Needs bash, not on Windows")
    @patch("album.gui.include.pyshortcuts.darwin.get_folders")
    @patch("album.gui.create_shortcut.platform.system", return_value="Darwin")
    def test_macos_app_launcher(self, _, get_folders):
        base = self.tmp_dir.joinpath("John Doe's $HOME", ".album")
        package_manager = self._write_posix_package_manager(base)
        env = base.joinpath("envs", "album")
        solution = "/data/my solution/solution.py"
        desktop = self.tmp_dir.joinpath("Desktop")
        get_folders.return_value = UserFolders(str(self.tmp_dir), str(desktop), "")

        with patch("album.gui.create_shortcut.make_shortcut", darwin.make_shortcut):
            _create_shortcut_from_environment_and_executable(
                base, env, base.joinpath("envs"), str(package_manager), "album gui", solution=solution
            )

        launchers = list(desktop.glob("*/Contents/MacOS/*"))
        self.assertEqual(1, len(launchers))
        self.assertEqual("Album - my solution", launchers[0].name)
        env_copy = os.environ.copy()
        for var in ["ALBUM_BASE_CACHE_PATH", "MAMBA_ROOT_PREFIX"]:
            env_copy.pop(var, None)
        result = subprocess.run(["bash", str(launchers[0])], capture_output=True, text=True, env=env_copy)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(self._expected_posix_output(base, env, solution), result.stdout.splitlines())


if __name__ == "__main__":
    unittest.main()
