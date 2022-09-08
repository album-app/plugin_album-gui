#!/usr/bin/env python

import os
import sys
from collections import namedtuple

UserFolders = namedtuple("UserFolders", ("home", "desktop", "startmenu"))

uname = sys.platform
if os.name == "nt":
    uname = "win"
if uname == "linux2":
    uname = "linux"

from .linux import (scut_ext, ico_ext, make_shortcut,
                    get_folders, get_homedir, get_desktop)

if uname.startswith('win'):
    from .windows import (scut_ext, ico_ext, make_shortcut,
                          get_folders, get_homedir, get_desktop)

elif uname.startswith('darwin'):
    from .darwin import (scut_ext, ico_ext, make_shortcut,
                         get_folders, get_homedir, get_desktop)

from .shortcut import shortcut, Shortcut, fix_filename


def get_cwd():
    """get current working directory
    Note: os.getcwd() can fail with permission error.

    when that happens, this changes to the users `HOME` directory
    and returns that directory so that it always returns an existing
    and readable directory.
    """
    try:
        return os.getcwd()
    except:
        home = get_homedir()
        os.chdir(home)
        return home

try:
    import wx
    HAS_WX = True
    from .wxgui import ShortcutFrame
except ImportError:
    HAS_WX = False
