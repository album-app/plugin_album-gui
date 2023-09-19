import unittest
from datetime import datetime
from unittest.mock import create_autospec, patch

from album.api import Album

from album.gui.solution_util import get_uninstall_actions_for_version, group_solutions_by_version, \
    solution_coordinates, generate_remove_solutions_actions, full_coordinates


class TestUnitSolutionUtil(unittest.TestCase):

    def test_get_uninstall_actions_for_version(self):
        album_instance = create_autospec(Album)
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name0:0.2.0", installed=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)
        catalog = index["catalogs"][0]

        options_name2 = get_uninstall_actions_for_version(album_instance,
                                                          group_solutions_by_version(catalog)["catalog1:group1:name2"],
                                                          catalog, exclude_newest=True)

        self.assertEqual(0, len(options_name2))

        append_version(index, coordinates="catalog1:group1:name2:0.3.0", installed=True)
        options_name2 = get_uninstall_actions_for_version(album_instance,
                                                          group_solutions_by_version(catalog)["catalog1:group1:name2"],
                                                          catalog, exclude_newest=True)
        self.assertEqual(1, len(options_name2))
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(options_name2[0].solution))

        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True)
        catalog = index["catalogs"][0]

        options_name2 = get_uninstall_actions_for_version(album_instance,
                                                          group_solutions_by_version(catalog)["catalog1:group1:name2"],
                                                          catalog, exclude_newest=True)

        self.assertEqual(0, len(options_name2))

    @patch("album.gui.solution_util.child_installed", return_value=True)
    def test_generate_remove_solutions_actions(self, child_installed_mock):
        album_instance = create_autospec(Album)
        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name0:0.2.0", installed=False)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=False)
        album_instance.get_index_as_dict.return_value = index
        
        catalogs = ["catalog1"]

        remove_actions = generate_remove_solutions_actions(album_instance, catalogs)
        self.assertEqual(2, len(remove_actions))
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(remove_actions[0].solution))
        self.assertEqual("group1:name0:0.1.0", solution_coordinates(remove_actions[1].solution))

        index = {}
        append_version(index, coordinates="catalog1:group1:name0:0.1.0", installed=True, launched=False)
        append_version(index, coordinates="catalog1:group1:name0:0.2.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.1.0", parent="catalog1:group1:name0:0.1.0", installed=True)
        append_version(index, coordinates="catalog1:group1:name2:0.2.0", installed=True)
        album_instance.get_index_as_dict.return_value = index

        catalogs = ["catalog1"]

        remove_actions = generate_remove_solutions_actions(album_instance, catalogs)

        self.assertEqual(4, len(remove_actions))
        self.assertEqual("group1:name0:0.2.0", solution_coordinates(remove_actions[0].solution))
        self.assertEqual("group1:name2:0.2.0", solution_coordinates(remove_actions[1].solution))
        self.assertEqual("group1:name2:0.1.0", solution_coordinates(remove_actions[2].solution))
        self.assertEqual("group1:name0:0.1.0", solution_coordinates(remove_actions[3].solution))


def find_solution_by_coordinates(catalog_id, group, name, version, solutions):
    for solution in solutions:
        if (solution["internal"]["catalog_id"] == catalog_id and
                solution["setup"]["group"] == group and
                solution["setup"]["name"] == name and
                solution["setup"]["version"] == version):
            return solution
    return None


def append_version(index, coordinates, parent=None, installed=True, launched=True):
    catalog, group, name, version = coordinates.split(":")
    catalog_id = 1  # You can dynamically generate this if you need to
    collection_id = len(index.get("catalogs", [{}])[0].get("solutions", [])) + 1

    # Create a generic entry
    entry = {
        "internal": {
            "catalog_id": catalog_id,
            "children": [],
            "collection_id": collection_id,
            "install_date": None,
            "installation_unfinished": 0,
            "installed": 1 if installed else 0,
            "last_execution": datetime.now().isoformat() if installed and launched else None,
            "parent": parent,
            "solution_id": None  # or some value
        },
        "setup": {
            "group": group,
            "name": name,
            "version": version
        }
    }

    # Add entry to catalog
    if "catalogs" not in index:
        index["catalogs"] = [{"catalog_id": catalog_id, "name": catalog, "solutions": []}]

    catalog_entry = next((c for c in index["catalogs"] if c["catalog_id"] == catalog_id), None)
    if catalog_entry:
        # Append child info to parent entry if parent is specified
        if parent:
            parent_catalog, parent_group, parent_name, parent_version = parent.split(":")
            parent_entry = find_solution_by_coordinates(catalog_id, parent_group, parent_name, parent_version,
                                                        catalog_entry["solutions"])
            if parent_entry:
                parent_entry["internal"]["children"].append({"collection_id_child": collection_id,
                                                             "catalog_id_child": catalog_id})

        # Append entry
        catalog_entry["solutions"].append(entry)
