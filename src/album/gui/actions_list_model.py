from functools import total_ordering

from PyQt5.QtGui import QStandardItemModel, QStandardItem


class ActionsListModel(QStandardItemModel):

    @total_ordering
    class ActionItem(QStandardItem):
        recently_used = None
        text = None
        action = None
        solution_coordinates = None

        def _is_valid_operand(self, other):
            return hasattr(other, "text")

        def __eq__(self, other):
            if not self._is_valid_operand(other):
                return NotImplemented
            return self.text[2:].lower() == other.text[2:].lower()

        def __lt__(self, other):
            if not self._is_valid_operand(other):
                return NotImplemented
            return self.text[2:].lower() < other.text[2:].lower()


    def __init__(self, item_list=None, parent=None):
        self.item_list = item_list
        super().__init__(parent)

# TODO implement filter model https://www.walletfox.com/course/qsortfilterproxymodelexample.php to filter e.g. by catalog
