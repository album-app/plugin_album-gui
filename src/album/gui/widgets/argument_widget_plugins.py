from PyQt5.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QFileDialog, QPushButton, QWidget, QCheckBox, QVBoxLayout, \
    QDoubleSpinBox, QSpinBox

from album.gui.widgets.argument_widget import ArgumentWidget


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
        self.setLayout(box)
        default_value = None
        if "default" in arg:
            default_value = arg["default"]
        self.valuebox = self.create_value_widget(default_value)
        arg_name = arg["name"]
        if "required" not in arg or arg["required"]:
            arg_name += "*"
        nameLb = QLabel("<b>%s</b> %s" % (arg_name, arg["description"]))
        nameLb.setWordWrap(True)
        nameLb.setBuddy(self.valuebox)
        box.addWidget(nameLb)
        box.addWidget(self.valuebox)

    def create_value_widget(self, default_value):
        raise NotImplementedError()

    def get_value(self):
        raise NotImplementedError


class StringWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self, default_value):
        res = QLineEdit()
        if default_value:
            res.setText(default_value)
        return res

    def get_value(self):
        return self.valuebox.text()


class BooleanWidget(AbstractWidget):
    def __init__(self, arg):
        self.checkbox = None
        super().__init__(arg)

    def create_value_widget(self, default_value):
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("QCheckBox::indicator{height: 20px; width: 20px;}")
        if default_value:
            self.checkbox.setChecked(bool(default_value))
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

    def create_value_widget(self, default_value):
        res = QDoubleSpinBox()
        if default_value:
            res.setValue(float(default_value))
        return res

    def get_value(self):
        return self.valuebox.value()


class IntegerWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self, default_value):
        res = QSpinBox()
        if default_value:
            res.setValue(int(default_value))
        return res

    def get_value(self):
        return int(self.valuebox.value())


class FileWidget(AbstractWidget):
    def __init__(self, arg, file_mode=QFileDialog.AnyFile):
        super().__init__(arg)
        self.file_mode = file_mode

    def create_value_widget(self, default_value):
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
