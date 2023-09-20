import os
import shutil
import sys
from urllib.request import urlopen

from PyQt5.QtCore import QUrl, QCoreApplication, pyqtSignal, QEventLoop, QThread
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar
import platform
import subprocess
import tempfile
from pathlib import Path
import logging

from album.core.utils.operations.file_operations import force_remove

logging.basicConfig(level=logging.DEBUG)


class Downloader(QThread):

    # Signal for the window to establish the maximum value
    # of the progress bar.
    setTotalProgress = pyqtSignal(int)
    # Signal to increase the progress.
    setCurrentProgress = pyqtSignal(int)
    # Signal to be emitted when the file has been downloaded successfully.
    succeeded = pyqtSignal()

    def __init__(self, url, filename):
        super().__init__()
        self._url = url
        self._filename = filename

    def run(self):
        readBytes = 0
        chunkSize = 1024
        # Open the URL address.
        with urlopen(self._url) as r:
            # Tell the window the amount of bytes to be downloaded.
            self.setTotalProgress.emit(int(r.info()["Content-Length"]))
            with open(self._filename, "ab") as f:
                while True:
                    # Read a piece of the file we are downloading.
                    chunk = r.read(chunkSize)
                    # If the result is `None`, that means data is not
                    # downloaded yet. Just keep waiting.
                    if chunk is None:
                        continue
                    # If the result is an empty `bytes` instance, then
                    # the file is complete.
                    elif chunk == b"":
                        break
                    # Write into the local file the downloaded chunk.
                    f.write(chunk)
                    readBytes += chunkSize
                    # Tell the window how many bytes we have received.
                    self.setCurrentProgress.emit(readBytes)
        # If this line is reached then no exception has ocurred in
        # the previous lines.
        self.succeeded.emit()


class UpdateAlbumDialog(QDialog):
    startDownload = pyqtSignal(str, Path)

    def __init__(self, parent, album_base_dir):
        super().__init__(parent)
        logging.debug("UpdateDialog initialized")
        self.album_base_dir = album_base_dir
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.manager = QNetworkAccessManager()

        self.info_label = QLabel("In order to update your Album installation, the following steps will be executed:\n\n- the Album Installer Wizard will be downloaded\n- this application (Album) will be closed\n- the Album Installer Wizard will be executed\n- Album will be relaunched\n\nThis should not remove or deinstall any existing Album catalog or solution on your system.\n\nDo you want to run this routine?")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        self.yes_button = QPushButton("Yes")
        self.yes_button.clicked.connect(self.prepare_download)
        layout.addWidget(self.yes_button)

        self.no_button = QPushButton("No")
        self.no_button.clicked.connect(self.reject)
        layout.addWidget(self.no_button)

        self.startDownload.connect(self.download)

    def prepare_download(self):
        logging.debug("Download preparation")
        os_type = platform.system()
        url = ""
        save_path = ""
        if os_type == "Windows":
            url = "https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/main/raw/installer/album_installer.exe?job=windows_installer_build"
            save_path = "album_installer.exe"
        elif os_type == "Linux":
            url = "https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/main/raw/installer/album_installer?job=linux_installer_build"
            save_path = "album_installer"
        elif os_type == "Darwin":  # macOS
            url = "https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/main/raw/installer/album_installer?job=macos_installer_build"
            save_path = "album_installer"

        self.save_path = Path(self.album_base_dir).joinpath(save_path)
        self.save_path_tmp = Path(self.album_base_dir).joinpath("tmp_" + str(save_path))
        self.startDownload.emit(url, self.save_path_tmp)

    def download(self, url, save_path):
        self.info_label.setText("Downloading the Album Installer Wizard...")
        self.progress_bar.show()
        self.yes_button.setEnabled(False)
        self.no_button.setEnabled(False)

        self.downloader = Downloader(url, save_path)
        # Connect the signals which send information about the download
        # progress with the proper methods of the progress bar.
        self.downloader.setTotalProgress.connect(self.progress_bar.setMaximum)
        self.downloader.setCurrentProgress.connect(self.progress_bar.setValue)
        # Qt will invoke the `succeeded()` method when the file has been
        # downloaded successfully and `downloadFinished()` when the
        # child thread finishes.
        # self.downloader.succeeded.connect(self.downloadSucceeded)
        self.downloader.finished.connect(self.downloadFinished)
        self.downloader.start()

    def downloadFinished(self):
        self.info_label.setText(
            "Download complete. Ready to update? This application will cloes, the installation wizard will run and Album will relaunch.")
        self.progress_bar.hide()
        self.yes_button.setText("Update Now")
        self.yes_button.setEnabled(True)
        self.yes_button.clicked.connect(self.update)
        self.no_button.setEnabled(True)
        del self.downloader

    def update(self):
        QCoreApplication.quit()
        command = self.save_path
        shutil.copy(self.save_path_tmp, command)
        self.make_executable(command)
        force_remove(self.save_path_tmp)

        os_type = platform.system()
        full_command = f"\"{command}; echo 'Press Enter to continue.'; read\""

        if os_type == "Windows":
            subprocess.Popen(["cmd.exe", "/k", full_command])
        elif os_type == "Darwin":  # macOS
            subprocess.Popen(["osascript", "-e", f'tell app "Terminal" to do script "{full_command}"'])
        else:  # Assuming Linux
            terminals = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]
            for terminal in terminals:
                try:
                    subprocess.Popen([terminal, "--", "bash", "-c", command])
                    break
                except FileNotFoundError:
                    continue
        sys.exit(0)

    def make_executable(self, path):
        import os
        mode = os.stat(path).st_mode
        mode |= (mode & 0o444) >> 2  # copy R bits to X
        os.chmod(path, mode)


if __name__ == "__main__":
    logging.debug("Application started")
    app = QApplication([])
    temp_dir = tempfile.mkdtemp()
    dialog = UpdateAlbumDialog(temp_dir)
    dialog.exec_()
    # not deleting the tmp dir because the wizard is installed there and executed after the python process is killed...
