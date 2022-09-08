from album.api import Album

from album.gui.app import AlbumGUI
from album.gui.create_shortcut import create_shortcut


def launch_gui(album_instance: Album, args):
    gui = _create_gui(album_instance)
    solution = args.solution
    if solution:
        gui.launch(solution=solution)
    else:
        gui.launch()
    gui.dispose()


def _create_gui(album_instance):
    return AlbumGUI(album_instance)


def create_parser_gui(parser):
    p = parser.create_command_parser('gui', launch_gui, 'Launch the Album GUI.')
    p.add_argument('solution', type=str,
                   help='path for the solution file or coordinates of the solution (group:name:version)', nargs='?')


def create_parser_shortcut(parser):
    p = parser.create_command_parser('add-shortcut', create_shortcut, 'Create shortcut for Album.')
    p.add_argument('solution', type=str,
                   help='path for the solution file or coordinates of the solution (group:name:version)', nargs='?')
