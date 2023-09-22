import time
import unittest

from test_gui_plugin.integration import test_integration_solution_status_widget, test_integration_create_shortcut, test_commandline


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromModule(test_integration_solution_status_widget))
    suite.addTests(loader.loadTestsFromModule(test_integration_create_shortcut))
    suite.addTests(loader.loadTestsFromModule(test_commandline))

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
