import sys
import unittest.mock
from argparse import Namespace
from unittest.mock import create_autospec, patch

from album import argument_parsing
from album.api import Album

from album.gui import commandline
from album.gui.app import AlbumGUI


class TestCommandline(unittest.TestCase):
    @patch('album.gui.commandline._create_gui')
    def test_run(self, _create_gui):
        album_instance = create_autospec(Album)
        album_gui = create_autospec(AlbumGUI)
        _create_gui.return_value = album_gui

        commandline.launch_gui(album_instance, Namespace(solution=None))
        album_gui.launch.assert_called_once()

    @patch('album.gui.commandline._create_gui')
    def test_run_solution(self, _create_gui):
        album_instance = create_autospec(Album)
        album_gui = create_autospec(AlbumGUI)
        _create_gui.return_value = album_gui

        commandline.launch_gui(album_instance, Namespace(solution="test"))
        album_gui.launch.assert_called_once_with("test")
        album_gui.launch.assert_called_once()

    def test_create_parser(self):
        parser = argument_parsing.create_parser()

        sys.argv = ["", "gui", "xyz"]
        args = parser.parse_known_args()
        self.assertEqual(commandline.launch_gui, args[0].func)
        self.assertEqual("xyz", args[0].solution)

        sys.argv = ["", "gui"]
        args = parser.parse_known_args()
        self.assertEqual(commandline.launch_gui, args[0].func)
        self.assertEqual(None, args[0].solution)


if __name__ == "__main__":
    unittest.main()
