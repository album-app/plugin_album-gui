from album.api import Album

from album.gui.app import AlbumGUI


def run(album_instance: Album, args):
    gui = _create_gui(album_instance)
    solution = args.solution
    if solution:
        gui.launch(solution=solution)
    else:
        gui.launch()
    gui.dispose()


def _create_gui(album_instance):
    return AlbumGUI(album_instance)


def create_parser(parser):
    p = parser.create_command_parser('gui', run, 'Launch the Album GUI.')
    p.add_argument('solution', type=str,
                   help='path for the solution file or coordinates of the solution (group:name:version)', nargs='?')
