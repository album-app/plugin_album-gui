import sys
import unittest
from time import sleep
from unittest import mock
from unittest.mock import create_autospec

from PyQt5.QtWidgets import QApplication, QDialog
from album.api import Album
from album.core.api.model.collection_index import ICollectionIndex
from album.core.controller.album_controller import AlbumController
from album.core.controller.collection.collection_manager import CollectionManager
from album.core.controller.task_manager import TaskManager
from album.core.model.resolve_result import ResolveResult

from album.gui.dialog.update_solutions_dialog import UpdateSolutionDialog
from src.album.gui.app import AlbumGUI


class TestInteractiveGUI(unittest.TestCase):

    def test_gui_realworld(self):
        album = Album.Builder().build()
        album.load_or_create_collection()
        gui = AlbumGUI(album)
        gui.launch()
        gui.dispose()
        album.close()

    def test_gui(self):
        #mocks
        mock_album = mock.create_autospec(Album)
        mock_album.get_catalogs_as_dict.return_value = {
            "catalogs": [
                {
                    "name": "catalog1",
                    "src": "url1"
                },
                {
                    "name": "catalog2",
                    "src": "url2"
                }
            ]
        }
        mock_album.get_index_as_dict.return_value = self._mock_index_dict()
        mock_controller = mock.create_autospec(AlbumController)
        mock_album._controller = mock_controller
        mock_collection_manager = mock.create_autospec(CollectionManager)
        mock_controller.collection_manager.return_value = mock_collection_manager
        mock_collection_index = mock.create_autospec(ICollectionIndex)
        mock_collection_manager.get_collection_index.return_value = mock_collection_index
        mock_collection_index.get_recently_launched_solutions.return_value = [self._mock_resolve_result()]
        mock_task_manager = mock.create_autospec(TaskManager)
        mock_resolve_result = mock.create_autospec(ResolveResult)
        mock_album.resolve.return_value = mock_resolve_result
        mock_resolve_db_entry = self._mock_resolve_result()
        mock_resolve_result.database_entry.return_value = mock_resolve_db_entry
        mock_album.is_installed.return_value = False
        mock_task_manager.get_status.side_effect = [{"status": "RUNNING", "records": [
            {"msg": "heavy work....", "asctime": 0}
        ]}, {"status": "FINISHED", "records": [
            {"msg": "heavy work....", "asctime": 0},
            {"msg": "done.", "asctime": 1}
        ]}, {"status": "RUNNING", "records": [
            {"msg": "heavy work....", "asctime": 0}
        ]}, {"status": "FINISHED", "records": [
            {"msg": "heavy work....", "asctime": 0},
            {"msg": "done.", "asctime": 1}
        ]}]

        mock_controller._task_manager = mock_task_manager
        gui = AlbumGUI(mock_album)
        gui.launch()
        gui.dispose()
        mock_album.close()

    def test_gui_updates(self):
        #mocks
        mock_album = mock.create_autospec(Album)
        mock_album.get_catalogs_as_dict.return_value = {
            "catalogs": [
                {
                    "name": "catalog1",
                    "src": "url1"
                },
                {
                    "name": "catalog2",
                    "src": "url2"
                }
            ]
        }
        mock_album.get_index_as_dict.return_value = self._mock_index_dict_updates()
        mock_controller = mock.create_autospec(AlbumController)
        mock_album._controller = mock_controller
        mock_collection_manager = mock.create_autospec(CollectionManager)
        mock_controller.collection_manager.return_value = mock_collection_manager
        mock_collection_index = mock.create_autospec(ICollectionIndex)
        mock_collection_manager.get_collection_index.return_value = mock_collection_index
        mock_collection_index.get_recently_launched_solutions.return_value = [self._mock_resolve_result()]
        mock_album.install = lambda x: sleep(1)
        mock_album.uninstall = lambda x: sleep(1)
        mock_task_manager = mock.create_autospec(TaskManager)
        mock_resolve_result = mock.create_autospec(ResolveResult)
        mock_album.resolve.return_value = mock_resolve_result
        mock_resolve_db_entry = self._mock_resolve_result()
        mock_resolve_result.database_entry.return_value = mock_resolve_db_entry
        mock_album.is_installed.return_value = False
        mock_task_manager.get_status.side_effect = [{"status": "RUNNING", "records": [
            {"msg": "heavy work....", "asctime": 0}
        ]}, {"status": "FINISHED", "records": [
            {"msg": "heavy work....", "asctime": 0},
            {"msg": "done.", "asctime": 1}
        ]}, {"status": "RUNNING", "records": [
            {"msg": "heavy work....", "asctime": 0}
        ]}, {"status": "FINISHED", "records": [
            {"msg": "heavy work....", "asctime": 0},
            {"msg": "done.", "asctime": 1}
        ]}]

        mock_controller._task_manager = mock_task_manager
        gui = AlbumGUI(mock_album)
        gui.launch()
        gui.dispose()
        mock_album.close()

    def test_gui_solution(self):
        #mocks
        mock_album = mock.create_autospec(Album)
        mock_task_manager = mock.create_autospec(TaskManager)
        mock_resolve_result = mock.create_autospec(ResolveResult)
        mock_album.resolve.return_value = mock_resolve_result
        mock_resolve_db_entry = self._mock_resolve_result()
        mock_resolve_result.database_entry.return_value = mock_resolve_db_entry
        mock_album.is_installed.return_value = False
        mock_task_manager.get_status.side_effect = [{"status": "RUNNING", "records": [
            {"msg": "heavy work....", "asctime": 0}
        ]}, {"status": "FINISHED", "records": [
            {"msg": "heavy work....", "asctime": 0},
            {"msg": "done.", "asctime": 1}
        ]}, {"status": "RUNNING", "records": [
            {"msg": "heavy work....", "asctime": 0}
        ]}, {"status": "FINISHED", "records": [
            {"msg": "heavy work....", "asctime": 0},
            {"msg": "done.", "asctime": 1}
        ]}]

        gui = AlbumGUI(mock_album)
        solution = "solution.py"
        gui.launch(solution=solution)
        gui.dispose()
        mock_album.close()

    @staticmethod
    def _mock_resolve_result():
        mock_resolve_db_entry = mock.create_autospec(ICollectionIndex.ICollectionSolution)
        mock_resolve_db_entry.setup.return_value = {
            "group": "my-group",
            "name": "my-name",
            "version": "my-version",
            "title": "This is a solution",
            "description": "This solution does magical things.",
            "args": [
                {
                    "name": "inputsdf1",
                    "description": "this is a string parameter",
                    "type": "string",
                    "required": True,
                },
                {
                    "name": "input2",
                    "description": "this is a file parameter",
                    "type": "file"
                },
                {
                    "name": "input3_sdf",
                    "description": "this is a directory parameter, it's required, also, this description is a bit longer, to force a line break at some point",
                    "type": "directory",
                },
                {
                    "name": "input4",
                    "description": "this is a boolean parameter",
                    "type": "boolean"
                },
                {
                    "name": "input5",
                    "description": "this is a float parameter",
                    "type": "float"
                },
                {
                    "name": "input6",
                    "description": "this is a double parameter",
                    "type": "double"
                },
                {
                    "name": "input7",
                    "description": "this is an integer parameter",
                    "type": "integer"
                },
            ]
        }
        return mock_resolve_db_entry

    def test_gui_solution_update_widget(self):
        app = QApplication(sys.argv)
        album = create_autospec(Album)
        # album.upgrade = lambda x: sleep(1)
        album.get_index_as_dict.return_value = TestInteractiveGUI._mock_index_dict_updates()
        dialog = UpdateSolutionDialog(album)
        if dialog.exec_() == QDialog.Accepted:
            all_checked, checked_items = dialog.getCheckedItems()
            print("All choices activated: ", all_checked)
            print("Activated choices: ", checked_items)
        sys.exit(app.exec_())

    @staticmethod
    def _mock_index_dict():
        return {
            "base": "/home/deschmi/.album",
            "catalogs": [
                {
                    "branch_name": "main",
                    "catalog_id": 1,
                    "deletable": 0,
                    "name": "cache_catalog",
                    "path": "/home/deschmi/.album/catalogs/cache_catalog",
                    "solutions": [
                        {
                            "internal": {
                                "catalog_id": 1,
                                "children": [],
                                "collection_id": 13,
                                "hash": "930702db01e37d744cd59823d1485fd4",
                                "install_date": None,
                                "installation_unfinished": 1,
                                "installed": 0,
                                "last_execution": "2022-06-23T15:47:36.941544",
                                "parent": None,
                                "solution_id": None
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.4.2",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How do you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template running Java code via Gradle.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": None,
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-gradle-java11",
                                "tags": [
                                    "template",
                                    "java",
                                    "gradle"
                                ],
                                "timestamp": None,
                                "title": "Gradle template for Java 11",
                                "version": "0.1.0"
                            }
                        }
                    ],
                    "src": "/home/deschmi/.album/catalogs/cache_catalog",
                    "type": "direct"
                },
                {
                    "branch_name": "main",
                    "catalog_id": 2,
                    "deletable": 1,
                    "name": "default",
                    "path": "/home/deschmi/.album/catalogs/default",
                    "solutions": [
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 1,
                                "hash": "8b4dac3ffd778059adffb303324e7f8a",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 1
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "The output file name to where the processed boat image is going to be saved.",
                                        "name": "output_image_path",
                                        "type": "file"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": "- initial release\n",
                                "cite": [
                                    {
                                        "doi": "10.1038/nmeth.2019",
                                        "text": "Schindelin, J., Arganda-Carreras, I., Frise, E., Kaynig, V., Longair, M., Pietzsch, T., \u2026 Cardona, A. (2012). Fiji: an open-source platform for biological-image analysis. Nature Methods, 9(7), 676\u2013682. ",
                                        "url": "https://fiji.sc"
                                    }
                                ],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template run a macro script in Fiji.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6405812",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-fiji-macro",
                                "tags": [
                                    "template",
                                    "java",
                                    "fiji",
                                    "macro",
                                    "maven"
                                ],
                                "timestamp": "2022-04-01T13:10:34.597873",
                                "title": "Fiji Macro template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 2,
                                "hash": "78f2ebf59d3ee7eb159d560f1572c2e2",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 2
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "The image about to be displayed in Napari.",
                                        "name": "input_image_path",
                                        "type": "file"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [
                                    {
                                        "doi": "10.5281/zenodo.3555620",
                                        "text": "napari contributors (2019). napari: a multi-dimensional image viewer for python.",
                                        "url": "https://github.com/napari/napari"
                                    }
                                ],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template for running Napari.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6409780",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-napari",
                                "tags": [
                                    "template",
                                    "napari"
                                ],
                                "timestamp": "2022-04-03T15:18:31.509282",
                                "title": "Napari template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 3,
                                "hash": "eb830b05155f07324af5120f28c32b73",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 3
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How to you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template for running Python code.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6410028",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-python",
                                "tags": [
                                    "template",
                                    "python"
                                ],
                                "timestamp": "2022-04-03T18:24:50.029662",
                                "title": "Python template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 4,
                                "hash": "69109e24df430eba3a73068a78c148a1",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 4
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How do you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template running Java code via Maven, providing the POM and source file separately.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6410070",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-maven-java11",
                                "tags": [
                                    "template",
                                    "java",
                                    "maven"
                                ],
                                "timestamp": "2022-04-03T22:07:54.215169",
                                "title": "Maven template for Java 11",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 5,
                                "hash": "9b3bedc08ab3e040cb51f61ce35f284d",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 5
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How do you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [
                                    {
                                        "text": "scyjava - supercharged Java access from Python",
                                        "url": "https://pypi.org/project/scyjava"
                                    }
                                ],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template for running Java code via scyjava.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6410878",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-scyjava",
                                "tags": [
                                    "template",
                                    "java",
                                    "scyjava"
                                ],
                                "timestamp": "2022-04-04T08:09:30.950849",
                                "title": "ScyJava template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 6,
                                "hash": "ab7b68c6d4836610fb345f72253c368b",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 6
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How to you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [
                                    {
                                        "text": "R core team. R: A Language and Environment for Statistical Computing. R Foundation for Statistical Computing",
                                        "url": "https://www.R-project.org/"
                                    }
                                ],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template for running R code.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6411064",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-r",
                                "tags": [
                                    "template",
                                    "R"
                                ],
                                "timestamp": "2022-04-04T08:19:36.535409",
                                "title": "R template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 7,
                                "hash": "a00441ca2abb796b40f7e7d236dc711b",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 7
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "The output file name to where a random image is going to be saved.",
                                        "name": "output_image_path",
                                        "type": "file"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [
                                    {
                                        "doi": "10.1186/s12859-017-1934-z",
                                        "text": "Rueden, C. T., Schindelin, J., Hiner, M. C., DeZonia, B. E., Walter, A. E., Arena, E. T., & Eliceiri, K. W. (2017). ImageJ2: ImageJ for the next generation of scientific image data. BMC Bioinformatics, 18(1).",
                                        "url": "https://imagej.net"
                                    }
                                ],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template generating an ImgLib2 image with random values in ImageJ2.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6411110",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-imagej2",
                                "tags": [
                                    "template",
                                    "java",
                                    "imagej2",
                                    "scijava",
                                    "scyjava"
                                ],
                                "timestamp": "2022-04-04T09:52:14.034264",
                                "title": "ImageJ2 template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 8,
                                "hash": "7e1a3a4163d8fc51a0606c4c3757383d",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 8
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How do you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template running Java code via Maven, providing the POM and source file separately.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6411456",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-maven-java8",
                                "tags": [
                                    "template",
                                    "java",
                                    "maven"
                                ],
                                "timestamp": "2022-04-04T10:00:58.765589",
                                "title": "Maven template for Java 8",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 9,
                                "hash": "d873aa615a02ccf3008c1c70ecb81fb5",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 9
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How do you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template running Java code via Maven.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6411481",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-maven-singlefile",
                                "tags": [
                                    "template",
                                    "java",
                                    "maven"
                                ],
                                "timestamp": "2022-04-04T10:07:51.175463",
                                "title": "Maven template (single file version)",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 10,
                                "hash": "ba1b57a506ed4790f91294a520818427",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 10
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "The image about to be displayed in Icy.",
                                        "name": "input_image_path",
                                        "type": "file"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": "- initial release\n",
                                "cite": [
                                    {
                                        "doi": "10.1038/nmeth.2075",
                                        "text": "de Chaumont, F. et al. (2012). Icy: an open bioimage informatics platform for extended reproducible research, Nature Methods, 9, pp. 690-696",
                                        "url": "https://icy.bioimageanalysis.org"
                                    }
                                ],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template for running Icy.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6411528",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-icy",
                                "tags": [
                                    "template",
                                    "icy"
                                ],
                                "timestamp": "2022-04-04T10:20:07.946465",
                                "title": "Icy template",
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 11,
                                "hash": "3674d80ccbd91cab3e61a3483e702971",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 11
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [],
                                "authors": [],
                                "changelog": None,
                                "cite": [],
                                "covers": [],
                                "custom": {},
                                "description": None,
                                "documentation": [],
                                "doi": "10.5281/zenodo.6411558",
                                "group": "album",
                                "license": None,
                                "name": "template-minimal",
                                "tags": [],
                                "timestamp": "2022-04-04T10:57:14.810172",
                                "title": None,
                                "version": "0.1.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 11,
                                "hash": "3674d80ccbd91cab3e61a3483e702971",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 11
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.3.1",
                                "album_version": None,
                                "args": [],
                                "authors": [],
                                "changelog": None,
                                "cite": [],
                                "covers": [],
                                "custom": {},
                                "description": None,
                                "documentation": [],
                                "doi": "10.5281/zenodo.6411558",
                                "group": "album",
                                "license": None,
                                "name": "template-minimal",
                                "tags": [],
                                "timestamp": "2022-04-04T10:57:14.810172",
                                "title": None,
                                "version": "0.2.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 2,
                                "children": [],
                                "collection_id": 12,
                                "hash": "71097af4150c9a6434198a2dd92d2fba",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": 12
                            },
                            "setup": {
                                "acknowledgement": None,
                                "album_api_version": "0.4.2",
                                "album_version": None,
                                "args": [
                                    {
                                        "description": "How do you want to be addressed?",
                                        "name": "name",
                                        "type": "string"
                                    }
                                ],
                                "authors": [
                                    "Album team"
                                ],
                                "changelog": None,
                                "cite": [],
                                "covers": [
                                    {
                                        "description": "Dummy cover image.",
                                        "source": "cover.png"
                                    }
                                ],
                                "custom": {},
                                "description": "An Album solution template running Java code via Gradle.",
                                "documentation": [
                                    "documentation.md"
                                ],
                                "doi": "10.5281/zenodo.6580977",
                                "group": "album",
                                "license": "unlicense",
                                "name": "template-gradle-java11",
                                "tags": [
                                    "template",
                                    "java",
                                    "gradle"
                                ],
                                "timestamp": "2022-05-25T15:51:14.542630",
                                "title": "Gradle template for Java 11",
                                "version": "0.1.0"
                            }
                        }
                    ],
                    "src": "https://gitlab.com/album-app/catalogs/default",
                    "type": "request"
                }
            ]
        }

    @staticmethod
    def _mock_index_dict_updates():
        return {
            "base": "/path/to/base",
            "catalogs": [
                {
                    "branch_name": "main",
                    "catalog_id": 1,
                    "deletable": 0,
                    "name": "first_catalog",
                    "path": "/path/to/first_catalog",
                    "solutions": [
                        {
                            "internal": {
                                "catalog_id": 1,
                                "children": [],
                                "collection_id": 1,
                                "hash": "old_hash",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 1,
                                "last_execution": "2021-01-01T00:00:00",
                                "parent": None,
                                "solution_id": None
                            },
                            "setup": {
                                "group": "generic",
                                "name": "single_version",
                                "version": "1.0.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 1,
                                "children": [],
                                "collection_id": 1,
                                "hash": "old_hash",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 1,
                                "last_execution": "2021-01-01T00:00:00",
                                "parent": None,
                                "solution_id": None
                            },
                            "setup": {
                                "group": "generic",
                                "name": "solution1",
                                "version": "1.0.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 1,
                                "children": [],
                                "collection_id": 2,
                                "hash": "new_hash",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 0,
                                "last_execution": None,
                                "parent": None,
                                "solution_id": None
                            },
                            "setup": {
                                "group": "generic",
                                "name": "solution1",
                                "version": "2.0.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 1,
                                "children": [2],
                                "collection_id": 3,
                                "hash": "old_hash_parent",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 1,
                                "last_execution": "2021-01-01T00:00:00",
                                "parent": None,
                                "solution_id": None
                            },
                            "setup": {
                                "group": "generic",
                                "name": "common_solution_parent",
                                "version": "1.0.0"
                            }
                        },
                        {
                            "internal": {
                                "catalog_id": 1,
                                "children": [1],
                                "collection_id": 4,
                                "hash": "new_hash_parent",
                                "install_date": None,
                                "installation_unfinished": 0,
                                "installed": 1,
                                "last_execution": "2021-01-01T00:00:00",
                                "parent": None,
                                "solution_id": None
                            },
                            "setup": {
                                "group": "generic",
                                "name": "common_solution_parent",
                                "version": "2.0.0"
                            }
                        }
                    ],
                    "src": "/path/to/first_catalog_src",
                    "type": "direct"
                }
            ]
        }

if __name__ == '__main__':
    TestInteractiveGUI().run()
