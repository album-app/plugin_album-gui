import inspect
import os
import unittest
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QCheckBox, QPushButton
from album.runner.album_logging import get_active_logger

from album.gui.widgets import argument_widget_plugins
from album.gui.widgets.argument_widget_plugins import AbstractWidget, BooleanWidget, DoubleWidget, FileWidget, \
    IntegerWidget, StringWidget, create_gui_boolean, create_gui_directory, create_gui_double, create_gui_file, \
    create_gui_float, create_gui_integer, create_gui_string


def _arg(arg_type, **kwargs):
    arg = {"name": "%s_arg" % arg_type, "description": "a %s argument" % arg_type, "type": arg_type}
    arg.update(kwargs)
    return arg


def _set_to_default_button(widget):
    buttons = [btn for btn in widget.findChildren(QPushButton) if btn.text() == "set to default"]
    return buttons[0] if buttons else None


def _unset_checkbox(widget):
    return widget.unset_btn


class TestUnitArgumentWidgetPlugins(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # the unit tests also run on headless CI runners, render widgets offscreen unless told otherwise
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.app = QApplication.instance() or QApplication([])

    def test_all_widgets_set_value_accepts_value(self):
        for widget_class in [AbstractWidget, StringWidget, BooleanWidget, DoubleWidget, IntegerWidget, FileWidget]:
            with self.subTest(widget_class=widget_class.__name__):
                self.assertEqual(["self", "value"], list(inspect.signature(widget_class.set_value).parameters))

    def test_file_widget_with_default(self):
        # used to raise TypeError: set_value() takes 1 positional argument but 2 were given
        widget = create_gui_file(_arg("file", default="/path/to/input.txt"))
        self.assertEqual("/path/to/input.txt", widget.get_wrapped_value())

        widget.text.setText("/another/file.txt")
        self.assertEqual("/another/file.txt", widget.get_wrapped_value())
        _set_to_default_button(widget).click()
        self.assertEqual("/path/to/input.txt", widget.get_wrapped_value())

    def test_directory_widget_with_default(self):
        widget = create_gui_directory(_arg("directory", default="/path/to/dir"))
        self.assertIsInstance(widget, FileWidget)
        self.assertEqual("/path/to/dir", widget.get_wrapped_value())

        widget.text.setText("")
        _set_to_default_button(widget).click()
        self.assertEqual("/path/to/dir", widget.get_wrapped_value())

    def test_file_widget_set_value_path(self):
        widget = create_gui_file(_arg("file"))
        widget.set_value(Path("some", "file.txt"))
        self.assertEqual(str(Path("some", "file.txt")), widget.get_value())

    def test_file_widget_optional_without_default(self):
        widget = create_gui_file(_arg("file", required=False))
        self.assertIsNone(_set_to_default_button(widget))
        self.assertTrue(_unset_checkbox(widget).isChecked())
        self.assertIsNone(widget.get_wrapped_value())

    def test_file_widget_required(self):
        widget = create_gui_file(_arg("file"))
        self.assertIsNone(_set_to_default_button(widget))
        self.assertIsNone(widget.unset_btn)
        widget.set_value("/required/file.txt")
        self.assertEqual("/required/file.txt", widget.get_wrapped_value())

    def test_integer_widget_negative_values(self):
        widget = create_gui_integer(_arg("integer", default=-5))
        self.assertEqual(-5, widget.get_wrapped_value())
        self.assertLess(widget.spin_box.minimum(), -1000000)
        self.assertEqual(-widget.spin_box.minimum() - 1, widget.spin_box.maximum())

        widget.set_value(-123456789)
        self.assertEqual(-123456789, widget.get_value())
        widget.set_value(123456789)
        self.assertEqual(123456789, widget.get_value())
        widget.set_value("-42")
        self.assertEqual(-42, widget.get_value())

    def test_integer_widget_range_limits(self):
        widget = create_gui_integer(_arg("integer"))
        widget.set_value(argument_widget_plugins.INTEGER_MIN)
        self.assertEqual(argument_widget_plugins.INTEGER_MIN, widget.get_value())
        widget.set_value(argument_widget_plugins.INTEGER_MAX)
        self.assertEqual(argument_widget_plugins.INTEGER_MAX, widget.get_value())

    def test_double_widget_negative_values(self):
        for create in [create_gui_double, create_gui_float]:
            with self.subTest(create=create.__name__):
                widget = create(_arg("float", default=-2.5))
                self.assertEqual(-2.5, widget.get_wrapped_value())
                self.assertEqual(6, widget.spin_box.decimals())
                self.assertEqual(-widget.spin_box.minimum(), widget.spin_box.maximum())
                self.assertGreaterEqual(widget.spin_box.maximum(), 1e9)

                widget.set_value(-123456.123456)
                self.assertAlmostEqual(-123456.123456, widget.get_value(), places=6)
                widget.set_value(987654321.5)
                self.assertAlmostEqual(987654321.5, widget.get_value(), places=6)
                widget.set_value("-0.000001")
                self.assertAlmostEqual(-0.000001, widget.get_value(), places=6)

    def test_falsy_defaults_are_applied(self):
        cases = [
            (create_gui_integer, _arg("integer", default=0), 0, 7),
            (create_gui_double, _arg("float", default=0.0), 0.0, 7.5),
            (create_gui_boolean, _arg("boolean", default=False), False, True),
            (create_gui_string, _arg("string", default=""), "", "changed"),
            (create_gui_file, _arg("file", default=""), "", "/changed.txt"),
        ]
        for create, arg, default, other_value in cases:
            with self.subTest(type=arg["type"]):
                widget = create(arg)
                # a default exists, so the argument is not "unset" but initialized with the default
                self.assertIsNone(widget.unset_btn)
                self.assertEqual(default, widget.get_wrapped_value())
                self.assertIs(type(default), type(widget.get_wrapped_value()))

                widget.set_value(other_value)
                self.assertEqual(other_value, widget.get_wrapped_value())
                _set_to_default_button(widget).click()
                self.assertEqual(default, widget.get_wrapped_value())

    def test_truthy_defaults_are_applied(self):
        cases = [
            (create_gui_integer, _arg("integer", default=3), 3),
            (create_gui_double, _arg("float", default=1.25), 1.25),
            (create_gui_boolean, _arg("boolean", default=True), True),
            (create_gui_string, _arg("string", default="abc"), "abc"),
        ]
        for create, arg, default in cases:
            with self.subTest(type=arg["type"]):
                widget = create(arg)
                self.assertIsNone(widget.unset_btn)
                self.assertIsNotNone(_set_to_default_button(widget))
                self.assertEqual(default, widget.get_wrapped_value())

    def test_explicit_none_default_is_unset(self):
        widget = create_gui_integer(_arg("integer", default=None))
        self.assertIsNone(_set_to_default_button(widget))
        self.assertIsInstance(_unset_checkbox(widget), QCheckBox)
        self.assertIsNone(widget.get_wrapped_value())

        _unset_checkbox(widget).setChecked(False)
        widget.set_value(-1)
        self.assertEqual(-1, widget.get_wrapped_value())

    def test_unusable_default_is_left_unset(self):
        # used to raise ValueError / OverflowError while the run form was built
        cases = [
            (create_gui_integer, _arg("integer", default="")),
            (create_gui_integer, _arg("integer", default="2.5")),
            (create_gui_integer, _arg("integer", default=2 ** 31)),
            (create_gui_integer, _arg("integer", default=argument_widget_plugins.INTEGER_MIN - 1)),
            (create_gui_float, _arg("float", default="")),
            (create_gui_double, _arg("double", default="abc")),
        ]
        for create, arg in cases:
            with self.subTest(type=arg["type"], default=arg["default"]):
                with self.assertLogs(get_active_logger(), level="WARNING"):
                    widget = create(arg)
                self.assertIsNone(_set_to_default_button(widget))
                self.assertTrue(_unset_checkbox(widget).isChecked())
                self.assertIsNone(widget.get_wrapped_value())
                self.assertFalse(widget.shows_default_value())

                _unset_checkbox(widget).setChecked(False)
                widget.set_value(-7)
                self.assertEqual(-7, widget.get_wrapped_value())

    def test_shows_default_value(self):
        cases = [
            (create_gui_integer, _arg("integer", default=0), 5),
            (create_gui_double, _arg("float", default="1.0e-07"), 0.5),
            (create_gui_boolean, _arg("boolean", default=False), True),
            (create_gui_string, _arg("string", default=""), "x"),
            (create_gui_file, _arg("file", default="/in.txt"), "/other.txt"),
        ]
        for create, arg, other_value in cases:
            with self.subTest(type=arg["type"]):
                widget = create(arg)
                self.assertTrue(widget.shows_default_value())
                widget.set_value(other_value)
                self.assertFalse(widget.shows_default_value())
                _set_to_default_button(widget).click()
                self.assertTrue(widget.shows_default_value())

        for arg in [_arg("integer"), _arg("integer", required=False), _arg("integer", default=None)]:
            with self.subTest(arg=arg):
                widget = create_gui_integer(arg)
                if widget.unset_btn:
                    widget.unset_btn.setChecked(False)
                widget.set_value(0)
                self.assertFalse(widget.shows_default_value())

    def test_string_widget_set_value_non_string(self):
        widget = create_gui_string(_arg("string", default=5))
        self.assertEqual("5", widget.get_wrapped_value())


if __name__ == "__main__":
    unittest.main()
