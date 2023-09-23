from enum import Enum


class UpdateAction(Enum):
    NONE = 0,
    UNINSTALL = 1,
    INSTALL = 2


class UpdateActionItem:

    def __init__(self, update_action: UpdateAction = UpdateAction.NONE, catalog = None, solution=None, iteration=0):
        self.update_action = update_action
        self.catalog = catalog
        self.solution = solution
        self.iteration = iteration
