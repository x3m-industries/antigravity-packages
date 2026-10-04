#!/usr/bin/env python3
"""
Nautilus (GNOME Files) and Caja (MATE) context-menu extension for Antigravity IDE.
Adds right-click options:
- "Open in Antigravity IDE" on files and directories.
- "Open Folder in Antigravity IDE" on folder backgrounds.
Maintained by X3M Industries (https://github.com/x3m-industries/antigravity-packages)
"""

import subprocess
from urllib.parse import unquote, urlparse
import gi
from gi.repository import GObject

for _ver in ["4.1", "4.0", "3.0"]:
    try:
        gi.require_version("Nautilus", _ver)
        break
    except (ValueError, AttributeError):
        pass

for _ver in ["3.0", "2.0"]:
    try:
        gi.require_version("Caja", _ver)
        break
    except (ValueError, AttributeError):
        pass

try:
    from gi.repository import Nautilus as FM
except ImportError:
    try:
        from gi.repository import Caja as FM
    except ImportError:
        FM = None


class OpenInAntigravityIDE(GObject.GObject, FM.MenuProvider if FM else object):
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
        if not FM:
            return []
        # Support both 3.x (files) and 4.x (window, files) signatures
        files = args[-1] if args else []
        if not files:
            return []

        paths = [self._get_path(f) for f in files]
        paths = [p for p in paths if p]
        if not paths:
            return []

        item = FM.MenuItem(
            name="OpenInAntigravityIDE::open",
            label="Open in Antigravity IDE",
            tip="Open selected items in Antigravity IDE",
            icon="antigravity-ide",
        )
        item.connect("activate", lambda _menu_item, target_paths=paths: subprocess.Popen(["antigravity-ide"] + target_paths))
        return [item]

    def get_background_items(self, *args):
        if not FM:
            return []
        # Support both 3.x (folder) and 4.x (window, folder) signatures
        folder = args[-1] if args else None
        if not folder:
            return []

        path = self._get_path(folder)
        if not path:
            return []

        item = FM.MenuItem(
            name="OpenInAntigravityIDE::open_background",
            label="Open Folder in Antigravity IDE",
            tip="Open current folder in Antigravity IDE",
            icon="antigravity-ide",
        )
        item.connect("activate", lambda _menu_item, target_path=path: subprocess.Popen(["antigravity-ide", target_path]))
        return [item]
