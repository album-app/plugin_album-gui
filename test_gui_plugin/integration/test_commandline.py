import sys
import unittest.mock
from unittest.mock import patch

from album.argument_parsing import main


class TestCommandline(unittest.TestCase):
    @patch('album.gui.commandline._create_gui')
    def test_run(self, _create_gui):
        sys.argv = ["", "gui"]
        self.assertIsNone(main())

if __name__ == "__main__":
    unittest.main()
