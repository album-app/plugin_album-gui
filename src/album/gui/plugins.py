from PyQt5.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QFileDialog, QPushButton, QWidget, QCheckBox, QVBoxLayout, \
    QDoubleSpinBox, QSpinBox

from album.gui.argument_widget import ArgumentWidget


def create_gui_string(argument):
    return StringWidget(argument)


def create_gui_file(argument):
    return FileWidget(argument)


def create_gui_directory(argument):
    return FileWidget(argument, QFileDialog.DirectoryOnly)


def create_gui_boolean(argument):
    return BooleanWidget(argument)


def create_gui_float(argument):
    return DoubleWidget(argument)


def create_gui_double(argument):
    return DoubleWidget(argument)


def create_gui_integer(argument):
    return IntegerWidget(argument)


class AbstractWidget(ArgumentWidget):
    def __init__(self, arg):
        super().__init__()
        box = QVBoxLayout()
        valuelabelbox = QHBoxLayout()
        self.setLayout(box)
        self.valuebox = self.create_value_widget()
        descrLb = QLabel("%s" % (arg["description"]))
        descrLb.setWordWrap(True)
        descrLb.setStyleSheet("color: rgba(0,0,0,0.6)")
        arg_name = arg["name"]
        if "required" in arg:
            if arg["required"]:
                arg_name += " *"
        nameLb = QLabel("%s" % (arg_name))
        nameLb.setBuddy(self.valuebox)
        valuelabelbox.addWidget(nameLb, 1)
        valuelabelbox.addWidget(self.valuebox, 5)
        box.addLayout(valuelabelbox)
        box.addWidget(descrLb)

    def create_value_widget(self):
        raise NotImplementedError()

    def get_value(self):
        raise NotImplementedError


class StringWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self):
        return QLineEdit()

    def get_value(self):
        return self.valuebox.text()


class BooleanWidget(AbstractWidget):
    def __init__(self, arg):
        self.checkbox = None
        super().__init__(arg)

    def create_value_widget(self):
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("QCheckBox::indicator{height: 20px; width: 20px;}")
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        layout.addStretch()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.checkbox)
        return widget

    def get_value(self):
        return self.checkbox.isChecked()


class DoubleWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self):
        return QDoubleSpinBox()

    def get_value(self):
        return self.valuebox.value()


class IntegerWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self):
        return QSpinBox()

    def get_value(self):
        return self.valuebox.value()


class FileWidget(AbstractWidget):
    def __init__(self, arg, file_mode=QFileDialog.AnyFile):
        super().__init__(arg)
        self.file_mode = file_mode

    def create_value_widget(self):
        layout = QHBoxLayout()
        self.btn = QPushButton("Browse")
        self.btn.clicked.connect(self._get_files)
        self.text = QLineEdit()
        layout.addWidget(self.text)
        layout.addWidget(self.btn)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget()
        widget.setLayout(layout)
        return widget

    def get_value(self):
        return self.text.text()

    def _get_files(self):
        dlg = QFileDialog()
        dlg.setFileMode(self.file_mode)

        if dlg.exec_():
            self.files = dlg.selectedFiles()
            if self.files:
                self.text.setText(self.files[0])
        self.btn.clearFocus()
