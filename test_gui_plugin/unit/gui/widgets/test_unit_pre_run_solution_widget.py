import os
import unittest

from PyQt5.QtWidgets import QApplication, QPushButton
from album.runner.album_logging import get_active_logger

from album.gui.widgets.pre_run_solution_widget import PreRunSolutionWidget


class TestUnitPreRunSolutionWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # the unit tests also run on headless CI runners, render widgets offscreen unless told otherwise
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def test_add_arguments_with_defaults(self):
        # a solution with a file or directory argument with a default used to break the run form (TypeError)
        args = [
            {"name": "input", "type": "file", "description": "input file", "default": "/data/in.tif"},
            {"name": "output", "type": "directory", "description": "output dir", "default": "/data/out"},
            {"name": "offset", "type": "integer", "description": "offset", "default": -10},
            {"name": "iterations", "type": "integer", "description": "iterations", "default": 0},
            {"name": "shift", "type": "float", "description": "shift", "default": -0.5},
            {"name": "sigma", "type": "float", "description": "sigma", "default": 0.0},
            {"name": "verbose", "type": "boolean", "description": "verbose", "default": False},
            {"name": "prefix", "type": "string", "description": "prefix", "default": ""},
            {"name": "label", "description": "label without type", "required": False},
        ]
        widget = PreRunSolutionWidget(None)
        widget.add_arguments(args)

        self.assertEqual("/data/in.tif", widget._widgets["input"].get_wrapped_value())
        self.assertEqual("/data/out", widget._widgets["output"].get_wrapped_value())
        self.assertEqual(-10, widget._widgets["offset"].get_wrapped_value())
        self.assertEqual(-0.5, widget._widgets["shift"].get_wrapped_value())
        self.assertIs(False, widget._widgets["verbose"].get_wrapped_value())
        # unchanged defaults are not passed, the solution applies them itself
        self.assertEqual({}, widget.get_values())
        self.assertTrue(widget.check_required_fields())

        new_values = {
            "input": "/data/other.tif",
            "output": "/data/other",
            "offset": -11,
            "iterations": 3,
            "shift": -0.25,
            "sigma": 1.5,
            "verbose": True,
            "prefix": "p_",
        }
        for name, value in new_values.items():
            widget._widgets[name].set_value(value)
        self.assertEqual({name: str(value) for name, value in new_values.items()}, widget.get_values())
        self.assertTrue(widget.check_required_fields())

    def test_unchanged_defaults_are_not_passed(self):
        # passed as strings, these values would differ from the declared defaults: "False" and "0" are truthy,
        # album does not convert arguments without type (or of type "double") and the spin box rounds to 6 decimals
        args = [
            {"name": "flag", "description": "no type", "default": False},
            {"name": "count", "description": "no type", "default": 0},
            {"name": "factor", "type": "double", "description": "double", "default": 0.0},
            {"name": "tiny", "type": "float", "description": "rounded by the spin box", "default": 1e-07},
            # arguments read from the collection database: "type" is always set, defaults are strings
            {"name": "db_flag", "type": None, "description": "from the database", "default": "0", "required": False},
            {"name": "db_tiny", "type": "float", "description": "from the database", "default": "1.0e-07"},
        ]
        widget = PreRunSolutionWidget(None)
        widget.add_arguments(args)
        self.assertEqual({}, widget.get_values())

        widget._widgets["flag"].set_value("True")
        widget._widgets["factor"].set_value(-2.5)
        widget._widgets["tiny"].set_value(0.5)
        self.assertEqual({"flag": "True", "factor": "-2.5", "tiny": "0.5"}, widget.get_values())

        # back to the default, by hand or with the "set to default" button
        widget._widgets["flag"].set_value("False")
        buttons = [b for b in widget._widgets["factor"].findChildren(QPushButton) if b.text() == "set to default"]
        buttons[0].click()
        self.assertEqual({"tiny": "0.5"}, widget.get_values())

    def test_required_argument_with_default_is_passed(self):
        # argparse requires "required" arguments on the command line even if they have a default
        widget = PreRunSolutionWidget(None)
        widget.add_arguments([
            {"name": "threshold", "type": "integer", "description": "threshold", "required": True, "default": 0},
            {"name": "mode", "description": "mode", "required": True, "default": "fast"},
        ])
        self.assertEqual({"threshold": "0", "mode": "fast"}, widget.get_values())
        self.assertTrue(widget.check_required_fields())

    def test_unusable_numeric_default(self):
        # used to raise ValueError / OverflowError while the run form was built
        widget = PreRunSolutionWidget(None)
        with self.assertLogs(get_active_logger(), level="WARNING"):
            widget.add_arguments([
                {"name": "n", "type": "integer", "description": "n", "default": ""},
                {"name": "x", "type": "float", "description": "x", "default": ""},
                {"name": "big", "type": "integer", "description": "big", "default": "3000000000"},
            ])
        self.assertEqual({}, widget.get_values())
        self.assertTrue(widget.check_required_fields())

        widget._widgets["n"].unset_btn.setChecked(False)
        widget._widgets["n"].set_value(-4)
        self.assertEqual({"n": "-4"}, widget.get_values())

    def test_required_arguments(self):
        widget = PreRunSolutionWidget(None)
        widget.add_arguments([
            {"name": "input", "type": "file", "description": "input file"},
            {"name": "threshold", "type": "integer", "description": "threshold", "required": True},
        ])
        self.assertFalse(widget.check_required_fields())

        widget._widgets["input"].set_value("/data/in.tif")
        widget._widgets["threshold"].set_value(-3)
        self.assertEqual({"input": "/data/in.tif", "threshold": "-3"}, widget.get_values())
        self.assertTrue(widget.check_required_fields())


if __name__ == "__main__":
    unittest.main()
