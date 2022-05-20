from album.api import Album
from album.core.controller.task_manager import TaskManager

from album.gui import AlbumGUI


def run(album_instance: Album, args):
    task_manager = TaskManager()
    gui = AlbumGUI(album_instance, task_manager)
    solution = args.solution
    if solution:
        gui.launch_solution(solution)
    else:
        gui.launch()
    gui.dispose()


def create_parser(parser):
    p = parser.create_command_parser('gui', run, 'Launch the Album GUI.')
    p.add_argument('solution', type=str, help='path for the solution file or coordinates of the solution (group:name:version)')
