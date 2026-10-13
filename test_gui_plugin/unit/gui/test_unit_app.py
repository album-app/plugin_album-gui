import argparse
import unittest

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


if __name__ == "__main__":
    unittest.main()
