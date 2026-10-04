#!/usr/bin/env python3
"""
Nautilus (GNOME Files) context-menu extension for Antigravity IDE.
Adds right-click options:
- "Open in Antigravity IDE" on files and directories.
- "Open Folder in Antigravity IDE" on folder backgrounds.
Maintained by X3M Industries (https://github.com/x3m-industries/antigravity-packages)
"""

import subprocess
from urllib.parse import unquote, urlparse
from gi.repository import GObject, Nautilus


class OpenInAntigravityIDE(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()

    def _get_path(self, file_info):
        if not file_info:
            return None
        uri = file_info.get_uri()
        parsed = urlparse(uri)
        if parsed.scheme != "file":
            return None
        return unquote(parsed.path)

    def get_file_items(self, *args):
        # Support both Nautilus 3.x (files) and 4.x (window, files) signatures
        files = args[-1] if args else []
        if not files or len(files) != 1:
            return []

        path = self._get_path(files[0])
        if not path:
            return []

        item = Nautilus.MenuItem(
            name="OpenInAntigravityIDE::open",
            label="Open in Antigravity IDE",
            tip="Open this file or folder in Antigravity IDE",
            icon="antigravity-ide",
        )
        item.connect("activate", lambda _menu_item: subprocess.Popen(["antigravity-ide", path]))
        return [item]

    def get_background_items(self, *args):
        # Support both Nautilus 3.x (folder) and 4.x (window, folder) signatures
        folder = args[-1] if args else None
        if not folder:
            return []

        path = self._get_path(folder)
        if not path:
            return []

        item = Nautilus.MenuItem(
            name="OpenInAntigravityIDE::open_background",
            label="Open Folder in Antigravity IDE",
            tip="Open current folder in Antigravity IDE",
            icon="antigravity-ide",
        )
        item.connect("activate", lambda _menu_item: subprocess.Popen(["antigravity-ide", path]))
        return [item]
