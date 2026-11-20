"""
Volatility Subprocess Execution Engine
Handles Volatility 2 and Volatility 3 execution with real-time streaming,
structured output parsing, process cancellation, and artifact management.
"""

import os
import sys
import json
import csv
import io
import re
import time
import asyncio
import subprocess
import psutil
import shutil
import shlex
from pathlib import Path
from typing import Dict, List, Any, Optional

# Active tasks store
# task_id -> TaskInfo
tasks_store: Dict[str, Dict[str, Any]] = {}

def sanitize_line(line: str) -> str:
    """Removes ANSI escape codes and progress carriage returns"""
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', line)
    return clean.replace('\r', '\n')


def parse_tabular_output(raw_text: str) -> Dict[str, Any]:
    """
    Parses standard Volatility 2 & 3 text/table output into structured columns and rows.
    """
    # Parse the original CSV stream so quoted newlines and empty cells survive.
    csv_start = re.search(r'(?m)^TreeDepth,.*$', raw_text)
    if csv_start:
        reader = csv.reader(io.StringIO(raw_text[csv_start.start():]), escapechar='\\')
        header = next(reader)
        return {'columns': header, 'rows': [row for row in reader if len(row) == len(header)]}
    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
    if not lines:
        return {"columns": [], "rows": []}

    # Filter out Volatility progress/banner lines
    content_lines = []
    for l in lines:
        if l.startswith("Volatility 3 Framework") or l.startswith("Volatility Foundation"):
            continue
        if l.startswith("Progress:") or "PDB scanning finished" in l or "Reconstruction finished" in l:
            continue
        content_lines.append(l)

    if not content_lines:
        return {"columns": [], "rows": []}

    key_values = [re.match(r'^\s*([^:\n]+?)\s+:\s*(.*)$', line) for line in content_lines]
    if key_values and key_values[0]:
        return {'columns': ['Field', 'Value'], 'rows': [[m.group(1).strip(), m.group(2)] for m in key_values if m]}

    # Case 1: CSV format
    first_line = content_lines[0]
    if "," in first_line and len(content_lines) > 1:
        try:
            reader = csv.reader(content_lines)
            header = next(reader, None)
            if header and len(header) > 1:
                rows = []
                for r in reader:
                    if r and len(r) == len(header):
                        rows.append(r)
                if rows:
                    return {"columns": [c.strip() for c in header], "rows": rows}
        except Exception:
            pass

    # Case 2: Volatility 2 & 3 Tabular text
    header_idx = -1
    for idx, l in enumerate(content_lines[:15]):
        tokens = [t.strip() for t in re.split(r'\s{2,}|\t', l) if t.strip()]
        if len(tokens) >= 2:
            keywords = ["pid", "offset", "name", "threads", "handles", "time", "proto", "local", "foreign", "state", "path", "command", "variable", "value"]
            if any(k in l.lower() for k in keywords):
                header_idx = idx
                break

    if header_idx != -1:
        header_line = content_lines[header_idx]
        columns = [t.strip() for t in re.split(r'\s{2,}|\t', header_line) if t.strip()]
        # Volatility 2 aligns fields to the dashed separator. Splitting rows on
        # whitespace corrupts adjacent numeric cells, empty values and paths.
        original = [line.rstrip() for line in raw_text.splitlines() if line.strip()]
        for index, line in enumerate(original):
            if re.fullmatch(r'[\s\-]+', line) and '-' in line and index:
                spans = list(re.finditer(r'-+', line))
                if len(spans) >= 2:
                    starts = [span.start() for span in spans]
                    def cells(value):
                        return [value[start:(starts[i + 1] if i + 1 < len(starts) else len(value))].strip()
                                for i, start in enumerate(starts)]
                    return {'columns': cells(original[index - 1]),
                            'rows': [cells(value) for value in original[index + 1:]
                                     if not value.startswith(('***', '==='))]}
        
        data_start = header_idx + 1
        if data_start < len(content_lines) and re.match(r'^[\s\-_=]+$', content_lines[data_start]):
            data_start += 1

        rows = []
        for line in content_lines[data_start:]:
            if line.startswith("***") or line.startswith("==="):
                continue
            parts = [t.strip() for t in re.split(r'\s{2,}|\t', line) if t.strip()]
            if len(parts) == len(columns):
                rows.append(parts)
            elif len(parts) > len(columns):
                merged = parts[:len(columns)-1] + [" ".join(parts[len(columns)-1:])]
                rows.append(merged)
            elif len(parts) >= 2:
                padded = parts + [""] * (len(columns) - len(parts))
                rows.append(padded)

        if columns and rows:
            return {"columns": columns, "rows": rows}

    return {"columns": [], "rows": []}


def parse_process_tree(raw_text: str) -> List[Dict[str, Any]]:
    tree_nodes = []
    lines = raw_text.splitlines()
    
    pattern_vol3 = re.compile(r'^(?P<indent>[.\s*]*)\s*(?P<pid>\d+)\s+(?P<ppid>\d+)\s+(?P<name>[\w\.\-]+)')
    pattern_vol2 = re.compile(r'^(?P<indent>[.\s*]*)\s*(?:0x[0-9a-fA-F]+:)?(?P<name>[\w\.\-]+)\s+(?P<pid>\d+)\s+(?P<ppid>\d+)')

    for line in lines:
        m3 = pattern_vol3.search(line)
        if m3:
            indent_level = len(m3.group("indent").replace(" ", ""))
            tree_nodes.append({
                "name": m3.group("name"),
                "pid": m3.group("pid"),
                "ppid": m3.group("ppid"),
                "level": indent_level,
                "raw": line.strip()
            })
            continue

        m2 = pattern_vol2.search(line)
        if m2 and "PID" not in m2.group("name"):
            indent_level = len(m2.group("indent").replace(" ", ""))
            tree_nodes.append({
                "name": m2.group("name"),
                "pid": m2.group("pid"),
                "ppid": m2.group('ppid'),
                "level": indent_level,
                "raw": line.strip()
            })

    return tree_nodes


def split_arguments(value: str) -> List[str]:
    """Keep Windows backslashes and quoted arguments intact, without a shell."""
    if os.name != 'nt':
        return shlex.split(value)
    import ctypes
    from ctypes import wintypes
    count = ctypes.c_int()
    parse = ctypes.windll.shell32.CommandLineToArgvW
    parse.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
    parse.restype = ctypes.POINTER(wintypes.LPWSTR)
    pointer = parse('program ' + value, ctypes.byref(count))
    if not pointer:
        raise ValueError('Tham số CLI không hợp lệ.')
    try:
        return [pointer[i] for i in range(1, count.value)]
    finally:
        ctypes.windll.kernel32.LocalFree(ctypes.cast(pointer, ctypes.c_void_p))


class VolatilityRunner:
    def __init__(self, workspace_dir: str):
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.config_path = os.path.join(workspace_dir, 'gui_config.json')
        self.output_dir = os.path.join(workspace_dir, 'output')
        self.vol3_cmd = shutil.which('vol.exe') or shutil.which('vol') or 'vol.exe'
        self.vol2_python = shutil.which('python2.exe') or 'python2.exe'
        self.vol2_script = os.path.join(workspace_dir, 'volatility-master', 'vol.py')
        candidates = list(Path(workspace_dir, 'bin').glob('**/volatility*standalone.exe'))
        self.vol2_custom_exe = str(candidates[0]) if candidates else ''
        self._probe_cache = {}
        if os.path.isfile(self.config_path):
            with open(self.config_path, encoding='utf-8') as handle:
                self._apply_config(json.load(handle))
        os.makedirs(self.output_dir, exist_ok=True)

    def _environment(self, engine):
        env = os.environ.copy()
        env.update(PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
        dependencies = os.path.join(self.workspace_dir, '.gui-deps')
        if engine == 'vol3' and os.path.isdir(dependencies):
            env['PYTHONPATH'] = dependencies + (os.pathsep + env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        return env

    def _probe(self, command):
        key = tuple(command)
        if key in self._probe_cache:
            return self._probe_cache[key]
        try:
            result = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=20,
                                    env=self._environment('vol3' if command[0] == self.vol3_cmd else 'vol2'))
            ok = result.returncode == 0
            error = '' if ok else (result.stderr or result.stdout or f'Exit code {result.returncode}')[-1500:]
        except Exception as exc:
            ok, error = False, str(exc)
        self._probe_cache[key] = (ok, error)
        return ok, error

    def get_config(self):
        vol3_ok, vol3_error = self._probe([self.vol3_cmd, '-h'])
        vol2_command = ([self.vol2_custom_exe, '-h'] if self.vol2_custom_exe else
                        [self.vol2_python, self.vol2_script, '-h'])
        vol2_ok, vol2_error = self._probe(vol2_command)
        return dict(vol3_command=self.vol3_cmd, vol3_ready=vol3_ok, vol3_error=vol3_error,
                    vol2_python=self.vol2_python, vol2_script=self.vol2_script,
                    vol2_custom_exe=self.vol2_custom_exe, vol2_ready=vol2_ok,
                    vol2_error=vol2_error,
                    vol2_mode=('standalone_exe' if self.vol2_custom_exe else 'python2_script') if vol2_ok else 'none',
                    output_dir=self.output_dir)

    def _apply_config(self, config):
        mapping = {'vol3_command': 'vol3_cmd', 'vol2_python': 'vol2_python',
                   'vol2_script': 'vol2_script', 'vol2_custom_exe': 'vol2_custom_exe', 'output_dir': 'output_dir'}
        for key, attr in mapping.items():
            if key in config:
                value = config[key]
                if not isinstance(value, str):
                    raise ValueError(f'{key} phải là chuỗi.')
                value = value.strip().strip('"')
                if not value and key in ('output_dir', 'vol3_command', 'vol2_python', 'vol2_script'):
                    raise ValueError(f'{key} không được để trống.')
                if key == 'output_dir':
                    value = os.path.abspath(os.path.join(self.workspace_dir, value))
                setattr(self, attr, value)

    def update_config(self, config):
        previous = {key: getattr(self, attr) for key, attr in
                    [('vol3_command', 'vol3_cmd'), ('vol2_python', 'vol2_python'),
                     ('vol2_script', 'vol2_script'), ('vol2_custom_exe', 'vol2_custom_exe'), ('output_dir', 'output_dir')]}
        try:
            self._apply_config(config)
            os.makedirs(self.output_dir, exist_ok=True)
            saved = {key: getattr(self, 'vol3_cmd' if key == 'vol3_command' else key) for key in previous}
            with open(self.config_path + '.tmp', 'w', encoding='utf-8') as handle:
                json.dump(saved, handle, ensure_ascii=False, indent=2)
            os.replace(self.config_path + '.tmp', self.config_path)
            self._probe_cache.clear()
        except Exception:
            self._apply_config(previous)
            raise

    def validate(self, engine, image_path, plugin_name=None):
        if engine not in ('vol2', 'vol3'):
            raise ValueError('Engine không hợp lệ.')
        if not image_path or not os.path.isfile(image_path):
            raise ValueError('Không tìm thấy file Memory Dump. Hãy kiểm tra đường dẫn đầy đủ.')
        if plugin_name:
            from .plugin_catalog import VOLATILITY_2_PLUGINS, VOLATILITY_3_PLUGINS
            catalog = VOLATILITY_3_PLUGINS if engine == 'vol3' else VOLATILITY_2_PLUGINS
            if plugin_name not in {p['name'] for p in catalog}:
                raise ValueError('Plugin không thuộc engine đã chọn.')
        cfg = self.get_config()
        if not cfg[engine + '_ready']:
            raise ValueError(f'{engine} chưa chạy được: ' + cfg[engine + '_error'])

    def build_command(self, engine, image_path, plugin_name, profile=None, options=None,
                      custom_args=None, output_subfolder=None):
        out_dir = output_subfolder or self.output_dir
        option_metadata = {}
        if engine == 'vol3':
            from .plugin_catalog import VOLATILITY_3_PLUGINS
            entry = next((p for p in VOLATILITY_3_PLUGINS if p['name'] == plugin_name), {})
            option_metadata = {opt['name']: opt for opt in entry.get('options', [])}
            # -f drops the UNC hostname inside Volatility's URI conversion.
            # --single-location accepts the complete URI, including WSL shares.
            image_args = (['--single-location', Path(image_path).as_uri()]
                          if image_path.startswith(('\\\\', '//')) else ['-f', image_path])
            cmd = [self.vol3_cmd, '-q', '-r', 'csv'] + image_args + ['-o', out_dir, plugin_name]
        elif engine == 'vol2':
            cmd = [self.vol2_custom_exe] if self.vol2_custom_exe else [self.vol2_python, self.vol2_script]
            if plugin_name == 'screenshot':
                cmd += ['--plugins', str(Path(__file__).with_name('vol2_plugins'))]
            cmd += ['-f', image_path]
            if profile and profile.strip():
                cmd += ['--profile=' + profile.strip()]
            cmd += ['guiscreenshot' if plugin_name == 'screenshot' else plugin_name]
        else:
            raise ValueError('Engine không hợp lệ.')
        for key, value in (options or {}).items():
            if not re.fullmatch(r'-{1,2}[\w-]+', key):
                raise ValueError('Tên tùy chọn không hợp lệ.')
            if key in ('-D', '--dump-dir') and engine == 'vol2':
                cmd += [key, str(value).strip() if isinstance(value, str) and value.strip() else out_dir]
            elif value is True:
                cmd.append(key)
            elif value is not None and value is not False and str(value).strip():
                text = str(value).strip()
                metadata = option_metadata.get(key, {})
                if metadata.get('is_list'):
                    values = re.split(r'[,\s]+', text) if metadata.get('element_type') == 'int' else split_arguments(text)
                else:
                    values = [text]
                cmd += [key] + values
        if engine == 'vol2' and plugin_name in ('dumpfiles', 'malfind', 'procdump', 'dlldump', 'memdump', 'vaddump', 'dumpregistry', 'moddump', 'screenshot', 'dumpcerts', 'evtlogs') and not any(k in cmd for k in ('-D', '--dump-dir')):
            cmd += ['-D', out_dir]
        if custom_args and custom_args.strip():
            extra = split_arguments(custom_args)
            if engine == 'vol3':
                global_flags = {'--offline', '--clear-cache', '--write-config', '-q', '--quiet', '-v', '--verbosity'}
                global_values = {'-c', '--config', '-e', '--extend', '-p', '--plugin-dirs', '-s', '--symbol-dirs',
                                 '-l', '--log', '--cache-path', '-u', '--remote-isf-url', '--filters', '--save-config',
                                 '-r', '--renderer', '-o', '--output-dir'}
                before, after = [], []
                index = 0
                while index < len(extra):
                    token = extra[index]
                    key = token.split('=', 1)[0]
                    if key in global_flags or key in global_values:
                        before.append(token)
                        if key in global_values and '=' not in token:
                            index += 1
                            if index >= len(extra):
                                raise ValueError('Thiếu giá trị cho ' + key)
                            before.append(extra[index])
                    else:
                        after.append(token)
                    index += 1
                position = cmd.index(plugin_name)
                cmd[position:position] = before
                cmd += after
            else:
                cmd += extra
        return cmd

    def create_task(self, task_id, engine, image_path, plugin_name, profile=None, options=None, custom_args=None):
        directory = os.path.join(self.output_dir, f"run_{task_id}_{plugin_name.replace('.', '_')}")
        cmd = self.build_command(engine, image_path, plugin_name, profile, options, custom_args, directory)
        task = dict(id=task_id, engine=engine, plugin=plugin_name, image_path=image_path,
                    profile=profile, command=subprocess.list2cmdline(cmd), command_list=cmd,
                    output_dir=directory, status='QUEUED', start_time=time.time(), end_time=None,
                    duration=None, return_code=None, raw_logs=[], table_data={'columns': [], 'rows': []},
                    tree_data=[], extracted_files=[], process=None)
        tasks_store[task_id] = task
        return task

    async def run_task(self, task_id, engine, image_path, plugin_name, profile=None, options=None, custom_args=None):
        task = tasks_store.get(task_id) or self.create_task(task_id, engine, image_path, plugin_name, profile, options, custom_args)
        if task['status'] == 'KILLED':
            return
        task['status'] = 'RUNNING'
        stdout = bytearray()
        direct_json = plugin_name in ('memmap', 'windows.memmap')
        json_stream = None
        try:
            os.makedirs(task['output_dir'], exist_ok=True)
            if direct_json:
                json_stream = open(os.path.join(task['output_dir'], 'memmap.output.partial'), 'wb')
                task['raw_logs'].append('[*] Memmap đang xuất trực tiếp ra JSON; không tải bảng kết quả vào GUI.')
            env = self._environment(engine)
            proc = await asyncio.create_subprocess_exec(*task['command_list'], cwd=self.workspace_dir,
                    stdout=json_stream if direct_json else asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, env=env)
            task['process'] = proc
            if task['status'] == 'KILLED':
                self._kill_process(proc)

            async def read_stream(stream, capture=False):
                import codecs
                decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
                pending = ''
                while True:
                    chunk = await stream.read(65536)
                    if capture:
                        stdout.extend(chunk)
                    pending += decoder.decode(chunk, final=not chunk)
                    parts = sanitize_line(pending).split('\n')
                    pending = parts.pop()
                    task['raw_logs'].extend(line for line in parts if line.strip() and not line.startswith('GUI_SCREENSHOT '))
                    if not chunk:
                        if pending.strip():
                            task['raw_logs'].append(pending)
                        break

            if direct_json:
                await read_stream(proc.stderr)
            else:
                await asyncio.gather(read_stream(proc.stdout, True), read_stream(proc.stderr))
            task['return_code'] = await proc.wait()
            if direct_json:
                json_stream.close()
                if proc.returncode == 0 and task['status'] != 'KILLED':
                    await asyncio.to_thread(self.finalize_memmap_json, task)
            raw = stdout.decode('utf-8', errors='replace')
            if engine == 'vol2' and plugin_name == 'screenshot' and proc.returncode == 0 and task['status'] != 'KILLED':
                from .screenshot_renderer import render_screenshots
                images = await asyncio.to_thread(render_screenshots, raw)
                task['raw_logs'].extend('Wrote ' + str(path) for path in images)
                raw = '\n'.join('Wrote ' + str(path) for path in images)
            if not direct_json:
                task['table_data'] = await asyncio.to_thread(parse_tabular_output, raw)
            if 'pstree' in plugin_name.lower():
                table = task['table_data']
                cols = table['columns']
                if all(key in cols for key in ('PID', 'PPID', 'ImageFileName')):
                    task['tree_data'] = [dict(pid=row[cols.index('PID')], ppid=row[cols.index('PPID')],
                         name=row[cols.index('ImageFileName')],
                         level=int(row[cols.index('TreeDepth')]) if 'TreeDepth' in cols else 0) for row in table['rows']]
                else:
                    task['tree_data'] = parse_process_tree(raw)
            for path in Path(task['output_dir']).rglob('*'):
                if path.name.endswith('.partial'):
                    continue
                if 'recovered' in path.relative_to(task['output_dir']).parts:
                    continue
                if path.is_file():
                    entry = dict(name=str(path.relative_to(task['output_dir'])), path=str(path), size=path.stat().st_size)
                    if engine == 'vol3' and plugin_name == 'windows.dumpfiles':
                        from .artifact_manager import describe_dump_name
                        entry.update(describe_dump_name(path.name, entry['size']))
                    task['extracted_files'].append(entry)
            if task['status'] != 'KILLED':
                task['status'] = 'SUCCESS' if proc.returncode == 0 else 'FAILED'
        except asyncio.CancelledError:
            if task.get('process'):
                self._kill_process(task['process'])
                await task['process'].wait()
            task['status'] = 'CANCELLED'
            raise
        except Exception as exc:
            task['status'] = 'ERROR' if task['status'] != 'KILLED' else 'KILLED'
            task['raw_logs'].append('[LỖI] ' + str(exc))
        finally:
            if json_stream is not None and not json_stream.closed:
                json_stream.close()
            task['end_time'] = time.time()
            task['duration'] = round(task['end_time'] - task['start_time'], 2)
            task['process'] = None

    @staticmethod
    def finalize_memmap_json(task):
        source = Path(task['output_dir']) / 'memmap.output.partial'
        partial = source.with_name('memmap.json.partial')
        count = 0
        with source.open(encoding='utf-8-sig', errors='replace', newline='') as handle, partial.open('w', encoding='utf-8') as output:
            output.write('[\n')
            if task['engine'] == 'vol3':
                reader = csv.DictReader(handle, escapechar='\\')
                if not reader.fieldnames or 'Virtual' not in reader.fieldnames:
                    raise ValueError('Không nhận diện được đầu ra memmap để xuất JSON.')
                records = reader
            else:
                def vol2_records():
                    process_name, pid = '', None
                    for line in handle:
                        proc = re.match(r'^(.*?)\s+pid:\s*(\d+)\s*$', line.strip())
                        if proc:
                            process_name, pid = proc[1], int(proc[2])
                            continue
                        row = re.match(r'^\s*(0x[\da-f]+)\s+(0x[\da-f]+)\s+(0x[\da-f]+)\s+(0x[\da-f]+)\s*$', line, re.I)
                        if row and pid is not None:
                            yield dict(Process=process_name, PID=pid, Virtual=row[1], Physical=row[2], Size=row[3], DumpFileOffset=row[4])
                records = vol2_records()
            for record in records:
                if count:
                    output.write(',\n')
                json.dump(record, output, ensure_ascii=False)
                count += 1
            output.write('\n]\n')
        target = partial.with_name('memmap.json')
        os.replace(partial, target)
        source.unlink()  # Only the intermediate stream created by this task.
        task['json_export'] = dict(name='memmap.json', path=str(target), rows_count=count, size=target.stat().st_size)
        task['raw_logs'].append(f'[*] Đã lưu memmap.json: {count} dòng. Có thể tải JSON hoặc mở thư mục kết quả.')

    @staticmethod
    def prepare_legacy_memmap_export(task):
        """Export existing in-memory results without returning them to the UI."""
        if task.get('json_export') or task.get('status') != 'SUCCESS':
            return
        table = task.get('table_data', {})
        if not table.get('columns'):
            return
        target = Path(task['output_dir']) / 'memmap.json'
        partial = target.with_name('memmap.json.partial')
        target.parent.mkdir(parents=True, exist_ok=True)
        with partial.open('w', encoding='utf-8') as handle:
            handle.write('[')
            for index, row in enumerate(table.get('rows', [])):
                if index:
                    handle.write(',\n')
                json.dump(dict(zip(table['columns'], row)), handle, ensure_ascii=False)
            handle.write(']\n')
        os.replace(partial, target)
        task['json_export'] = dict(name='memmap.json', path=str(target), rows_count=len(table.get('rows', [])), size=target.stat().st_size)

    @staticmethod
    def _kill_process(proc):
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            parent.kill()
        except psutil.NoSuchProcess:
            pass

    def kill_task(self, task_id):
        task = tasks_store.get(task_id)
        if not task or task['status'] not in ('QUEUED', 'RUNNING'):
            return False
        if task.get('process'):
            self._kill_process(task['process'])
        task['status'] = 'KILLED'
        task['raw_logs'].append('[!] Tiến trình đã được dừng.')
        task['end_time'] = time.time()
        task['duration'] = round(task['end_time'] - task['start_time'], 2)
        return True


