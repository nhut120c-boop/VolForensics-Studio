import subprocess
import unittest
from pathlib import Path

from app.plugin_catalog import VOLATILITY_3_PLUGINS
from app.volatility_runner import VolatilityRunner


class Vol3ExpansionTests(unittest.TestCase):
    def test_expanded_catalog_is_unique_and_keeps_memmap_alias(self):
        names = [item['name'] for item in VOLATILITY_3_PLUGINS]
        self.assertEqual(len(names), len(set(names)))
        self.assertGreaterEqual(len(names), 80)
        for name in ('windows.cmdscan.CmdScan', 'windows.consoles.Consoles', 'windows.vadinfo.VadInfo',
                     'windows.malware.psxview.PsXView', 'windows.mftscan.MFTScan', 'windows.memmap'):
            self.assertIn(name, names)
        self.assertNotIn('windows.memmap.Memmap', names)

    def test_list_and_choice_forms_build_commands_the_installed_cli_accepts(self):
        runner = VolatilityRunner(str(Path(__file__).resolve().parents[1]))
        for plugin, options in [
            ('windows.cmdscan.CmdScan', {'--max-history': '50, 100', '--no-registry': True}),
            ('windows.pe_symbols.PESymbols', {'--source': 'kernel', '--module': 'ntoskrnl.exe'}),
        ]:
            command = runner.build_command('vol3', '', plugin, options=options, custom_args='--help')
            result = subprocess.run(command, capture_output=True, text=True, errors='replace',
                                    env=runner._environment('vol3'), timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn('unrecognized arguments', result.stderr)
            if plugin.endswith('CmdScan'):
                index = command.index('--max-history')
                self.assertEqual(command[index + 1:index + 3], ['50', '100'])


if __name__ == '__main__':
    unittest.main()
