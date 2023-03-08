from PyQt5.QtGui import QFontInfo, QFont
from PyQt5.QtWidgets import QPushButton, QMessageBox


def display_error(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setText("Error")
    msg.setInformativeText(text)
    msg.setWindowTitle("Error")
    msg.exec_()


def display_info(title, text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setInformativeText(text)
    msg.setWindowTitle(title)
    msg.exec_()


def display_confirmation(text):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Question)
    msg.setText("Confirmation requested")
    res = msg.question(None, "Confirmation Requested", text, msg.Yes | msg.No)
    return res == msg.Yes


def create_btn(parent, emit_slot, label, shortcut):
    btn = QPushButton(parent)
    # box = QHBoxLayout()
    # box.setContentsMargins(4, 4, 4, 4)
    # box.addWidget(QLabel(label))
    # box.addStretch()
    # shortcut_label = QLabel("%s" % shortcut)
    # shortcut_label.setFont(get_monospace_font())
    # shortcut_label.setStyleSheet("color: rgba(0, 0, 0, 100);")
    # box.addWidget(shortcut_label)
    # btn.setLayout(box)
    btn.setText(label)
    btn.clicked.connect(emit_slot)
    return btn


def is_fixed_pitch(font):
    fi = QFontInfo(font)
    return fi.fixedPitch()


def get_monospace_font():
    font = QFont("monospace")
    if is_fixed_pitch(font):
        return font
    font.setStyleHint(QFont.Monospace)
    if is_fixed_pitch(font):
        return font
    font.setStyleHint(QFont.TypeWriter)
    if is_fixed_pitch(font):
        return font
    font.setFamily("courier")
    if is_fixed_pitch(font):
        return font
    return font
