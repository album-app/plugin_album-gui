import unittest

from album.gui.dialog.update_action_item import UpdateAction
from album.gui.dialog.update_solutions_dialog import UpdateSolutionDialog
from album.gui.solution_util import solution_coordinates
from unit.gui.test_unit_solution_util import append_version


class TestUnitUpdateSolutionsDialog(unittest.TestCase):
    def test__get_solution_options_single_update_same_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name1:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name1:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", parent="catalog1:group1:name1:0.1.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(2, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[1].solution))

    def test__get_solution_options_single_update_remove_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name1:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name1:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(3, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[1].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[2].update_action)
        self.assertEqual("group1:name1:0.1.0", solution_coordinates(options[2].solution))
        self.assertEqual(1, options[2].iteration)

    def test__get_solution_options_single_update_remove_double_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name1:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name1:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(4, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[1].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[2].update_action)
        self.assertEqual("group1:name1:0.1.0", solution_coordinates(options[2].solution))
        self.assertEqual(1, options[2].iteration)
        self.assertEqual(UpdateAction.UNINSTALL, options[3].update_action)
        self.assertEqual("group1:name0:0.1.0", solution_coordinates(options[3].solution))
        self.assertEqual(2, options[3].iteration)

    def test__get_solution_options_single_update_double_launched_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=True)
        append_version(index, coordinates="catalog1:group1:name1:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name1:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(3, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[1].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[2].update_action)
        self.assertEqual("group1:name1:0.1.0", solution_coordinates(options[2].solution))
        self.assertEqual(1, options[2].iteration)

    def test__get_solution_options_single_update_double_launched_updateable_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=True)
        append_version(index, coordinates="catalog1:group1:name0:0.2.0", installed=False)
        append_version(index, coordinates="catalog1:group1:name1:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name1:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(4, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name0:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.INSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[1].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[2].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[2].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[3].update_action)
        self.assertEqual("group1:name1:0.1.0", solution_coordinates(options[3].solution))
        self.assertEqual(1, options[3].iteration)

    def test__get_solution_options_single_update_changing_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name0:0.2.0", installed=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", parent="catalog1:group1:name0:0.2.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(3, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name0:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.INSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[1].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[2].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[2].solution))

    def test__get_solution_options_single_update_changing_unused_parent(self):
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name0:0.2.0", installed=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)

        options = UpdateSolutionDialog._get_solution_options(index)
        self.assertEqual(3, len(options))
        self.assertEqual(UpdateAction.INSTALL, options[0].update_action)
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(options[0].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[1].update_action)
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options[1].solution))
        self.assertEqual(UpdateAction.UNINSTALL, options[2].update_action)
        self.assertEqual("group1:name0:0.1.0", solution_coordinates(options[2].solution))
