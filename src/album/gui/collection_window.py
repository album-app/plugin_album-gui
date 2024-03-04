import pathlib
from importlib import metadata
from importlib.metadata import PackageNotFoundError

from PyQt5 import QtGui
from PyQt5.QtCore import Qt, pyqtSignal, QSortFilterProxyModel, QEvent
from PyQt5.QtGui import QKeyEvent, QPixmap, QPainter, QFont, QIcon, QColor, QTextCursor
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QHBoxLayout, QWidget, QMainWindow, QPushButton, QMenu, \
    QAction, QActionGroup, QSplitter, QComboBox, QStyle, QMessageBox, QTextEdit
from album.api import Album
from packaging.version import Version

import album
from album.gui.actions_list_model import ActionsListModel
from album.gui.solution_util import installed, group_solutions_by_version, solution_version, solution_coordinates, \
    full_coordinates, get_newest_prefer_installed
from album.gui.widgets.solution_view import SolutionView
from album.gui.widgets.util import create_btn


class CollectionWindow(QMainWindow):
    # events
    return_pressed = pyqtSignal(QKeyEvent)
    esc_pressed = pyqtSignal(QKeyEvent)
    show_solution = pyqtSignal(str)
    uninstall_solution = pyqtSignal(str)
    uninstall_solutions = pyqtSignal(list)
    install_solution = pyqtSignal(str)
    remove_catalog = pyqtSignal(dict)
    add_new_catalog = pyqtSignal(QWidget)
    open_about = pyqtSignal(QWidget)
    update_album = pyqtSignal(QWidget)
    update_catalog_dialog = pyqtSignal(list)
    update_solution_dialog = pyqtSignal()
    batch_uninstall_dialog = pyqtSignal(list)
    collection_changed = pyqtSignal()

    update_running = pyqtSignal(bool)
    upgrade_running = pyqtSignal(bool)
    available_updates_changed = pyqtSignal(bool)

    class Action:
        def __init__(self, signal, args=None, versions=None, catalog=None):
            self.signal = signal
            self.args = args
            self.versions = versions
            self.catalog = catalog

    def __init__(self, album_instance: Album, parent=None):
        super(CollectionWindow, self).__init__(parent)
        self.selected_solution = None
        self.selected_solution_version = None
        self.album_instance: Album = album_instance
        self.all_catalogs = []
        self.deletable_catalogs = []
        self.list_widget = None
        self.setWindowTitle("Album")
        try:
            self.album_api_version = metadata.version("album-runner")
        except PackageNotFoundError:
            self.album_api_version = metadata.version("album-solution-api")
        self.album_core_version = album.core.__version__
        self.album_gui_version = metadata.version("album-gui")
        self.installed_icon = self.create_icon_from_unicode(chr(0x2713), "#19c18f", size=12)
        self.notinstalled_icon = self.create_icon_from_unicode(chr(0x2717), "#ff6c87", size=12)

        self.search_model = ActionsListModel()
        # self.search_proxy_model = ActionFilterProxyModel()
        self.update_model()

        widget = QWidget(self)
        self.setMinimumWidth(800)
        self.setMinimumHeight(400)
        self.setWindowIcon(QtGui.QIcon(str(pathlib.Path(__file__).parent / 'resources' / 'album-xs.png')))
        self.layout = QVBoxLayout(widget)

        self.layout.setContentsMargins(0, 10, 0, 0)
        self.layout.setSpacing(0)

        self._create_list_widget()
        self._create_search_line()

        top_layout = QSplitter()
        top_layout.addWidget(self._create_center())
        top_layout.addWidget(self._create_right())
        self.layout.addWidget(self.search_line)
        self.layout.addWidget(top_layout, 1)
        self.layout.addLayout(self._create_status_layout())

        self.setCentralWidget(widget)

    def _create_center(self):
        res = QWidget()
        layout = QVBoxLayout(res)
        res.setAutoFillBackground(True)
        # res.setPalette(self.pal)
        res.setContentsMargins(2, 0, 2, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.list_widget)
        return res

    def _create_search_line(self):
        self.search_line = QLineEdit(self)
        self.search_line.setStyleSheet(
            "QLineEdit { border-radius: 0px; border-top: 1px solid #bbbbbb; border-bottom: 1px solid #bbbbbb;padding: 3px;}")
        self.search_line.installEventFilter(self)
        self.proxy.setFilterCaseSensitivity(False)
        self.search_line.textChanged.connect(self.proxy.setFilterFixedString)
        self.proxy.rowsInserted.connect(self.list_widget.select_first_item)
        self.proxy.rowsRemoved.connect(self.list_widget.select_first_item)
        self.proxy.rowsMoved.connect(self.list_widget.select_first_item)

    def _create_list_widget(self):
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.search_model)
        self.list_widget = SolutionView(self)
        self.list_widget.selectionModel().selectionChanged.connect(self._update_focus_solution)

    def _update_focus_solution(self):
        item = self._get_currently_selected_item()
        if item:
            versions = item.action.versions
            self.version_combo.clear()

            for idx, version in enumerate(versions):
                self.version_combo.addItem(solution_version(version))
                if installed(version):
                    self.version_combo.setItemIcon(idx, self.installed_icon)
                else:
                    self.version_combo.setItemIcon(idx, self.notinstalled_icon)
            # self.version_combo.addItems(solution_version(version) for version in versions)
            # self.version_combo.setEnabled(len(versions) > 1)
            self.selected_solution = get_newest_prefer_installed(versions)
            self.selected_solution_version = solution_version(self.selected_solution)
            self.version_combo.setCurrentText(self.selected_solution_version)
            self._update_focus_solution_version()

    @staticmethod
    def create_icon_from_unicode(unicode_char, color='black', font_name='Arial', size=16):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(QColor(color))
        painter.setFont(QFont(font_name, size))
        painter.drawText(0, 0, size, size, Qt.AlignCenter, unicode_char)
        painter.end()
        return QIcon(pixmap)

    def _update_focus_solution_version(self):
        if self.selected_solution:
            if self.version_combo.currentText():
                self.selected_solution_version = self.version_combo.currentText()

                item = self._get_currently_selected_item()
                versions = item.action.versions
                version_match = [version for version in versions if solution_version(version) == self.selected_solution_version]
                self.selected_solution = version_match[0]
                item.action.args = full_coordinates(self.selected_solution, item.action.catalog)

            self.selected_solution_group.setText(self.selected_solution["setup"]["group"])
            self.selected_solution_name.setText(self.selected_solution["setup"]["name"])

            self.solution_api_warning.setVisible(Version(self.album_api_version) < Version(self.selected_solution["setup"]["album_api_version"]))

            self.selected_solution_description.setPlainText("")
            if "title" in self.selected_solution["setup"] and self.selected_solution["setup"]["title"]:
                self.selected_solution_description.append("~ <b>%s</b>" % self.selected_solution["setup"]["title"])

            if "description" in self.selected_solution["setup"] and self.selected_solution["setup"]["description"]:
                self.selected_solution_description.append(self.selected_solution["setup"]["description"])

            if "cite" in self.selected_solution["setup"] and self.selected_solution["setup"]["cite"]:
                citations = ""
                for citation in self.selected_solution["setup"]["cite"]:
                    citations += citation["text"] + "\n"
                    if "url" in citation:
                        citations += citation["url"] + "\n"
                self.selected_solution_description.append("\nCredits: %s" % citations if citations else "")

            if "solution_creators" in self.selected_solution["setup"]:
                creators = ""
                for creator in self.selected_solution["setup"]["solution_creators"]:
                    creators += creator + "\n"
                self.selected_solution_description.append("\nSolution file written by %s" % creators if creators else "")

            cursor = self.selected_solution_description.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.selected_solution_description.setTextCursor(cursor)

            self.run_btn.setVisible(True)
        else:
            self.selected_solution_description.setPlainText("")
            self.selected_solution_group.setText("")
            self.selected_solution_name.setText("")
            self.run_btn.setVisible(False)

    def _create_status_layout(self):
        status_layout = QHBoxLayout()
        catalog_status = self._create_status_with_action(
            "catalogs: %s" % len(self.album_instance.get_catalogs_as_dict()["catalogs"]), self._get_catalog_actions())

        solutions_status = self._create_status(
            "solution versions total: %s" % self._get_solution_count(self.album_instance.get_index_as_dict()))
        installed_status = self._create_status_with_action(
            "installed solution versions: %s" % self._get_installed_solution_count(self.album_instance.get_index_as_dict()), self._get_update_solution_actions())
        # running_status = self._create_status("running: 0")
        # updates_status = self._create_status("updates: 0")
        self.collection_changed.connect(lambda: catalog_status.setText(
            "catalogs: %s" % len(self.album_instance.get_catalogs_as_dict()["catalogs"])))
        self.collection_changed.connect(lambda: self._set_actions(catalog_status, self._get_catalog_actions()))
        self.collection_changed.connect(lambda: solutions_status.setText(
            "solutions: %s" % self._get_solution_count(self.album_instance.get_index_as_dict())))
        self.collection_changed.connect(lambda: installed_status.setText(
            "installed: %s" % self._get_installed_solution_count(self.album_instance.get_index_as_dict())))
        # update_btn = self._create_status_with_action("update", self._get_update_actions())

        status_layout.addWidget(catalog_status)
        status_layout.addWidget(solutions_status)
        status_layout.addWidget(installed_status)
        status_layout.addStretch()

        album_label = QPushButton("Album v%s" % (self.album_core_version))
        album_pixmap = QIcon(str(pathlib.Path(__file__).parent / 'resources' / 'album-xs.png'))
        album_label.setIcon(album_pixmap)
        self._set_actions(album_label, self._get_installation_actions())

        status_layout.addWidget(album_label)
        status_layout.setContentsMargins(3, 3, 3, 3)
        status_layout.setSpacing(10)
        return status_layout

    def _get_catalog_actions(self):
        actions = QActionGroup(self)
        add_catalog = QAction("Add catalog")
        add_catalog.triggered.connect(lambda: self.add_new_catalog.emit(self))
        actions.addAction(add_catalog)
        update_catalog = QAction("Update catalog(s)")
        update_catalog.triggered.connect(lambda: self.update_catalog_dialog.emit([catalog["name"] for catalog in self.all_catalogs]))
        actions.addAction(update_catalog)
        for catalog in self.deletable_catalogs:
            add_catalog = QAction("Remove catalog %s" % catalog["name"])
            add_catalog.triggered.connect(self.make_remove_catalog_action(catalog))
            actions.addAction(add_catalog)
        return actions.actions()

    def _get_installation_actions(self):
        actions = QActionGroup(self)
        about = QAction("About")
        about.triggered.connect(lambda: self.open_about.emit(self))
        actions.addAction(about)
        update_album = QAction("Update or reinstall Album (experimental)")
        update_album.triggered.connect(lambda: self.update_album.emit(self))
        actions.addAction(update_album)
        return actions.actions()

    def _get_update_solution_actions(self):
        actions = QActionGroup(self)
        batch_uninstall = QAction("Uninstall all solutions from catalog(s)")
        batch_uninstall.triggered.connect(lambda: self.batch_uninstall_dialog.emit([catalog["name"] for catalog in self.all_catalogs]))
        update_solutions = QAction("Update solution(s)")
        update_solutions.triggered.connect(self.update_solution_dialog)
        actions.addAction(update_solutions)
        actions.addAction(batch_uninstall)
        return actions.actions()

    def make_remove_catalog_action(self, catalog):
        def remove_catalog():
            self.remove_catalog.emit(catalog)
        return remove_catalog

    def _create_action_widget(self):
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        self.run_btn = create_btn(self, self.run_action, "Run", "Enter")
        self.run_btn.setMinimumWidth(100)
        self.run_btn.setAutoDefault(True)
        self.run_btn.setDefault(True)
        self.search_line.returnPressed.connect(self.run_btn.toggle)
        action_layout.addWidget(self.run_btn)
        self.return_pressed.connect(self.run_btn.keyPressEvent)
        self.esc_pressed.connect(self.close)
        action_widget.setContentsMargins(0, 2, 0, 0)
        return action_widget

    def _create_right(self):
        res_w = QWidget()
        res_w.setFixedWidth(270)

        self.version_combo = QComboBox()
        self.version_combo.currentIndexChanged.connect(self._update_focus_solution_version)

        res = QVBoxLayout(res_w)
        res.setContentsMargins(10, 10, 10, 0)

        self.selected_solution_group = QLabel("")
        self.selected_solution_name = QLabel("")
        self.solution_api_warning = QPushButton("Warning: Potential incompatibility")
        self.solution_api_warning.setIcon(self.style().standardIcon(QStyle.SP_MessageBoxWarning))
        self.solution_api_warning.clicked.connect(self.show_warning_dialog)

        self.selected_solution_description = self.create_readonly_textedit("No description provided.")
        content_widget = QWidget(res_w)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.addWidget(self.selected_solution_description)
        content_layout.addStretch()
        combo_layout_version = QHBoxLayout()
        combo_layout_version.addWidget(QLabel("Version: "))
        combo_layout_version.addWidget(self.version_combo)
        layout_group = QHBoxLayout()
        layout_group.addWidget(QLabel("Group: "))
        layout_group.addStretch()
        layout_group.addWidget(self.selected_solution_group)
        layout_name = QHBoxLayout()
        layout_name.addWidget(QLabel("Name: "))
        layout_name.addStretch()
        layout_name.addWidget(self.selected_solution_name)

        self.solution_locations = QVBoxLayout()

        res.addLayout(layout_group)
        res.addLayout(layout_name)
        res.addLayout(combo_layout_version)
        res.addWidget(self.selected_solution_description)
        res.addLayout(self.solution_locations)
        res.addWidget(self.solution_api_warning)
        res.addWidget(self._create_action_widget())
        self._update_focus_solution()
        return res_w

    def create_readonly_textedit(self, text):
        textedit = QTextEdit()
        textedit.setPlainText(text)
        textedit.setReadOnly(True)
        textedit.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Allows text selection but not editing
        textedit.setFocusPolicy(Qt.StrongFocus)
        textedit.setTextInteractionFlags(Qt.TextEditorInteraction)
        textedit.setWordWrapMode(1)  # Word wrap
        return textedit

    @staticmethod
    def show_warning_dialog():
        QMessageBox.warning(None, "Warning", "Your Album installation might be too old to install and run this solution. Please update your installation if you run into issues, for example by running the Album Install Wizard again. This will not uninstall or remove any existing solutions or catalogs.")

    @staticmethod
    def _create_status(title):
        label = QLabel("%s" % title)
        return label

    def _create_status_with_action(self, title, actions):
        label = QPushButton("%s" % title, self)
        self._set_actions(label, actions)
        return label

    def _set_actions(self, button, actions):
        menu = QMenu(button)
        # label.setContextMenuPolicy(Qt.ActionsContextMenu)
        menu.addActions(actions)
        button.setMenu(menu)

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            if key == Qt.Key_Return:
                self.return_pressed.emit(event)
            if key == Qt.Key_Escape:
                self.esc_pressed.emit(event)
            if source is self.search_line:
                key = event.key()
                if key == Qt.Key_Left or key == Qt.Key_Right or key == Qt.Key_Up or key == Qt.Key_Down:
                    self.list_widget.keyPressEvent(event)
        return super().eventFilter(source, event)

    def run_action(self):
        item = self._get_currently_selected_item()
        action = item.action
        if action.args:
            action.signal.emit(action.args)
        else:
            action.signal.emit()

    def _get_currently_selected_item(self):
        if len(self.list_widget.selectedIndexes()) > 0:
            source_index = self.proxy.mapToSource(self.list_widget.selectedIndexes()[0])
            item = self.search_model.item(source_index.row())
            return item
        return None

    def update_model(self):
        index = self.album_instance.get_index_as_dict()
        actions_list = []
        self.all_catalogs = []
        self.deletable_catalogs = []
        for catalog in index["catalogs"]:

            solutions = group_solutions_by_version(catalog)

            for solution_key in solutions:
                versions = solutions[solution_key]
                solution = get_newest_prefer_installed(versions)
                item = self._create_action_item(catalog, solution, solution_key, versions)
                actions_list.append(item)
        for catalog in index["catalogs"]:
            self.all_catalogs.append(catalog)
            if catalog["deletable"]:
                self.deletable_catalogs.append(catalog)

        actions_list.sort()
        self.search_model.removeRows(0, self.search_model.rowCount())
        for item in actions_list:
            self.search_model.appendRow(item)
        # self.search_model.set_list(actions_list)
        if self.list_widget:
            self.list_widget.select_first_item()
        self.collection_changed.emit()

    def _create_action_item(self, catalog, solution, solution_key, versions):
        coordinates = solution_coordinates(solution)
        if "title" in solution["setup"]:
            title = solution["setup"]["title"]
            if not title:
                title = coordinates
        else:
            title = coordinates
        item = ActionsListModel.ActionItem()
        item.setEditable(False)
        item.setCheckState(2 if installed(solution) else 0)
        item.setText("[%s] %s" % (catalog["name"], title))
        item.text = "[%s] %s" % (catalog["name"], title)
        item.action = CollectionWindow.Action(self.show_solution, full_coordinates(solution, catalog), versions, catalog)
        item.solution_key = solution_key
        return item

    def set_active(self):
        pass

    def set_not_active(self):
        pass

    @staticmethod
    def _get_solution_count(index_dict):
        count = 0
        for catalog in index_dict["catalogs"]:
            count += len(catalog["solutions"])
        return count

    @staticmethod
    def _get_installed_solution_count(index_dict):
        count = 0
        for catalog in index_dict["catalogs"]:
            count += len([solution for solution in catalog["solutions"] if installed(solution)])
        return count
