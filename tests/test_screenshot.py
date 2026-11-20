import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from app.screenshot_renderer import render_screenshots
from app.volatility_runner import VolatilityRunner


class ScreenshotTests(unittest.TestCase):
    def test_standalone_screenshot_loads_external_plugin(self):
        with tempfile.TemporaryDirectory() as directory:
            runner = VolatilityRunner(directory)
            runner.vol2_custom_exe = 'volatility.exe'
            command = runner.build_command('vol2', 'image.raw', 'screenshot', 'Win7SP1x64')
            self.assertEqual(command[0], 'volatility.exe')
            self.assertTrue((Path(command[command.index('--plugins') + 1]) / 'gui_screenshot.py').is_file())
            self.assertIn('guiscreenshot', command)
            self.assertEqual(command[command.index('-D') + 1], runner.output_dir)

    def test_geometry_produces_valid_png_and_rejects_invalid_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'desktop.png'
            desktop = dict(path=str(path), width=100, height=80, windows=[
                dict(window=[10, 10, 90, 70], client=[12, 25, 88, 68], title='Window')])
            output = 'GUI_SCREENSHOT ' + json.dumps(desktop)
            self.assertEqual(render_screenshots(output), [path])
            with Image.open(path) as image:
                self.assertEqual(image.format, 'PNG')
                self.assertEqual(image.size, (100, 80))
                self.assertEqual(image.getpixel((10, 10)), (0, 0, 0))
            desktop['width'] = -1
            with self.assertRaises(ValueError):
                render_screenshots('GUI_SCREENSHOT ' + json.dumps(desktop))
            self.assertFalse(path.with_suffix('.png.partial').exists())
