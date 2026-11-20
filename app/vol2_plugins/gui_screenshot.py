"""Export GDI window geometry for the GUI's Python 3 image renderer."""
import json
import os

import volatility.debug as debug
import volatility.plugins.gui.screenshot as screenshot


class GuiScreenshot(screenshot.Screenshot):
    """Export pseudo-screenshot geometry without requiring bundled PIL."""

    def render_text(self, outfd, data):
        if not self._config.DUMP_DIR or not os.path.isdir(self._config.DUMP_DIR):
            debug.error("Please supply an existing --dump-dir")
        seen = set()
        for station in data:
            for desktop in station.desktops():
                offset = int(desktop.PhysicalAddress)
                if offset in seen:
                    continue
                seen.add(offset)
                foreground = desktop.DeskInfo.spwnd
                if not foreground:
                    continue
                windows = []
                for window, _level in desktop.windows(
                        win=foreground,
                        filter=lambda item: 'WS_VISIBLE' in str(item.style)):
                    windows.append(dict(
                        window=[int(value) for value in window.rcWindow.get_tup()],
                        client=[int(value) for value in window.rcClient.get_tup()],
                        title=unicode(window.strName or '')))
                filename = "session_{0}.{1}.{2}.png".format(
                    desktop.dwSessionId, station.Name, desktop.Name)
                # Memory-derived names must remain inside the chosen directory.
                filename = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
                payload = dict(path=os.path.join(self._config.DUMP_DIR, filename),
                               width=int(foreground.rcWindow.right) + 1,
                               height=int(foreground.rcWindow.bottom) + 1,
                               windows=windows)
                outfd.write('GUI_SCREENSHOT ' + json.dumps(payload) + '\n')
