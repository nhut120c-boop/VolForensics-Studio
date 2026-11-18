"""
Volatility 2 & 3 Plugin Catalog - Bản địa hóa Tiếng Việt
"""

VOLATILITY_3_PLUGINS = [
    # Thông tin hệ thống (Tương đương imageinfo)
    {
        "name": "windows.info",
        "category": "Hệ thống",
        "os": "windows",
        "desc": "Nhận diện thông tin hệ điều hành: kiến trúc 32/64-bit, Kernel Base, DTB, Windows Build, Service Pack, múi giờ...",
        "options": []
    },
    # Tiến trình & Bộ nhớ
    {
        "name": "windows.memmap",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Xuất ánh xạ bộ nhớ ảo/vật lý trực tiếp ra JSON, không hiện bảng trên GUI. Bật Dump để trích xuất thêm bộ nhớ ra file .dmp.",
        "options": [
            {"name": "--pid", "label": "PID tiến trình (một PID)", "type": "text", "placeholder": "Ví dụ: 2096"},
            {"name": "--dump", "label": "Trích xuất bộ nhớ tiến trình", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.pstree",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Hiển thị cây phân cấp quan hệ tiến trình Cha - Con (PPID  -  PID). Dễ dàng phát hiện các tiến trình con lạ hoặc bị spawn bất thường.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text", "placeholder": "Ví dụ: 1024", "help": "PID của tiến trình cần kiểm tra"}
        ]
    },
    {
        "name": "windows.pslist",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Liệt kê các tiến trình đang hoạt động bằng cách duyệt danh sách liên kết kép ActiveProcessLinks (PID, PPID, Threads, Handles, Thời gian tạo).",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text", "placeholder": "Ví dụ: 1024, 2048"},
            {"name": "--dump", "label": "Trích xuất file EXE (Dump)", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.psscan",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Quét vùng nhớ pool để tìm các cấu trúc tiến trình bị rootkit ngắt liên kết (unlinked) hoặc tiến trình ẩn đã bị kết thúc.",
        "options": [
            {"name": "--dump", "label": "Trích xuất tiến trình ẩn", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.cmdline",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Khôi phục toàn bộ tham số và câu lệnh thực thi (Command-line Arguments) của tiến trình khi khởi chạy.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text", "placeholder": "Ví dụ: 1234"}
        ]
    },
    {
        "name": "windows.dlllist",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Liệt kê danh sách các thư viện liên kết động (DLL) được nạp vào không gian bộ nhớ của từng tiến trình.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text", "placeholder": "Ví dụ: 1024"},
            {"name": "--dump", "label": "Trích xuất các file DLL", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.handles",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Liệt kê các tay cầm đối tượng (Handles) đang mở: File, Khóa Registry, Mutex, Event, Thread.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text", "placeholder": "Ví dụ: 1024"}
        ]
    },
    {
        "name": "windows.envars",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Hiển thị các biến môi trường của tiến trình (Đường dẫn TEMP, USERNAME, COMPUTERNAME...).",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"}
        ]
    },
    {
        "name": "windows.privileges",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Kiểm tra đặc quyền token tiến trình (SeDebugPrivilege, SeImpersonatePrivilege, enabled/disabled).",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"}
        ]
    },
    {
        "name": "windows.sessions",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Phân loại các tiến trình theo phiên đăng nhập (Console, RDP, Services, System).",
        "options": []
    },
    {
        "name": "windows.threads",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Liệt kê các luồng (Threads) thực thi của tiến trình kèm địa chỉ bắt đầu và trạng thái.",
        "options": []
    },

    # Mã độc & Chèn mã (Malware)
    {
        "name": "windows.malfind",
        "category": "Mã độc",
        "os": "windows",
        "desc": "Quét bộ nhớ phát hiện mã chèn ẩn (Injected Code, DLL Injection, vùng nhớ PAGE_EXECUTE_READWRITE không gắn file).",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"},
            {"name": "--dump", "label": "Trích xuất vùng nhớ nghi ngờ", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.hollowprocesses",
        "category": "Mã độc",
        "os": "windows",
        "desc": "Phát hiện kỹ thuật Process Hollowing / Doppelgänging (phần header thực thi trong RAM khác với file gốc).",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"}
        ]
    },
    {
        "name": "windows.ldrmodules",
        "category": "Mã độc",
        "os": "windows",
        "desc": "Phát hiện DLL bị ẩn bằng cách so sánh 3 danh sách nạp PEB với danh sách vùng nhớ VAD.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"}
        ]
    },
    {
        "name": "windows.mutantscan",
        "category": "Mã độc",
        "os": "windows",
        "desc": "Quét bộ nhớ tìm kiếm Mutex/Mutant (các mã độc thường tạo Mutex để đảm bảo chỉ chạy 1 phiên bản).",
        "options": []
    },

    # Mạng (Network)
    {
        "name": "windows.netscan",
        "category": "Mạng",
        "os": "windows",
        "desc": "Quét bộ nhớ tìm kết nối mạng TCP/UDP (kết nối trực tiếp, cổng đang lắng nghe, IPv4/IPv6, ánh xạ PID).",
        "options": []
    },
    {
        "name": "windows.netstat",
        "category": "Mạng",
        "os": "windows",
        "desc": "Duyệt qua các cấu trúc mạng đang hoạt động để liệt kê kết nối hiện hữu.",
        "options": []
    },

    # Registry & Mật khẩu
    {
        "name": "windows.registry.hivelist",
        "category": "Registry",
        "os": "windows",
        "desc": "Liệt kê danh sách các Hive Registry đã nạp (SYSTEM, SAM, SOFTWARE, NTUSER.DAT) kèm địa chỉ Virtual Offset.",
        "options": [
            {"name": "--dump", "label": "Trích xuất các Hive ra ổ đĩa", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.registry.printkey",
        "category": "Registry",
        "os": "windows",
        "desc": "Xem các khóa và giá trị con trong Registry (ví dụ khóa Persistence Run, RunOnce).",
        "options": [
            {"name": "--key", "label": "Đường dẫn khóa", "type": "text", "placeholder": "Microsoft\\Windows\\CurrentVersion\\Run"},
            {"name": "--offset", "label": "Địa chỉ Hive Offset (tùy chọn)", "type": "text"}
        ]
    },
    {
        "name": "windows.registry.userassist",
        "category": "Registry",
        "os": "windows",
        "desc": "Giải mã khóa UserAssist để biết ứng dụng nào người dùng đã khởi chạy, số lần chạy và thời gian chạy cuối.",
        "options": []
    },
    {
        "name": "windows.registry.hashdump",
        "category": "Mật khẩu",
        "os": "windows",
        "desc": "Trích xuất Hash mật khẩu người dùng Windows (NTLM / LM) từ SAM hive trong bộ nhớ.",
        "options": []
    },
    {
        "name": "windows.registry.lsadump",
        "category": "Mật khẩu",
        "os": "windows",
        "desc": "Trích xuất LSA Secrets (mật khẩu tài khoản service, thông tin xác thực domain lưu trong RAM).",
        "options": []
    },

    # File & Trích xuất
    {
        "name": "windows.filescan",
        "category": "File & Dữ liệu",
        "os": "windows",
        "desc": "Quét bộ nhớ vật lý tìm các cấu trúc FILE_OBJECT (tìm đường dẫn file đang mở hoặc file đệm kèm địa chỉ offset).",
        "options": []
    },
    {
        "name": "windows.dumpfiles",
        "category": "File & Dữ liệu",
        "os": "windows",
        "desc": "Trích xuất các file được cache trong bộ nhớ (EXE, tài liệu, logs) ra thư mục chỉ định.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"},
            {"name": "--virtaddr", "label": "Địa chỉ ảo (từ filescan)", "type": "text"}
        ]
    },
    {
        "name": "windows.pedump",
        "category": "File & Dữ liệu",
        "os": "windows",
        "desc": "Khôi phục và trích xuất file thực thi nhị phân từ không gian bộ nhớ của tiến trình.",
        "options": [
            {"name": "--pid", "label": "Lọc theo PID", "type": "text"},
            {"name": "--base", "label": "Địa chỉ PE Base (bắt buộc)", "type": "text", "required": True, "placeholder": "0x140000000"},
            {"name": "--kernel-module", "label": "Trích xuất mô-đun kernel", "type": "boolean", "default": False}
        ]
    },

    # Kernel & Drivers
    {
        "name": "windows.modules",
        "category": "Kernel & Driver",
        "os": "windows",
        "desc": "Liệt kê các mô-đun kernel và driver đã nạp qua PsLoadedModuleList.",
        "options": [
            {"name": "--dump", "label": "Trích xuất các Driver", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.modscan",
        "category": "Kernel & Driver",
        "os": "windows",
        "desc": "Quét bộ nhớ tìm kiếm các driver bị rootkit ẩn hoặc hủy liên kết.",
        "options": [
            {"name": "--dump", "label": "Trích xuất Driver", "type": "boolean", "default": False}
        ]
    },
    {
        "name": "windows.svcscan",
        "category": "Kernel & Driver",
        "os": "windows",
        "desc": "Quét bộ nhớ tìm danh sách các Windows Services, đường dẫn file nhị phân và trạng thái.",
        "options": []
    },
    {
        "name": "windows.ssdt",
        "category": "Kernel & Driver",
        "os": "windows",
        "desc": "Liệt kê bảng System Service Descriptor Table (SSDT) để phát hiện hook kernel.",
        "options": []
    }
]

VOLATILITY_2_PLUGINS = [
    {
        "name": "imageinfo",
        "category": "Hệ thống",
        "os": "windows",
        "desc": "Xác định gợi ý profile hệ điều hành, địa chỉ KDBG, số CPU và múi giờ.",
        "options": []
    },
    {
        "name": "kdbgscan",
        "category": "Hệ thống",
        "os": "windows",
        "desc": "Quét chữ ký KDBG chuyên sâu khi imageinfo trả về nhiều profile nghi vấn.",
        "options": []
    },
    {
        "name": "pslist",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Liệt kê danh sách tiến trình đang chạy.",
        "options": [
            {"name": "-p", "label": "Lọc theo PID", "type": "text"}
        ]
    },
    {
        "name": "pstree",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Hiển thị cây phân cấp tiến trình cha/con.",
        "options": []
    },
    {
        "name": "cmdline",
        "category": "Tiến trình",
        "os": "windows",
        "desc": "Xem tham số thực thi dòng lệnh của tiến trình.",
        "options": [
            {"name": "-p", "label": "Lọc theo PID", "type": "text"}
        ]
    },
    {
        "name": "netscan",
        "category": "Mạng",
        "os": "windows",
        "desc": "Quét kết nối mạng TCP/UDP (Windows Vista trở lên).",
        "options": []
    },
    {
        "name": "malfind",
        "category": "Mã độc",
        "os": "windows",
        "desc": "Tìm kiếm mã chèn độc hại trong vùng nhớ ảo.",
        "options": [
            {"name": "-p", "label": "Lọc theo PID", "type": "text"},
            {"name": "-D", "label": "Thư mục trích xuất", "type": "text"}
        ]
    },
    {
        "name": "hashdump",
        "category": "Mật khẩu",
        "os": "windows",
        "desc": "Trích xuất hash NTLM từ SAM/SYSTEM hive.",
        "options": [
            {"name": "-y", "label": "SYSTEM Hive Offset", "type": "text"},
            {"name": "-s", "label": "SAM Hive Offset", "type": "text"}
        ]
    },
    {
        "name": "filescan",
        "category": "File & Dữ liệu",
        "os": "windows",
        "desc": "Quét tìm các đối tượng file trong bộ nhớ vật lý.",
        "options": []
    },
    {
        "name": "dumpfiles",
        "category": "File & Dữ liệu",
        "os": "windows",
        "desc": "Trích xuất file từ cache bộ nhớ.",
        "options": [
            {"name": "-p", "label": "Lọc theo PID", "type": "text"},
            {"name": "-Q", "label": "Địa chỉ vật lý (-Q)", "type": "text"},
            {"name": "-D", "label": "Thư mục lưu file", "type": "text"}
        ]
    }
]

def _expand_vol3_catalog():
    import json
    from pathlib import Path
    entries = json.loads(Path(__file__).with_name('vol3_catalog.json').read_text(encoding='utf-8'))
    labels = {
        '--pid': 'PID tiến trình', '--dump': 'Trích xuất dữ liệu (Dump)', '--key': 'Đường dẫn khóa Registry',
        '--offset': 'Địa chỉ Offset', '--address': 'Địa chỉ cần kiểm tra', '--base': 'Địa chỉ Base',
        '--virtaddr': 'Địa chỉ ảo', '--physaddr': 'Địa chỉ vật lý', '--maxsize': 'Kích thước tối đa (byte)',
        '--max-history': 'Số lệnh trong history', '--max-buffers': 'Số history buffer',
        '--no-registry': 'Không lấy cấu hình từ Registry', '--yara-rules': 'YARA rule / chuỗi tìm kiếm',
        '--yara-file': 'Đường dẫn file YARA', '--insensitive': 'Không phân biệt hoa thường',
        '--regex': 'Biểu thức chính quy', '--pattern': 'Mẫu tìm kiếm', '--physical': 'Dùng địa chỉ vật lý',
        '--physical-offsets': 'Hiển thị offset vật lý', '--include-corrupt': 'Bao gồm bản ghi lỗi',
        '--kernel-module': 'Trích xuất module kernel', '--recurse': 'Duyệt đệ quy',
    }
    translated = {
        'cmdscan': 'Khôi phục lịch sử lệnh CMD từ các cấu trúc command history trong RAM.',
        'consoles': 'Khôi phục nội dung console, lịch sử lệnh và các buffer của cửa sổ CMD.',
        'vadinfo': 'Phân tích vùng nhớ VAD: địa chỉ, quyền truy cập và file ánh xạ; hỗ trợ dump.',
        'vadwalk': 'Duyệt cây vùng nhớ VAD của các tiến trình.',
        'vadregexscan': 'Tìm mẫu biểu thức chính quy trong các vùng nhớ VAD.',
        'vadyarascan': 'Quét các vùng nhớ tiến trình bằng YARA.',
        'psxview': 'Đối chiếu nhiều cách liệt kê để phát hiện tiến trình bị ẩn.',
        'cachedump': 'Trích xuất thông tin xác thực domain được cache trong Registry.',
        'hivescan': 'Quét bộ nhớ tìm hive Registry.',
        'amcache': 'Phân tích dấu vết ứng dụng đã chạy từ AmCache.',
        'scheduled_tasks': 'Phân tích tác vụ theo lịch, trigger và lệnh thực thi từ Registry.',
        'callbacks': 'Liệt kê các callback kernel để phát hiện đăng ký bất thường.',
        'driverscan': 'Quét tìm các cấu trúc driver trong bộ nhớ.',
        'driverirp': 'Liệt kê bảng hàm IRP của driver, hỗ trợ phát hiện hook.',
        'unloadedmodules': 'Liệt kê module kernel và driver đã được gỡ khỏi bộ nhớ.',
        'svcList': 'Liệt kê Windows Services từ cấu trúc quản lý dịch vụ.',
        'symlinkscan': 'Quét tìm các symbolic link trong bộ nhớ.',
        'mftscan': 'Quét bản ghi MFT để tìm dấu vết file và thư mục.',
        'strings': 'Ánh xạ kết quả strings về tiến trình và địa chỉ bộ nhớ.',
    }

    def category(name):
        lower = name.lower()
        if any(key in lower for key in ('hashdump', 'lsadump', 'cachedump', 'skeleton_key')):
            return 'Mật khẩu'
        if '.registry.' in lower:
            return 'Registry'
        if any(key in lower for key in ('cmdscan', 'consoles', 'cmdline', 'envars')):
            return 'Dòng lệnh & Môi trường'
        if '.malware.' in lower or any(key in lower for key in ('malfind', 'hollowprocesses', 'ldrmodules', 'psxview', 'yarascan', 'ghosting', 'masquerade')):
            return 'Mã độc'
        if any(key in lower for key in ('netscan', 'netstat')):
            return 'Mạng'
        if any(key in lower for key in ('dump', 'filescan', 'mftscan', 'strings', 'verinfo', 'memmap')):
            return 'File & Dữ liệu'
        if any(key in lower for key in ('pslist', 'psscan', 'pstree', 'dlllist', 'handles', 'envars', 'privileges', 'threads', 'sessions', 'vad')):
            return 'Tiến trình'
        if any(key in lower for key in ('driver', 'modules', 'modscan', 'ssdt', 'callbacks', 'timers', 'svc', 'symlink', 'mutant', 'pool')):
            return 'Kernel & Driver'
        return 'Hệ thống'

    def options(entry, previous=()):
        previous = {opt['name']: opt for opt in previous}
        result = []
        for source in entry['options']:
            option = source.copy()
            option['label'] = previous.get(option['name'], {}).get('label', labels.get(option['name'], option['label']))
            if option.get('required') and '(bắt buộc)' not in option['label']:
                option['label'] += ' (bắt buộc)'
            if option.get('is_list'):
                option['label'] += ' — có thể nhập nhiều giá trị'
            result.append(option)
        return result

    covered = set()
    for plugin in VOLATILITY_3_PLUGINS:
        matches = [entry for entry in entries if entry['name'].startswith(plugin['name'] + '.')]
        if len(matches) != 1:
            continue
        entry = matches[0]
        covered.add(entry['name'])
        if entry['deprecated']:
            current = [item for item in entries if not item['deprecated'] and item['class_name'] == entry['class_name']]
            if len(current) == 1:
                covered.add(current[0]['name'])
        plugin['options'] = options(entry, plugin.get('options', []))
        plugin['category'] = category(entry['name'])
    for entry in entries:
        if entry['deprecated'] or entry['name'] in covered:
            continue
        module = entry['name'].split('.')[-2]
        VOLATILITY_3_PLUGINS.append(dict(name=entry['name'], category=category(entry['name']), os='windows',
            desc=translated.get(module, entry['desc']), options=options(entry)))


_expand_vol3_catalog()


def _expand_vol2_catalog():
    """Expose the standalone's analysis plugins, with forms for common tasks."""
    import json
    from pathlib import Path

    def text(name, label, placeholder=''):
        return dict(name=name, label=label, type='text', placeholder=placeholder)

    def flag(name, label):
        return dict(name=name, label=label, type='boolean', default=False)

    pid = text('-p', 'Lọc theo PID', 'Ví dụ: 2096 hoặc 4,2096')
    dump = text('-D', 'Thư mục trích xuất (để trống: thư mục của lần chạy)')
    history = text('-M', 'Số lệnh tối đa trong history', 'Mặc định: 50')
    forms = {
        'cmdscan': [history],
        'consoles': [history, text('-B', 'Số history buffer', 'Mặc định: 4')],
        'envars': [pid, flag('--silent', 'Ẩn các biến môi trường thông thường')],
        'dlllist': [pid], 'handles': [pid, text('-t', 'Loại đối tượng', 'File, Key, Mutant…'), flag('--silent', 'Chỉ hiện đối tượng có tên')],
        'getsids': [pid], 'privs': [pid], 'memmap': [pid], 'vadinfo': [pid],
        'vadtree': [pid], 'vadwalk': [pid], 'ldrmodules': [pid],
        'procdump': [pid, dump], 'dlldump': [pid, text('-b', 'Địa chỉ DLL Base'), dump],
        'memdump': [pid, dump], 'vaddump': [pid, dump], 'dumpregistry': [dump],
        'moddump': [text('-b', 'Địa chỉ module Base'), dump], 'screenshot': [dump],
        'printkey': [text('-K', 'Đường dẫn khóa Registry', r'Software\Microsoft\Windows\CurrentVersion\Run'), text('-o', 'Hive offset (tùy chọn)')],
        'hivedump': [text('-o', 'Hive offset (bắt buộc)')],
        'lsadump': [text('-y', 'SYSTEM Hive Offset'), text('-s', 'SECURITY Hive Offset')],
        'cachedump': [text('-y', 'SYSTEM Hive Offset'), text('-s', 'SECURITY Hive Offset')],
        'yarascan': [pid, text('-Y', 'YARA rule / chuỗi tìm kiếm'), text('-y', 'Đường dẫn file YARA rules')],
        'strings': [text('-s', 'Đường dẫn file kết quả strings (bắt buộc)')],
    }
    descriptions = {
        'cmdscan': 'Khôi phục lịch sử lệnh CMD bằng cách quét _COMMAND_HISTORY, kể cả lệnh cũ còn trong RAM.',
        'consoles': 'Khôi phục console CMD: lịch sử lệnh, nội dung màn hình, tiến trình gắn với cửa sổ console.',
        'envars': 'Xem biến môi trường (environment variables): USERNAME, PATH, TEMP, COMPUTERNAME… theo tiến trình.',
        'dlllist': 'Liệt kê DLL được nạp trong từng tiến trình.',
        'handles': 'Liệt kê các handle: file, khóa Registry, mutex và đối tượng đang mở.',
        'getsids': 'Xem SID của người dùng và nhóm sở hữu tiến trình.',
        'privs': 'Kiểm tra các đặc quyền token của tiến trình.',
        'psscan': 'Quét tìm tiến trình ẩn hoặc đã kết thúc trong bộ nhớ pool.',
        'psxview': 'Đối chiếu nhiều cách liệt kê tiến trình để phát hiện tiến trình bị ẩn.',
        'ldrmodules': 'Đối chiếu danh sách DLL để phát hiện module bị ẩn hoặc gỡ liên kết.',
        'procdump': 'Trích xuất file thực thi EXE của tiến trình.',
        'dlldump': 'Trích xuất DLL từ không gian địa chỉ tiến trình.',
        'memdump': 'Trích xuất toàn bộ vùng nhớ có thể đọc của tiến trình.',
        'memmap': 'Xuất ánh xạ địa chỉ ảo/vật lý trực tiếp ra JSON, không hiện bảng trên GUI.',
        'vadinfo': 'Phân tích các vùng nhớ ảo VAD và quyền truy cập.',
        'vadtree': 'Hiển thị cây vùng nhớ VAD của tiến trình.',
        'vadwalk': 'Duyệt các nút trong cây VAD.',
        'vaddump': 'Trích xuất từng vùng nhớ VAD của tiến trình.',
        'hivelist': 'Liệt kê các hive Registry và địa chỉ offset.',
        'hivescan': 'Quét bộ nhớ pool tìm các hive Registry.',
        'printkey': 'Đọc khóa, khóa con và giá trị trong Registry.',
        'hivedump': 'Liệt kê cây khóa Registry của một hive.',
        'dumpregistry': 'Trích xuất các hive Registry ra file.',
        'userassist': 'Giải mã UserAssist để xem lịch sử ứng dụng đã chạy.',
        'shellbags': 'Khôi phục lịch sử thư mục đã duyệt từ ShellBags.',
        'shimcache': 'Khôi phục lịch sử thực thi lưu trong Application Compatibility Cache.',
        'amcache': 'Phân tích AmCache để tìm dấu vết ứng dụng đã thực thi.',
        'lsadump': 'Trích xuất LSA Secrets từ các hive trong bộ nhớ.',
        'cachedump': 'Trích xuất thông tin xác thực domain được cache.',
        'svcscan': 'Quét danh sách Windows Services, trạng thái và đường dẫn chương trình.',
        'modules': 'Liệt kê module kernel và driver đã nạp.',
        'modscan': 'Quét tìm module kernel và driver bị ẩn.',
        'moddump': 'Trích xuất driver kernel ra file.',
        'apihooks': 'Phát hiện API hook trong tiến trình và kernel.',
        'callbacks': 'Liệt kê callback kernel được đăng ký.',
        'connections': 'Liệt kê kết nối TCP trên Windows XP/2003.',
        'connscan': 'Quét tìm cấu trúc kết nối TCP trên Windows XP/2003.',
        'sockets': 'Liệt kê socket trên Windows XP/2003.',
        'sockscan': 'Quét tìm cấu trúc socket trên Windows XP/2003.',
        'clipboard': 'Khôi phục nội dung clipboard còn trong bộ nhớ.',
        'notepad': 'Khôi phục nội dung Notepad còn trong bộ nhớ; phụ thuộc phiên bản Windows.',
        'iehistory': 'Khôi phục cache và lịch sử Internet Explorer.',
        'screenshot': 'Dựng ảnh màn hình từ các cấu trúc GDI trong RAM.',
        'yarascan': 'Tìm chuỗi hoặc mẫu mã độc bằng YARA trong bộ nhớ.',
        'timeliner': 'Tổng hợp dấu thời gian và sự kiện thành timeline.',
    }
    categories = {
        'Dòng lệnh & Môi trường': 'cmdline cmdscan consoles envars',
        'Tiến trình': 'pslist pstree psscan dlllist handles getsids privs memmap vadinfo vadtree vadwalk joblinks sessions threads thrdscan',
        'Mã độc': 'malfind psxview ldrmodules apihooks yarascan impscan servicediff',
        'Registry': 'hivelist hivescan hivedump printkey dumpregistry userassist shellbags shimcache amcache auditpol getservicesids shutdowntime',
        'Mật khẩu': 'hashdump lsadump cachedump truecryptmaster truecryptpassphrase truecryptsummary',
        'Mạng': 'netscan connections connscan sockets sockscan',
        'File & Dữ liệu': 'filescan dumpfiles procdump dlldump memdump vaddump moddump dumpcerts evtlogs screenshot clipboard notepad iehistory mftparser strings imagecopy raw2dmp hpakextract',
        'Kernel & Driver': 'modules modscan driverscan driverirp drivermodule devicetree callbacks ssdt idt gdt timers unloadedmodules kpcrscan mutantscan symlinkscan objtypescan bigpools multiscan poolpeek',
    }
    known = {plugin['name']: plugin for plugin in VOLATILITY_2_PLUGINS}
    bundled = json.loads(Path(__file__).with_name('vol2_catalog.json').read_text(encoding='utf-8'))
    for entry in bundled:
        name = entry['name']
        # The web runner cannot host an interactive Python shell. Patching
        # evidence in place is outside the analysis workflow.
        if name in ('volshell', 'patcher'):
            continue
        category = next((cat for cat, names in categories.items() if name in names.split()), 'Hệ thống')
        if name in known:
            known[name]['category'] = category
            continue
        VOLATILITY_2_PLUGINS.append(dict(name=name, category=category, os='windows',
            desc=descriptions.get(name, entry['desc']), options=forms.get(name, [])))


_expand_vol2_catalog()


QUICK_TRIAGE_RECIPES = {
    "vol3": [
        {"name": "windows.info", "label": "1. Thông tin hệ điều hành", "desc": "Kiểm tra kiến trúc, build Windows, thời gian hệ thống"},
        {"name": "windows.pstree", "label": "2. Cây tiến trình (PsTree)", "desc": "Quan sát phả hệ tiến trình cha - con, phát hiện tiến trình giả mạo"},
        {"name": "windows.pslist", "label": "3. Danh sách tiến trình", "desc": "Liệt kê toàn bộ tiến trình, thời gian chạy và PID"},
        {"name": "windows.cmdline", "label": "4. Lệnh thực thi (CmdLine)", "desc": "Trích xuất tham số dòng lệnh được dùng để chạy ứng dụng"},
        {"name": "windows.netscan", "label": "5. Kết nối mạng (NetScan)", "desc": "Quét C2, socket kết nối ra ngoài và cổng mở"},
        {"name": "windows.malfind", "label": "6. Quét mã độc (Malfind)", "desc": "Phát hiện mã chèn không xác định trong không gian RAM"}
    ],
    "vol2": [
        {"name": "imageinfo", "label": "1. Nhận diện Profile", "desc": "Xác định profile Windows phù hợp"},
        {"name": "pstree", "label": "2. Cây tiến trình", "desc": "Quan sát phả hệ tiến trình"},
        {"name": "pslist", "label": "3. Danh sách tiến trình", "desc": "Liệt kê tiến trình đang chạy"},
        {"name": "cmdline", "label": "4. Lệnh thực thi", "desc": "Trích xuất tham số dòng lệnh"},
        {"name": "netscan", "label": "5. Kết nối mạng", "desc": "Quét kết nối mạng"},
        {"name": "malfind", "label": "6. Quét mã chèn", "desc": "Phát hiện vùng nhớ chèn mã độc"}
    ]
}
