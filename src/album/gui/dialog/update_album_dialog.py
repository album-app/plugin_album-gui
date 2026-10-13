import logging
import platform
import shlex
import shutil
import subprocess
import sys
import tempfile
from http.client import InvalidURL
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from PyQt5.QtCore import QCoreApplication, pyqtSignal, QThread
from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout, \
    QLineEdit
from album.core.utils.operations.file_operations import force_remove
from album.runner.album_logging import get_active_logger


def get_installer_download(branch, system=None, machine=None):
    """Return the URL of the Album Installer Wizard built by the album-package CI and the file name to save it as.

    The artifact paths and job names have to match the installer build jobs in the .gitlab-ci.yml of album-package.
    """
    system = platform.system() if system is None else system
    machine = platform.machine() if machine is None else machine
    url = f"https://gitlab.com/album-app/plugins/album-package/-/jobs/artifacts/{branch}/raw/installer/"
    if system == "Windows":
        return url + "album_installer.exe?job=windows_installer_build", "album_installer.exe"
    elif system == "Linux":
        return url + "album_installer?job=linux_installer_build", "album_installer"
    elif system == "Darwin":  # macOS, there is one installer per architecture
        arch = "arm64" if machine.lower() in ("arm64", "aarch64") else "x86_64"
        return url + f"{arch}/album_installer.app?job=macos_installer_build_{arch}", "album_installer"
    raise NotImplementedError("Updating Album is not supported on %s." % system)


LINUX_TERMINALS = ["gnome-terminal", "konsole", "xfce4-terminal", "xterm"]


def get_installer_launch_commands(installer, system=None):
    """Return the commands (arguments for subprocess.Popen) that run the installer in a terminal window.

    On Linux there is one candidate per supported terminal emulator, the first one that exists is used.
    """
    system = platform.system() if system is None else system
    installer = str(installer)
    if system == "Windows":
        # A string, not a list: cmd removes the outer pair of quotes and the inner pair keeps a path with spaces or
        # characters like & ( ) together. subprocess would escape inner quotes as \" which cmd does not understand.
        return ['cmd.exe /k ""%s""' % installer]
    if system == "Darwin":
        # Terminal runs the text in a shell. Within the AppleScript string, \ and " have to be escaped.
        shell_command = shlex.quote(installer).replace("\\", "\\\\").replace('"', '\\"')
        return [["osascript", "-e", 'tell application "Terminal" to do script "%s"' % shell_command]]
    return [[terminal, "--", "bash", "-c", shlex.quote(installer)] for terminal in LINUX_TERMINALS]


class Downloader(QThread):

    setTotalProgress = pyqtSignal(int)
    setCurrentProgress = pyqtSignal(int)
    stop_signal = pyqtSignal()
    succeeded = pyqtSignal()
    failed = False
    failed_msg = ""

    def __init__(self, url, filename):
        super().__init__()
        self._url = url
        self._filename = filename
        self.running = True
        self.stop_signal.connect(self.stop)

    def stop(self):  # Method to set running to False
        self.running = False

    def run(self):
        self.failed = True
        try:
            self.download()
            self.failed = False
            self.succeeded.emit()
        except InvalidURL:
            self.failed_msg = "Invalid URL: %s" % self._url
        except HTTPError:
            self.failed_msg = "Cannot download %s" % self._url
        except Exception as e:
            self.failed_msg = str(e)

    def download(self):
        get_active_logger().info("Downloading %s.." % self._url)
        readBytes = 0
        chunkSize = 1024
        with urlopen(self._url) as r:
            # Tell the window the amount of bytes to be downloaded.
            self.setTotalProgress.emit(int(r.info()["Content-Length"]))
            with open(self._filename, "ab") as f:
                while True:
                    if not self.running:
                        break
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


class UpdateAlbumDialog(QDialog):
    startDownload = pyqtSignal(str, Path)

    def __init__(self, parent, album_base_dir):
        super().__init__(parent)
        logging.debug("UpdateDialog initialized")
        self.album_base_dir = album_base_dir
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.manager = QNetworkAccessManager()

        self.info_label = QLabel("This is an experimental feature. Use at your own risk. You can always rerun the install wizard from the website to update or fix an Album installation.\n\nIn order to update your Album installation, the following steps will be executed:\n\n- the Album Installer Wizard will be downloaded\n- this application (Album) will be closed\n- the Album Installer Wizard will be executed\n- Album will be relaunched\n\nThis should not remove or deinstall any existing Album catalog or solution on your system.\n\nDo you want to run this routine?")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        branch_choice = QHBoxLayout()
        self.branch_choice_label = QLabel("album-package branch (don\'t change this if you are unsure)")
        branch_choice.addWidget(self.branch_choice_label)
        self.package_branch = QLineEdit("main")
        branch_choice.addWidget(self.package_branch)
        layout.addLayout(branch_choice)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        self.progress_bar.hide()

        action_bar = QHBoxLayout()

        self.yes_button = QPushButton("Yes")
        self.yes_button.clicked.connect(self.prepare_download)
        action_bar.addWidget(self.yes_button)

        self.no_button = QPushButton("No")
        self.no_button.clicked.connect(self.reject)
        action_bar.addWidget(self.no_button)

        layout.addLayout(action_bar)

        self.startDownload.connect(self.download)

    def prepare_download(self):
        logging.debug("Download preparation")
        try:
            url, save_path = get_installer_download(self.package_branch.text())
        except NotImplementedError as e:
            self.info_label.setText(str(e))
            self.yes_button.setEnabled(False)
            return

        self.save_path = Path(self.album_base_dir).joinpath(save_path)
        self.save_path_tmp = Path(self.album_base_dir).joinpath("tmp_" + str(save_path))
        self.startDownload.emit(url, self.save_path_tmp)

    def download(self, url, save_path):
        self.info_label.setText("Downloading the Album Installer Wizard...")
        self.progress_bar.show()
        self.branch_choice_label.setVisible(False)
        self.package_branch.setVisible(False)
        self.yes_button.setEnabled(False)
        self.no_button.setEnabled(True)
        self.no_button.setText("Cancel")
        self.no_button.disconnect()
        self.no_button.clicked.connect(self.cancel_download)

        self.downloader = Downloader(url, save_path)
        # Connect the signals which send information about the download
        # progress with the proper methods of the progress bar.
        self.downloader.setTotalProgress.connect(self.progress_bar.setMaximum)
        self.downloader.setCurrentProgress.connect(self.progress_bar.setValue)
        # Qt will invoke the `succeeded()` method when the file has been
        # downloaded successfully and `downloadFinished()` when the
        # child thread finishes.
        # self.downloader.succeeded.connect(self.downloadSucceeded)
        self.downloader.finished.connect(self.download_finished)
        self.downloader.start()

    def cancel_download(self):
        if hasattr(self, 'downloader'):
            self.downloader.stop_signal.emit()
            self.downloader.wait()
            self.close()

    def download_finished(self):
        self.progress_bar.hide()
        self.no_button.setEnabled(True)
        self.no_button.disconnect()
        self.no_button.clicked.connect(self.reject)
        if self.downloader.failed:
            self.info_label.setText(
                "Download failed. %s" % self.downloader.failed_msg)
            self.no_button.setText("Close")
            self.yes_button.setEnabled(False)
        else:
            self.no_button.setText("No")
            self.info_label.setText(
                "Download complete. Ready to update? This application will close, the installation wizard will run and Album will relaunch.")
            self.yes_button.setText("Update Now")
            self.yes_button.setEnabled(True)
            self.yes_button.clicked.connect(self.update)
        del self.downloader

    def update(self):
        QCoreApplication.quit()
        command = self.save_path
        shutil.copy(self.save_path_tmp, command)
        self.make_executable(command)
        force_remove(self.save_path_tmp)

        for launch_command in get_installer_launch_commands(command):
            try:
                subprocess.Popen(launch_command)
                break
            except FileNotFoundError:
                continue
        else:
            get_active_logger().error("Cannot open a terminal to run %s, please run it yourself." % command)
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
    dialog = UpdateAlbumDialog(None, temp_dir)
    dialog.exec_()
    # not deleting the tmp dir because the wizard is installed there and executed after the python process is killed...
