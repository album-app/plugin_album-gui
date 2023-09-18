from distutils.version import LooseVersion

from album.api import Album

from album.gui.dialog.update_action_item import UpdateActionItem, UpdateAction


def solution_version(solution):
    return solution["setup"]["version"]


def solution_coordinates(solution):
    coordinates = "%s:%s:%s" % (
        solution["setup"]["group"], solution["setup"]["name"], solution_version(solution))
    return coordinates


def installed(solution):
    return solution["internal"]["installed"]


def was_launched(solution):
    return bool(solution["internal"]["last_execution"])


def group_solutions_by_version(catalog):
    solutions = {}
    for solution in catalog["solutions"]:
        coordinates = "%s:%s:%s" % (
            catalog["name"], solution["setup"]["group"], solution["setup"]["name"])
        if coordinates in solutions:
            solutions[coordinates].append(solution)
        else:
            solutions[coordinates] = [solution]
    for solution_key in solutions:
        versioned_solutions = solutions[solution_key]
        solutions[solution_key] = sorted(versioned_solutions, key=lambda x: LooseVersion(x["setup"]['version']))
    return solutions


def full_coordinates(solution, catalog):
    coordinates = solution_coordinates(solution)
    return "%s:%s" % (catalog["name"], coordinates)


def is_parent(solution):
    return len(solution["internal"]["children"]) > 0


def child_installed(album: Album, solution):
    installed_children = [album._controller.collection_manager().get_collection_index().get_solution_by_collection_id(
        child["collection_id_child"]).internal()["installed"] for child in solution["internal"]["children"]]
    return any(installed_children)


def generate_update_actions(catalogs, actions, index=0):
    remaining_catalogs = []
    new_actions = []
    for catalog in catalogs:
        remaining_solutions = {}
        for solution_key in catalog["solutions"]:
            versions = catalog["solutions"][solution_key]
            solution_actions = []
            installed_versions_not_unlaunched_parents = False
            installed_old = []
            installed_version_is_recent = False
            recent_version = versions[len(versions)-1]
            for idx, version in enumerate(reversed(versions)):
                if installed(version):
                    # check if a parent solution was ever launched and if not, if it is the parent of a solution to be uninstalled, if yes, mark for uninstallation too
                    if is_parent(version) and not was_launched(version):
                        can_be_uninstalled = True
                        for child in version["internal"]["children"]:
                            child_id = child["collection_id_child"]
                            child_solution = [action for action in actions if
                                              action.solution["internal"]["collection_id"] == child_id]
                            if len(child_solution) == 0 or child_solution[0].update_action is not UpdateAction.UNINSTALL:
                                # child solution is not marked to be uninstalled
                                if solution_key in remaining_solutions:
                                    remaining_solutions[solution_key].append(version)
                                else:
                                    remaining_solutions[solution_key] = [version]
                                can_be_uninstalled = False
                                break
                        if can_be_uninstalled:
                            solution_actions.append(
                                UpdateActionItem(UpdateAction.UNINSTALL, catalog, version, index))
                    else:
                        installed_versions_not_unlaunched_parents = True
                    if idx != 0 and not is_parent(version):
                        installed_old.append(version)
            if not installed(recent_version):
                solution_actions.append(UpdateActionItem(UpdateAction.INSTALL, catalog, versions[-1], index))
            if installed_versions_not_unlaunched_parents:
                for old_installation in installed_old:
                    solution_actions.append(UpdateActionItem(UpdateAction.UNINSTALL, catalog, old_installation, index))
            new_actions.extend(solution_actions)
        if len(remaining_solutions) > 0:
            catalog["solutions"] = remaining_solutions
            remaining_catalogs.append(catalog)
        actions.extend(new_actions)
        if len(remaining_catalogs) > 0 and len(new_actions) > 0:
            generate_update_actions(remaining_catalogs, actions, index + 1)


def get_newest_prefer_installed(versions):
    # check which is the newest installed version
    for version in reversed(versions):
        if installed(version):
            return version
    # no version installed, return the most recent one
    return versions[len(versions) - 1]


def get_uninstall_old_versions_actions(album_instance, versions, catalog, exclude_newest=False):
    newest_installed = get_newest_prefer_installed(versions)
    if not installed(newest_installed):
        # no versions installed
        return []
    versions_to_be_uninstalled = []
    found_action = True
    while found_action:
        found_action = False
        for idx, version in enumerate(reversed(versions)):
            if not installed(version):
                continue
            if exclude_newest and version == newest_installed:
                continue
            if not child_installed(album_instance, version) and version not in versions_to_be_uninstalled:
                found_action = True
                versions_to_be_uninstalled.append(version)
            else:
                for child in version["internal"]["children"]:
                    child_id = child["collection_id_child"]
                    child_will_be_uninstalled = any([to_be_uninstalled for to_be_uninstalled in versions_to_be_uninstalled if
                                                     to_be_uninstalled["internal"]["collection_id"] == child_id])
                    if child_will_be_uninstalled and version not in versions_to_be_uninstalled:
                        found_action = True
                        versions_to_be_uninstalled.append(version)
    return [UpdateActionItem(UpdateAction.UNINSTALL, catalog, version) for version in versions_to_be_uninstalled]
