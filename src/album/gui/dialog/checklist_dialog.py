import sys

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QApplication, QCheckBox, QVBoxLayout, QHBoxLayout,
    QPushButton, QScrollArea, QWidget, QLabel
)


class CheckListDialog(QDialog):
    actionSubmitted = pyqtSignal(list)

    def __init__(self, options, title="", question="", action_name=""):
        super().__init__()
        self.setWindowTitle(title)
        self.options = options
        self.checkboxes = []
        self.availableUpdates = []
        self.custom_layout = self.initUI(question, action_name)

    def initUI(self, question, action_name):
        scrollArea = QScrollArea()
        scrollWidget = QWidget()
        vbox = QVBoxLayout(scrollWidget)
        for option in self.options:
            checkbox = QCheckBox(option)
            vbox.addWidget(checkbox)
            self.checkboxes.append(checkbox)
        scrollArea.setWidget(scrollWidget)
        scrollArea.setWidgetResizable(True)

        hbox = QHBoxLayout()
        selectAllButton = QPushButton("Select All")
        selectAllButton.clicked.connect(self.selectAll)
        deselectAllButton = QPushButton("Deselect All")
        deselectAllButton.clicked.connect(self.deselectAll)
        self.actionButton = QPushButton(action_name)
        self.actionButton.clicked.connect(self.applyAction)
        self.cancelButton = QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        hbox.addWidget(selectAllButton)
        hbox.addWidget(deselectAllButton)
        hbox.addWidget(self.actionButton)
        hbox.addWidget(self.cancelButton)
        custom_layout = QVBoxLayout()
        vbox2 = QVBoxLayout()
        vbox2.addWidget(QLabel(question))
        vbox2.addLayout(custom_layout)
        vbox2.addWidget(scrollArea)
        vbox2.addLayout(hbox)

        self.setLayout(vbox2)
        return custom_layout

    def selectAll(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselectAll(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def applyAction(self):
        self.actionSubmitted.emit(self.getCheckedItems())

    def getCheckedItems(self):
        checked_items = []
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                checked_items.append(checkbox.text())
        return checked_items


if __name__ == "__main__":
    app = QApplication(sys.argv)
    options = ["Option " + str(i) for i in range(1, 51)]
    dialog = CheckListDialog(
        options, title="Check List Dialog", question="Please select options:", action_name="Action"
    )
    if dialog.exec_() == QDialog.Accepted:
        checked_items = dialog.getCheckedItems()
        print("Activated choices: ", checked_items)
    sys.exit(app.exec_())