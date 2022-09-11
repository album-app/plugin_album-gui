import typing
from functools import total_ordering

from PyQt5.QtCore import QAbstractListModel, QModelIndex, QVariant, Qt


class ActionsListModel(QAbstractListModel):

    @total_ordering
    class ActionItem:
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

    def set_list(self, item_list):
        self.item_list = item_list
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.item_list), 0))

    def item_from_index(self, index):
        return self.item_list[index]

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.item_list) if self.item_list else 0

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if not index.isValid():
            return QVariant()
        if index.row() >= len(self.item_list) or index.row() < 0:
            return QVariant()

        if role == Qt.DisplayRole:
            item = self.item_list[index.row()]
            return item.text
        elif role == Qt.TextAlignmentRole:
            if index.column() == 0:
                return QVariant(Qt.AlignLeft | Qt.AlignVCenter)
            else:
                return Qt.AlignCenter
        return QVariant()

# TODO implement filter model https://www.walletfox.com/course/qsortfilterproxymodelexample.php to filter e.g. by catalog
