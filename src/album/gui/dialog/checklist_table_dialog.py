import sys

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QBrush, QPalette
from PyQt5.QtWidgets import (
    QDialog, QApplication, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QCheckBox, QWidget
)

from album.gui.dialog.update_action_item import UpdateActionItem, UpdateAction
from album.gui.solution_util import full_coordinates, solution_coordinates


class CheckListTableDialog(QDialog):
    actionSubmitted = pyqtSignal(list)

    def __init__(self, options, title="", question="", action_name="", enable_disable_options=False):
        super().__init__()
        self.setWindowTitle(title)
        self.options = options
        self.initUI(question, action_name, enable_disable_options)

    def initUI(self, question, action_name, enable_disable_options):
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(len(self.options))
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setHorizontalHeaderLabels(["Select", "Action", "Catalog", "Solution"])
        self.tableWidget.horizontalHeader().hide()
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 40)
        self.tableWidget.setColumnWidth(1, 100)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

        self.uninstallCheckbox = QCheckBox("Uninstall old version of solutions")
        self.uninstallCheckbox.setChecked(True)
        self.uninstallCheckbox.stateChanged.connect(self.updateRows)

        self.installCheckbox = QCheckBox("Update installed solutions to newest version")
        self.installCheckbox.setChecked(True)
        self.installCheckbox.stateChanged.connect(self.updateRows)

        for i, option in enumerate(self.options):
            checkBoxWidget = QWidget()
            layout = QHBoxLayout(checkBoxWidget)
            layout.setContentsMargins(3, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            layout.addWidget(checkbox)

            self.tableWidget.setCellWidget(i, 0, checkBoxWidget)
            action_item = QTableWidgetItem(option.update_action.name)
            self.tableWidget.setItem(i, 1, action_item)
            solution_item = QTableWidgetItem(solution_coordinates(option.solution))
            self.tableWidget.setItem(i, 3, solution_item)
            catalog_item = QTableWidgetItem(str(option.catalog["name"]))
            self.tableWidget.setItem(i, 2, catalog_item)

            self.colorRow(i, option)

        self.tableWidget.setAutoFillBackground(False)
        palette = self.tableWidget.palette()
        palette.setColor(QPalette.Base, Qt.transparent)
        self.tableWidget.setPalette(palette)
        self.tableWidget.setShowGrid(False)
        self.tableWidget.setAlternatingRowColors(True)
        # self.tableWidget.setStyleSheet("border: 0px;")

        hbox = QHBoxLayout()
        self.actionButton = QPushButton(action_name)
        self.actionButton.clicked.connect(self.applyAction)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        hbox.addWidget(self.actionButton)
        hbox.addWidget(self.cancelButton)

        custom_layout = QVBoxLayout()
        vbox2 = QVBoxLayout()
        q_label = QLabel(question)
        q_label.setWordWrap(True)
        vbox2.addWidget(q_label)
        if enable_disable_options:
            vbox2.addWidget(self.installCheckbox)
            vbox2.addWidget(self.uninstallCheckbox)
        vbox2.addLayout(custom_layout)
        vbox2.addWidget(self.tableWidget)
        vbox2.addLayout(hbox)

        self.setLayout(vbox2)
        self.updateRows()

    def colorRow(self, i, option):
        action_item = self.tableWidget.item(i, 1)

        if option.update_action == UpdateAction.INSTALL:
            action_item.setForeground(QBrush(QColor('green')))
        elif option.update_action == UpdateAction.UNINSTALL:
            action_item.setForeground(QBrush(QColor('red')))

    def updateRows(self):
        for i in range(self.tableWidget.rowCount()):
            action_item = self.tableWidget.item(i, 1)
            checkbox = self.tableWidget.cellWidget(i, 0)

            enabled = True
            if action_item.text() == "UNINSTALL":
                enabled = self.uninstallCheckbox.isChecked()
            elif action_item.text() == "INSTALL":
                enabled = self.installCheckbox.isChecked()

            checkbox.setEnabled(enabled)
            self.tableWidget.item(i, 1).setFlags(
                self.tableWidget.item(i, 1).flags() | Qt.ItemIsEnabled if enabled else self.tableWidget.item(i, 1).flags() & ~Qt.ItemIsEnabled)
            self.tableWidget.item(i, 2).setFlags(
                self.tableWidget.item(i, 2).flags() | Qt.ItemIsEnabled if enabled else self.tableWidget.item(i, 2).flags() & ~Qt.ItemIsEnabled)
            self.tableWidget.item(i, 3).setFlags(
                self.tableWidget.item(i, 3).flags() | Qt.ItemIsEnabled if enabled else self.tableWidget.item(i, 2).flags() & ~Qt.ItemIsEnabled)

            if enabled:
                self.colorRow(i, self.options[i])
            else:
                action_item.setForeground(QBrush(QColor('lightgrey')))

    def applyAction(self):
        checked_items = self.getCheckedItems()
        self.actionSubmitted.emit(checked_items)
        self.accept()

    def getCheckedItems(self):
        checked_items = []
        for i in range(self.tableWidget.rowCount()):
            checkbox_widget = self.tableWidget.cellWidget(i, 0)
            layout = checkbox_widget.layout()
            checkbox = layout.itemAt(0).widget()

            if checkbox.isChecked() and checkbox.isEnabled():
                checked_items.append(self.options[i])

        return checked_items


if __name__ == "__main__":
    app = QApplication(sys.argv)

    options = [
        UpdateActionItem(UpdateAction.NONE, "Solution 1"),
        UpdateActionItem(UpdateAction.UNINSTALL, "Solution 2"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
        UpdateActionItem(UpdateAction.INSTALL, "Solution 3"),
    ]

    dialog = CheckListTableDialog(
        options, title="Check List Dialog", question="Please select options:", action_name="Action"
    )

    dialog.tableWidget.horizontalHeader().setStretchLastSection(True)

    if dialog.exec_() == QDialog.Accepted:
        checked_items = dialog.getCheckedItems()
        for item in checked_items:
            print(f"Action: {item.update_action.name}, Solution: {item.solution}")

    sys.exit(app.exec_())
