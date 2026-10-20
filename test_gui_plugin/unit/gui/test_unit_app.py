import argparse
import unittest
from unittest.mock import MagicMock

from album.gui.app import AlbumGUI


class TestUnitApp(unittest.TestCase):

    def test_construct_args(self):
        values = {"offset": "-10", "tiny": str(-0.00001), "flag": "-v", "empty": "", "expr": "a=b", "name": "x y"}
        argv = AlbumGUI._construct_args("group:name:0.1.0", values)
        self.assertEqual([
            "group:name:0.1.0", "--offset=-10", "--tiny=-1e-05", "--flag=-v", "--empty=", "--expr=a=b", "--name=x y"
        ], argv)

        # parsed like album-solution-api does it in the solution environment
        parser = argparse.ArgumentParser()
        for name in values:
            parser.add_argument("--%s" % name)
        self.assertEqual(values, vars(parser.parse_args(argv[1:])))

    def test_get_run_arguments(self):
        # the installed solution declares the default None, its database entry has no default
        declared = [{"name": "count", "type": "integer", "default": None}]
        album_instance = MagicMock()
        album_instance.resolve_installed.return_value.loaded_solution.return_value.setup.return_value = {
            "args": declared
        }
        solution_data = MagicMock()
        solution_data.setup.return_value = {"args": [{"name": "count", "type": "integer"}]}

        args = AlbumGUI._get_run_arguments(album_instance, "group:name:0.1.0", solution_data)

        self.assertEqual(declared, args)
        album_instance.resolve_installed.assert_called_once_with("group:name:0.1.0")

    def test_get_run_arguments_from_the_database_entry(self):
        # e.g. the solution file of the installation cannot be read
        album_instance = MagicMock()
        album_instance.resolve_installed.side_effect = ValueError("cannot load")
        stored = [{"name": "count", "type": "integer"}]
        solution_data = MagicMock()
        solution_data.setup.return_value = {"args": stored}

        self.assertEqual(stored, AlbumGUI._get_run_arguments(album_instance, "group:name:0.1.0", solution_data))

    def test_get_run_arguments_none(self):
        album_instance = MagicMock()
        album_instance.resolve_installed.return_value.loaded_solution.return_value.setup.return_value = {}

        self.assertIsNone(AlbumGUI._get_run_arguments(album_instance, "group:name:0.1.0", MagicMock()))


if __name__ == "__main__":
    unittest.main()
