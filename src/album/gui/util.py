from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QLabel, QMessageBox


def display_error(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Error")
    msg.setInformativeText(text)
    msg.setWindowTitle("Error")
    msg.show()


def create_btn(parent, emit_slot, label, shortcut):
    btn = QPushButton(parent)
    box = QHBoxLayout()
    box.setContentsMargins(4, 4, 4, 4)
    box.addWidget(QLabel(label))
    box.addStretch()
    shortcut_label = QLabel("%s" % shortcut)
    shortcut_label.setStyleSheet("color: rgba(0, 0, 0, 100); font-family: monospace;")
    box.addWidget(shortcut_label)
    btn.setLayout(box)
    btn.clicked.connect(emit_slot)
    return btn
