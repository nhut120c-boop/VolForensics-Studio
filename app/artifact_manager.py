"""Make readable copies of Volatility cache dumps without changing evidence."""
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

_DUMP_NAME = re.compile(
    r'^file\.(0x[0-9a-f]+)\.(0x[0-9a-f]+)\.'
    r'(ImageSectionObject|DataSectionObject|SharedCacheMap)\.(.+)\.(img|dat|vacb)$', re.I)


def describe_dump_name(filename, size):
    """Describe the wrapper name without opening or copying file contents."""
    match = _DUMP_NAME.match(filename)
    if not match:
        return {}
    return dict(original_name=match[4], cache_type=match[3],
                warning='0 byte: không lấy được dữ liệu từ cache.' if size == 0 else '')


def _digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_name(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).rstrip(' .') or 'unnamed'
    if value.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}:
        value = '_' + value
    # Keep the final extension while bounding names from damaged FILE_OBJECTs.
    if len(value) > 100:
        suffix = Path(value).suffix[:16]
        value = value[:100 - len(suffix)] + suffix
    return value


def _file_type(path):
    with path.open('rb') as handle:
        header = handle.read(4096)
        if header.startswith(b'MZ') and len(header) >= 64:
            offset = int.from_bytes(header[60:64], 'little')
            if offset <= path.stat().st_size - 4:
                handle.seek(offset)
                if handle.read(4) == b'PE\0\0':
                    return 'PE (EXE/DLL)', ''
            return 'MZ', 'Có MZ nhưng chưa đọc được PE header; có thể thiếu trang nhớ.'
    signatures = [(b'%PDF-', 'PDF'), (b'\x89PNG\r\n\x1a\n', 'PNG'), (b'\xff\xd8\xff', 'JPEG'),
                  (b'PK\x03\x04', 'ZIP / Office Open XML'), (b'regf', 'Registry hive'),
                  (b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1', 'OLE / Office'),
                  (b'7z\xbc\xaf\x27\x1c', '7-Zip'), (b'Rar!\x1a\x07', 'RAR')]
    for magic, label in signatures:
        if header.startswith(magic):
            return label, ''
    if header and not any(header):
        return 'Chưa xác định', 'Header toàn byte 0; có thể thiếu các trang đầu của file.'
    return 'Chưa xác định', 'Chưa xác nhận định dạng hoặc độ đầy đủ từ header.'


def recover_dump_names(directory):
    """Copy nonempty Vol3 dumpfiles outputs, preserving each cache variant.

    A name or recognizable header is not a guarantee of complete file recovery.
    Originals are never renamed, overwritten, deleted, or executed.
    """
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError('Không tìm thấy thư mục trích xuất.')
    candidates = [(path, _DUMP_NAME.match(path.name)) for path in root.iterdir() if path.is_file() and not path.is_symlink()]
    candidates = [(path, match) for path, match in candidates if match]
    destination_root = root / 'recovered'
    needed = sum(path.stat().st_size for path, match in candidates
                 if not (destination_root / match[3] / f'{match[1]}_{match[2]}__{_safe_name(match[4])}').exists())
    if needed + 64 * 1024 * 1024 > shutil.disk_usage(root).free:
        raise OSError('Không đủ dung lượng để tạo bản sao giữ tên gốc. Bản dump ban đầu được giữ nguyên.')
    records = []
    for path, match in candidates:
        size = path.stat().st_size
        record = dict(source_name=path.name, original_name=match[4], cache_type=match[3], size=size,
                      recovered_path=None, recovered_name=None, file_type='', warning='', sha256=None)
        if not size:
            record.update(file_type='File rỗng', warning='0 byte: không lấy được dữ liệu từ cache; không có bản sao để mở.')
            records.append(record)
            continue
        try:
            record['file_type'], record['warning'] = _file_type(path)
            record['sha256'] = _digest(path)
            folder = destination_root / match[3]
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / f'{match[1]}_{match[2]}__{_safe_name(match[4])}'
            if target.exists() and _digest(target) != record['sha256']:
                raise FileExistsError(f'Bản sao đã có nhưng khác nội dung: {target.name}. Không ghi đè.')
            if not target.exists():
                # Exclusive creation and verification keep repeated recovery safe.
                with path.open('rb') as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output, 1024 * 1024)
                if _digest(target) != record['sha256']:
                    raise OSError(f'Bản sao không khớp SHA-256: {target.name}')
            record.update(recovered_path=str(target), recovered_name=target.name)
        except OSError as exc:
            record['warning'] = 'Không đọc/sao chép được tệp: ' + str(exc)
        records.append(record)
    if candidates:
        destination_root.mkdir(exist_ok=True)
        manifest = destination_root / 'manifest.json'
        temporary = destination_root / 'manifest.json.tmp'
        with temporary.open('w', encoding='utf-8') as handle:
            json.dump(dict(note='Bản sao giữ nguyên nội dung. Tên gốc/header không xác nhận file đầy đủ.', files=records), handle, ensure_ascii=False, indent=2)
        os.replace(temporary, manifest)
    return dict(files=records, copied_count=sum(bool(r['recovered_path']) for r in records),
                empty_count=sum(r['size'] == 0 for r in records),
                error_count=sum(r['size'] > 0 and not r['recovered_path'] for r in records), output_dir=str(destination_root))
