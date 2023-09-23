import time
import unittest

from test_gui_plugin.unit.gui import test_commandline
from test_gui_plugin.unit.gui import test_unit_solution_util
from test_gui_plugin.unit.gui.dialog import test_unit_update_solutions_dialog


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_commandline))
    suite.addTests(loader.loadTestsFromModule(test_unit_solution_util))
    suite.addTests(loader.loadTestsFromModule(test_unit_update_solutions_dialog))

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
