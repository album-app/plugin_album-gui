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
        self.unset_btn = None
        default_value = None
        if "default" in arg:
            default_value = arg["default"]
        arg_name = arg["name"]
        optional = True
        if ("required" not in arg or arg["required"]) and "default" not in arg:
            arg_name += "*"
            optional = False
        self.valuebox = self.create_wrapped_value_widget(default_value, optional)
        nameLb = QLabel("<b>%s</b> %s" % (arg_name, arg["description"]))
        nameLb.setWordWrap(True)
        nameLb.setBuddy(self.valuebox)
        box.addWidget(nameLb)
        box.addWidget(self.valuebox)

    def get_wrapped_value(self):
        if self.unset_btn and self.unset_btn.isChecked():
            return None
        else:
            return self.get_value()

    def get_value(self):
        raise NotImplementedError

    def set_value(self, value):
        raise NotImplementedError

    def create_value_widget(self):
        raise NotImplementedError

    def create_wrapped_value_widget(self, default_value, optional):
        value_widget = self.create_value_widget()
        if optional:
            widget = self._create_optional_widget(value_widget, default_value)
            if default_value:
                self.set_value(default_value)
            return widget
        return value_widget

    def _create_optional_widget(self, widget, default_value, stretch_widget=True):
        res = QWidget()
        layout = QHBoxLayout(res)
        layout.setContentsMargins(0, 0, 0, 0)
        if default_value:
            set_to_default_btn = QPushButton("set to default")
            set_to_default_btn.clicked.connect(lambda: self.set_value(default_value))
            layout.addWidget(set_to_default_btn)
        else:
            self.unset_btn = QCheckBox()
            self.unset_btn.toggled.connect(lambda: widget.setEnabled(not self.unset_btn.isChecked()))
            self.unset_btn.setChecked(True)
            layout.addWidget(self.unset_btn)
            layout.addWidget(QLabel("unset"))
        if stretch_widget:
            layout.addWidget(widget, 1)
        else:
            layout.addStretch()
            layout.addWidget(widget)
        return res


class StringWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self):
        self.text_field = QLineEdit()
        return self.text_field

    def get_value(self):
        return self.text_field.text()

    def set_value(self, value):
        return self.text_field.setText(value)


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
        layout.addWidget(self.checkbox)
        widget.layout().setContentsMargins(0, 0, 0, 0)
        return widget

    def get_value(self):
        if self.unset_btn and self.unset_btn.isChecked():
            return None
        return self.checkbox.isChecked()

    def set_value(self, value):
        if value == '0' or value == 'False' or value == 'false':
            value = False
        self.checkbox.setChecked(bool(value))


class DoubleWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self):
        self.spin_box = QDoubleSpinBox()
        self.spin_box.setDecimals(6)
        self.spin_box.setMaximum(999999)
        return self.spin_box

    def get_value(self):
        return float(self.spin_box.value())

    def set_value(self, value):
        self.spin_box.setValue(float(value))


class IntegerWidget(AbstractWidget):
    def __init__(self, arg):
        super().__init__(arg)

    def create_value_widget(self):
        self.spin_box = QSpinBox()
        self.spin_box.setMaximum(1000000)
        return self.spin_box

    def set_value(self, value):
        self.spin_box.setValue(int(value))

    def get_value(self):
        return int(self.spin_box.value())


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

    def set_value(self):
        #TODO
        pass

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
