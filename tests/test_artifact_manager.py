import hashlib
import json
import tempfile
import unittest
import asyncio
import sys
from unittest.mock import patch
from pathlib import Path

from app.artifact_manager import recover_dump_names


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def put(self, original, content, cache='ImageSectionObject', suffix='img'):
        path = self.root / f'file.0x123.0x456.{cache}.{original}.{suffix}'
        path.write_bytes(content)
        return path

    def test_preserve_original_bytes_extension_and_cache_variants(self):
        pe = bytearray(128)
        pe[:2] = b'MZ'
        pe[60:64] = (64).to_bytes(4, 'little')
        pe[64:68] = b'PE\0\0'
        source = self.put('sample.exe', pe)
        second = self.put('sample.exe', b'different cache', 'DataSectionObject', 'dat')
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = recover_dump_names(self.root)
        self.assertEqual(result['copied_count'], 2)
        for record in result['files']:
            target = Path(record['recovered_path'])
            self.assertEqual(target.suffix, '.exe')
            self.assertEqual(target.read_bytes(), before[record['source_name']])
            self.assertEqual(record['sha256'], hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(result['files'][0]['file_type'] if result['files'][0]['source_name'] == source.name else result['files'][1]['file_type'], 'PE (EXE/DLL)')
        for name, content in before.items():
            self.assertEqual((self.root / name).read_bytes(), content)
        again = recover_dump_names(self.root)
        self.assertEqual(again['copied_count'], 2)
        self.assertEqual(len(list((self.root / 'recovered').rglob('*.exe'))), 2)

    def test_empty_and_missing_pages_have_explicit_warnings(self):
        self.put('empty.dll', b'')
        self.put('missing.pdf', b'\0' * 8192, 'DataSectionObject', 'dat')
        result = recover_dump_names(self.root)
        self.assertEqual(result['empty_count'], 1)
        empty = next(r for r in result['files'] if r['size'] == 0)
        self.assertIsNone(empty['recovered_path'])
        self.assertIn('0 byte', empty['warning'])
        missing = next(r for r in result['files'] if r['size'])
        self.assertTrue(missing['warning'])
        self.assertEqual(missing['file_type'], 'Chưa xác định')

    def test_real_img_extension_is_preserved_and_unrelated_files_ignored(self):
        self.put('disk.img', b'original image')
        (self.root / 'other.img').write_bytes(b'do not alter')
        result = recover_dump_names(self.root)
        self.assertEqual(len(result['files']), 1)
        self.assertTrue(result['files'][0]['recovered_name'].endswith('__disk.img'))
        self.assertEqual((self.root / 'other.img').read_bytes(), b'do not alter')

    def test_existing_modified_copy_is_never_overwritten(self):
        self.put('sample.txt', b'original')
        result = recover_dump_names(self.root)
        target = Path(result['files'][0]['recovered_path'])
        target.write_bytes(b'user changes')
        retry = recover_dump_names(self.root)
        self.assertEqual(retry['error_count'], 1)
        self.assertIn('Không ghi đè', retry['files'][0]['warning'])
        self.assertEqual(target.read_bytes(), b'user changes')

    def test_runner_only_describes_names_without_reading_or_copying_outputs(self):
        from app.volatility_runner import VolatilityRunner, tasks_store
        async def run():
            runner = VolatilityRunner(str(self.root))
            task = runner.create_task('artifact-integration', 'vol3', 'image.raw', 'windows.dumpfiles')
            self.addCleanup(tasks_store.pop, task['id'], None)
            task['command_list'] = [sys.executable, '-c',
                "import pathlib,sys; p=pathlib.Path(sys.argv[1]); "
                "(p/'file.0x123.0x456.DataSectionObject.sample.pdf.dat').write_bytes(b'%PDF-1.7\\nexample'); "
                "(p/'file.0x789.0xabc.ImageSectionObject.empty.dll.img').write_bytes(b''); "
                "print('TreeDepth,Cache,FileObject,FileName,Result')", task['output_dir']]
            with patch('app.artifact_manager.recover_dump_names', side_effect=AssertionError('Automatic recovery must not run')), \
                 patch('app.artifact_manager._file_type', side_effect=AssertionError('Output payload must not be read')):
                await runner.run_task(task['id'], 'vol3', 'image.raw', 'windows.dumpfiles')
            self.assertEqual(task['status'], 'SUCCESS')
            self.assertNotIn('recovery_summary', task)
            self.assertFalse((Path(task['output_dir']) / 'recovered').exists())
            self.assertEqual(len(task['extracted_files']), 2)
            pdf = next(f for f in task['extracted_files'] if f['size'])
            self.assertEqual(pdf['original_name'], 'sample.pdf')
            self.assertNotIn('recovered_path', pdf)
            self.assertTrue(pdf['path'].endswith('.dat'))
        asyncio.run(run())


if __name__ == '__main__':
    unittest.main()
