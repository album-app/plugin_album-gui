from PyQt5.QtWidgets import QLineEdit, QHBoxLayout, QLabel, QFileDialog, QPushButton, QWidget, QCheckBox, QVBoxLayout, \
    QDoubleSpinBox, QSpinBox

from album.runner.album_logging import get_active_logger

from album.gui.widgets.argument_widget import ArgumentWidget

# Qt spin boxes default to the range 0..99, which makes negative values impossible, so set explicit ranges.
# QSpinBox stores its value in a C int, this is the widest range it supports.
INTEGER_MIN = -2147483648
INTEGER_MAX = 2147483647
DOUBLE_MIN = -1e12
DOUBLE_MAX = 1e12
DOUBLE_DECIMALS = 6


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
        # the value the widget shows for the default of the argument, None if the argument has no (usable) default
        self.default_widget_value = None
        default_value = None
        if "default" in arg:
            default_value = arg["default"]
        arg_name = arg["name"]
        self._name = arg_name
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

    def shows_default_value(self):
        """Whether the argument has a default value and the widget (still) shows it."""
        return self.default_widget_value is not None and self.get_wrapped_value() == self.default_widget_value

    def get_value(self):
        raise NotImplementedError

    def set_value(self, value):
        raise NotImplementedError

    def create_value_widget(self):
        raise NotImplementedError

    def create_wrapped_value_widget(self, default_value, optional):
        value_widget = self.create_value_widget()
        if optional:
            if default_value is not None and not self._apply_default_value(default_value):
                default_value = None
            return self._create_optional_widget(value_widget, default_value)
        return value_widget

    def _apply_default_value(self, default_value):
        try:
            self.set_value(default_value)
        except (ValueError, TypeError, OverflowError) as e:
            # e.g. the default "" of an integer argument or a default outside the range of the spin box. Treat the
            # argument as one without default instead of failing to build the run form.
            get_active_logger().warning(
                "Cannot show the default value %r of argument %s, leaving it unset: %s" % (default_value, self._name, e)
            )
            return False
        self.default_widget_value = self.get_value()
        return True

    def _create_optional_widget(self, widget, default_value, stretch_widget=True):
        res = QWidget()
        layout = QHBoxLayout(res)
        layout.setContentsMargins(0, 0, 0, 0)
        if default_value is not None:
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
        return self.text_field.setText(str(value))


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
        self.spin_box.setDecimals(DOUBLE_DECIMALS)
        self.spin_box.setRange(DOUBLE_MIN, DOUBLE_MAX)
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
        self.spin_box.setRange(INTEGER_MIN, INTEGER_MAX)
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

    def set_value(self, value):
        self.text.setText(str(value))

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
