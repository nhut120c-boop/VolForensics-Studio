import asyncio
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.volatility_runner import VolatilityRunner, tasks_store


class MemmapJSONTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.runner = VolatilityRunner(self.temp.name)

    def task(self, name, plugin):
        task = self.runner.create_task(name, 'vol2' if plugin == 'memmap' else 'vol3', 'fixture.raw', plugin)
        self.addCleanup(tasks_store.pop, name, None)
        return task

    def test_memmap_uses_streaming_engine_output_for_json_conversion(self):
        for engine, plugin in [('vol2', 'memmap'), ('vol3', 'windows.memmap')]:
            cmd = self.runner.build_command(engine, 'image.raw', plugin)
            if engine == 'vol2':
                self.assertNotIn('--output=json', cmd)
            else:
                self.assertEqual(cmd[cmd.index('-r') + 1], 'csv')

    def test_large_result_goes_to_disk_without_table_or_stdout_logs(self):
        async def run():
            task = self.task('memmap-large-test', 'windows.memmap')
            task['command_list'] = [sys.executable, '-c',
                "print('TreeDepth,Virtual,Physical,Size'); "
                "print(''.join('0,0x%x,0x%x,0x1000\\n' % (n*4096,n*4096) for n in range(55000)),end='')"]
            await self.runner.run_task(task['id'], 'vol3', 'fixture.raw', 'windows.memmap')
            self.assertEqual(task['status'], 'SUCCESS')
            self.assertEqual(task['json_export']['rows_count'], 55000)
            self.assertEqual(task['table_data'], {'columns': [], 'rows': []})
            self.assertLess(len(task['raw_logs']), 5)
            self.assertEqual(len(json.loads(Path(task['json_export']['path']).read_text())), 55000)
        asyncio.run(run())

    def test_invalid_or_partial_json_is_not_published(self):
        async def run():
            task = self.task('memmap-invalid-test', 'windows.memmap')
            task['command_list'] = [sys.executable, '-c', "print('not JSON')"]
            await self.runner.run_task(task['id'], 'vol3', 'fixture.raw', 'windows.memmap')
            self.assertEqual(task['status'], 'ERROR')
            self.assertNotIn('json_export', task)
            self.assertEqual(task['extracted_files'], [])
        asyncio.run(run())

    def test_vol2_export_preserves_process_boundaries(self):
        task = self.task('memmap-vol2-test', 'memmap')
        directory = Path(task['output_dir'])
        directory.mkdir()
        (directory/'memmap.output.partial').write_text('System pid: 4\nVirtual Physical Size DumpFileOffset\n0x1000 0x2000 0x1000 0x0\n***\ncmd.exe pid: 2096\nVirtual Physical Size DumpFileOffset\n0x3000 0x4000 0x1000 0x0\n', encoding='utf-8')
        self.runner.finalize_memmap_json(task)
        data = json.loads(Path(task['json_export']['path']).read_text())
        self.assertEqual([r['PID'] for r in data], [4, 2096])
        self.assertEqual(data[1]['Process'], 'cmd.exe')

    def test_existing_large_task_returns_small_response_and_full_download(self):
        task = self.task('memmap-legacy-test', 'windows.memmap')
        task.update(status='SUCCESS', table_data={'columns': ['PID', 'Virtual'],
                    'rows': [['4', str(i)] for i in range(55000)]}, raw_logs=['large output'] * 55000)
        with patch.object(main, 'runner', self.runner), TestClient(main.app) as client:
            response = client.get('/api/task/' + task['id'])
            self.assertEqual(response.status_code, 200)
            self.assertLess(len(response.content), 5000)
            self.assertEqual(response.json()['table_data']['rows'], [])
            downloaded = client.get('/api/task/' + task['id'] + '/export-json')
            self.assertEqual(downloaded.status_code, 200)
            self.assertEqual(len(downloaded.json()), 55000)
            self.assertIn('attachment;', downloaded.headers['content-disposition'])


if __name__ == '__main__':
    unittest.main()
