"""Render the window geometry exported by the Volatility 2 GUI plugin."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def render_screenshots(output):
    paths = []
    font = ImageFont.load_default()
    for line in output.splitlines():
        if not line.startswith('GUI_SCREENSHOT '):
            continue
        desktop = json.loads(line[len('GUI_SCREENSHOT '):])
        width, height = desktop['width'], desktop['height']
        if width <= 0 or height <= 0 or width * height > 40000000:
            raise ValueError('Invalid GDI desktop dimensions: {} x {}'.format(width, height))
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        for window in desktop['windows']:
            for rectangle in (window['window'], window['client']):
                left, top, right, bottom = rectangle
                if right >= left and bottom >= top:
                    draw.rectangle(rectangle, outline='black', fill='white')
            left, top = window['window'][:2]
            draw.multiline_text((left + 2, top), window['title'].replace('\r\n', '\n'),
                                font=font, fill='black', spacing=0)
        path = Path(desktop['path'])
        partial = path.with_suffix('.png.partial')
        try:
            image.save(partial, format='PNG')
            partial.replace(path)
        finally:
            image.close()
            partial.unlink(missing_ok=True)
        paths.append(path)
    return paths
