"""Refresh the bundled GUI catalog from the installed Volatility 2 executable."""
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
executable = next((root / 'bin').glob('**/volatility*standalone.exe'))
result = subprocess.run([str(executable), '-h'], capture_output=True, text=True, errors='replace', timeout=30, check=True)
plugins = [{'name': match[0], 'desc': match[1].strip()} for match in
           re.findall(r'^\t\t([a-z][a-z0-9_]*)[ \t]+([^\r\n]+)', result.stdout, re.M)]
if len(plugins) < 20:
    raise RuntimeError('Could not read the standalone plugin list; catalog was not changed.')
(root / 'app' / 'vol2_catalog.json').write_text(json.dumps(plugins, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Synced {len(plugins)} Volatility 2 plugins.')
