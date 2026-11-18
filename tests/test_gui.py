import asyncio
import csv
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.volatility_runner import VolatilityRunner, parse_tabular_output, parse_process_tree, split_arguments, tasks_store


class RunnerTests(unittest.TestCase):
    def test_vol2_catalog_includes_shell_history_and_environment(self):
        from app.plugin_catalog import VOLATILITY_2_PLUGINS
        catalog = {item['name']: item for item in VOLATILITY_2_PLUGINS}
        self.assertEqual(len(catalog), len(VOLATILITY_2_PLUGINS))
        for name in ('cmdscan', 'consoles', 'envars', 'dlllist', 'handles', 'hivelist', 'printkey', 'procdump', 'psxview'):
            self.assertIn(name, catalog)
        self.assertEqual([opt['name'] for opt in catalog['consoles']['options']], ['-M', '-B'])
        self.assertIn('-p', [opt['name'] for opt in catalog['envars']['options']])
        self.assertNotIn('volshell', catalog)
        self.assertNotIn('patcher', catalog)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.runner = VolatilityRunner(self.temp.name)

    def test_windows_arguments_and_pid_list(self):
        command = self.runner.build_command('vol3', 'C:\\memory dump.raw', 'windows.pslist',
                    options={'--pid': '4, 120 300', '--dump': False},
                    custom_args=r'--key "Software\Microsoft\Windows"')
        self.assertEqual(command[command.index('--pid') + 1:command.index('--key')], ['4', '120', '300'])
        self.assertEqual(command[-1], r'Software\Microsoft\Windows')
        self.assertNotIn('--dump', command)

    def test_vol2_dump_directory_default(self):
        for name in ('procdump', 'memdump', 'vaddump', 'dumpregistry'):
            command = self.runner.build_command('vol2', 'memory.raw', name, profile='Win7SP1x86')
            self.assertEqual(command[command.index('-D') + 1], self.runner.output_dir)

    @unittest.skipUnless(os.name == 'nt', 'Windows UNC path')
    def test_wsl_unc_uses_complete_uri(self):
        command = self.runner.build_command('vol3', r'\\wsl.localhost\Ubuntu\home\test (1)\image.raw', 'windows.info')
        self.assertNotIn('-f', command)
        self.assertEqual(command[command.index('--single-location') + 1],
                         'file://wsl.localhost/Ubuntu/home/test%20%281%29/image.raw')

    def test_config_persistence_and_atomic_validation(self):
        self.runner.update_config({'vol3_command': sys.executable, 'output_dir': 'artifacts'})
        loaded = VolatilityRunner(self.temp.name)
        self.assertEqual(loaded.vol3_cmd, sys.executable)
        with self.assertRaises(ValueError):
            loaded.update_config({'vol3_command': 'changed', 'output_dir': ''})
        self.assertEqual(loaded.vol3_cmd, sys.executable)

    def test_global_options_precede_plugin(self):
        command = self.runner.build_command('vol3', 'image.raw', 'windows.info', custom_args='--offline -s "C:\\my symbols" --help')
        self.assertLess(command.index('--offline'), command.index('windows.info'))
        self.assertLess(command.index('-s'), command.index('windows.info'))
        self.assertEqual(command[-1], '--help')

    def test_csv_preserves_multiline_empty_and_header_only(self):
        text = 'Volatility 3 Framework 2.28.2\nTreeDepth,PID,Name,Command\n0,4,System,"line one\nline two, #?"\n1,5,,end\n'
        table = parse_tabular_output(text)
        self.assertEqual(table['rows'][0][-1], 'line one\nline two, #?')
        self.assertEqual(table['rows'][1][2], '')
        self.assertEqual(parse_tabular_output('TreeDepth,PID,Name\n')['columns'], ['TreeDepth', 'PID', 'Name'])

    def test_vol2_fixed_width_and_tree(self):
        header = f"{'Name':<30} {'Pid':>6} {'PPid':>6} {'Time'}"
        sep = '-' * 30 + ' ' + '-' * 6 + ' ' + '-' * 6 + ' ' + '-' * 20
        row = f"{'0x1234:System':<30} {4:>6} {0:>6} 2018-10-23 08:30:51"
        table = parse_tabular_output('\n'.join([header, sep, row]))
        self.assertEqual(table['rows'][0], ['0x1234:System', '4', '0', '2018-10-23 08:30:51'])
        self.assertEqual(parse_process_tree('. 0x1234:child.exe 120 4 2 10')[0]['ppid'], '4')
        self.assertEqual(parse_tabular_output('Suggested Profile(s) : Win7SP1x86\nImage date and time : 2018-10-23')['rows'][0], ['Suggested Profile(s)', 'Win7SP1x86'])

    def test_stream_large_output_separates_stderr_and_extracts(self):
        async def scenario():
            task = self.runner.create_task('test-success', 'vol3', 'fixture.raw', 'windows.pstree')
            self.addCleanup(tasks_store.pop, task['id'], None)
            script = ("import sys,pathlib; p=pathlib.Path(sys.argv[1]); "
                      "(p/'child').mkdir(); (p/'child'/'dump.bin').write_bytes(b'abc'); "
                      "print('TreeDepth,PID,PPID,ImageFileName,Command'); "
                      "print('0,4,0,System,'+'x'*100000); "
                      "print('1,8,4,child.exe,hello'); print('diagnostic',file=sys.stderr)")
            task['command_list'] = [sys.executable, '-c', script, task['output_dir']]
            await self.runner.run_task(task['id'], 'vol3', 'fixture.raw', 'windows.pstree')
            self.assertEqual(task['status'], 'SUCCESS')
            self.assertEqual(len(task['table_data']['rows']), 2)
            self.assertEqual(task['tree_data'][1]['level'], 1)
            self.assertEqual(task['extracted_files'][0]['size'], 3)
            self.assertIn('diagnostic', task['raw_logs'])
        asyncio.run(scenario())

    def test_cancel_running_and_queued(self):
        async def scenario():
            task = self.runner.create_task('test-cancel', 'vol3', 'fixture.raw', 'windows.info')
            self.addCleanup(tasks_store.pop, task['id'], None)
            task['command_list'] = [sys.executable, '-u', '-c', 'import time; print("ready"); time.sleep(60)']
            job = asyncio.create_task(self.runner.run_task(task['id'], 'vol3', 'fixture.raw', 'windows.info'))
            for _ in range(200):
                if 'ready' in task['raw_logs']:
                    break
                await asyncio.sleep(.01)
            self.assertIn('ready', task['raw_logs'])
            self.assertTrue(self.runner.kill_task(task['id']))
            await asyncio.wait_for(job, 5)
            self.assertEqual(task['status'], 'KILLED')
            self.assertIsNone(task['process'])
            task2 = self.runner.create_task('test-queued', 'vol3', 'fixture.raw', 'windows.info')
            self.addCleanup(tasks_store.pop, task2['id'], None)
            self.assertTrue(self.runner.kill_task(task2['id']))
            await self.runner.run_task(task2['id'], 'vol3', 'fixture.raw', 'windows.info')
            self.assertEqual(task2['status'], 'KILLED')
        asyncio.run(scenario())

    def test_api_rejects_invalid_requests(self):
        with TestClient(main.app) as client:
            for payload in [dict(engine='bad', image_path='missing', plugin_name='windows.info'),
                            dict(engine='vol3', image_path='missing', plugin_name='windows.info')]:
                response = client.post('/api/run', json=payload)
                self.assertEqual(response.status_code, 400)
            self.assertEqual(client.get('/api/task/missing/stream').status_code, 404)
            with patch.object(main.runner, 'get_config', return_value={'vol3_ready': True}):
                response = client.post('/api/run', json=dict(engine='vol3', image_path=__file__, plugin_name='wrong'))
                self.assertEqual(response.status_code, 400)
                response = client.post('/api/run', json=dict(engine='vol3', image_path=__file__, plugin_name='windows.pedump'))
                self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
