import unittest
from unittest import mock

from album.api import Album
from album.core.api.model.collection_index import ICollectionIndex
from album.core.controller.task_manager import TaskManager
from album.core.model.resolve_result import ResolveResult

from src.album.gui import AlbumGUI


class TestInteractiveGUI(unittest.TestCase):

    def test_gui(self):
        #mocks
        mock_album = mock.create_autospec(Album)
        mock_task_manager = mock.create_autospec(TaskManager)
        mock_resolve_result = mock.create_autospec(ResolveResult)
        mock_album.resolve.return_value = mock_resolve_result
        mock_resolve_db_entry = mock.create_autospec(ICollectionIndex.ICollectionSolution)
        mock_resolve_result.database_entry.return_value = mock_resolve_db_entry
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
                    "name": "input5",
                    "description": "this is a double parameter",
                    "type": "double"
                },
                {
                    "name": "input5",
                    "description": "this is an integer parameter",
                    "type": "integer"
                },
            ]
        }
        mock_album.is_installed.return_value = False
        mock_album.run.return_value = {
            "id": "0"
        }
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

        gui = AlbumGUI(mock_album, mock_task_manager)
        solution = "solution.py"
        if solution:
            gui.launch_solution(solution)
        else:
            gui.launch()
        gui.dispose()
        mock_album.close()


if __name__ == '__main__':
    TestInteractiveGUI().run()
