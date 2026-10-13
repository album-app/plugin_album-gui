import time
import unittest

from test_gui_plugin.unit.gui import test_commandline
from test_gui_plugin.unit.gui import test_unit_create_shortcut
from test_gui_plugin.unit.gui import test_unit_solution_util
from test_gui_plugin.unit.gui.dialog import test_unit_update_album_dialog
from test_gui_plugin.unit.gui.dialog import test_unit_update_solutions_dialog
from test_gui_plugin.unit.gui.widgets import test_unit_argument_widget_plugins
from test_gui_plugin.unit.gui.widgets import test_unit_pre_run_solution_widget
from test_gui_plugin.unit.gui import test_unit_app


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_commandline))
    suite.addTests(loader.loadTestsFromModule(test_unit_create_shortcut))
    suite.addTests(loader.loadTestsFromModule(test_unit_solution_util))
    suite.addTests(loader.loadTestsFromModule(test_unit_update_album_dialog))
    suite.addTests(loader.loadTestsFromModule(test_unit_update_solutions_dialog))
    suite.addTests(loader.loadTestsFromModule(test_unit_argument_widget_plugins))
    suite.addTests(loader.loadTestsFromModule(test_unit_pre_run_solution_widget))
    suite.addTests(loader.loadTestsFromModule(test_unit_app))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
    if result.wasSuccessful():
        time.sleep(5)
        print("Success")
        exit(0)
    else:
        print("Failed")
        exit(1)


main()
