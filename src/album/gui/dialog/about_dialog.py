import pathlib
from importlib import metadata
from importlib.metadata import PackageNotFoundError

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QDialog, QPushButton, QHBoxLayout

import album


class AboutDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        try:
            self.album_api_version = metadata.version("album-runner")
        except PackageNotFoundError:
            self.album_api_version = metadata.version("album-solution-api")
        self.album_core_version = album.core.__version__
        self.album_gui_version = metadata.version("album-gui")

        layout = QVBoxLayout()

        self.setWindowTitle("About Album")

        versions = QLabel("Versions: album v%s, album-gui v%s, max. album_api_version %s" % (self.album_core_version, self.album_gui_version, self.album_api_version))

        disclaimer = QLabel("You are using Album at your own risk. Album will run any code included in a solution without being able to check if it will harm your system, please be aware that this code has access to your system and data.")
        disclaimer.setWordWrap(True)

        maintenance = QLabel("Album is invented, maintained and developed by Helmholtz Imaging.")
        maintenance.setWordWrap(True)

        icon_layout = QHBoxLayout()
        icon_layout.setAlignment(Qt.AlignLeft)
        icon_size = 50
        hi_label = QLabel()
        hi_pixmap = QPixmap(str(pathlib.Path(__file__).parent.parent / 'resources' / 'hi.png'))
        hi_label.setPixmap(hi_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_layout.addWidget(hi_label)

        album_pixmap = QPixmap(str(pathlib.Path(__file__).parent.parent / 'resources' / 'album-xs.png'))
        album_label = QLabel()
        album_label.setPixmap(album_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_layout.addWidget(album_label)
        
        ok_button = QPushButton("Close")
        ok_button.clicked.connect(self.accept)
        layout.addLayout(icon_layout)
        album_website = QLabel("<a href='https://album.solutions'>https://album.solutions</a><br/><a href='https://helmholtz-imaging.de'>https://helmholtz-imaging.de</a>")
        album_website.setOpenExternalLinks(True)

        layout.addWidget(album_website)
        layout.addWidget(versions)
        layout.addWidget(maintenance)
        layout.addWidget(disclaimer)
        layout.addWidget(ok_button)

        self.setLayout(layout)