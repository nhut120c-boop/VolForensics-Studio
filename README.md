# ⚡ VolForensics Studio - Giao diện UX/UI cho Volatility 2 & Volatility 3

Ứng dụng giao diện đồ họa trực quan (Web-based Forensic Desktop UI) dành cho **Volatility 2** và **Volatility 3**, giúp bạn phân tích memory dump chuyên nghiệp mà **không cần phải gõ từng dòng lệnh terminal**, nhưng vẫn **giữ trọn vẹn 100% sức mạnh và tùy biến** của cả 2 phiên bản.

---

## 🌟 Tính năng nổi bật

1. **Hỗ trợ đồng thời Volatility 3 & Volatility 2**:
   - **Volatility 3**: Cài cùng các thư viện Python và chạy qua lệnh `vol`. Tự động xử lý Symbols, Windows/Linux/Mac.
   - **Volatility 2**: Tích hợp sẵn với mã nguồn `vol.py` trong thư mục, hỗ trợ chọn hoặc auto-detect profile (`imageinfo`/`kdbgscan`) hoặc cấu hình file `vol2.exe` standalone.

2. **Không cần nhớ lệnh hay gõ tay**:
   - **Catalog plugin phân loại thông minh**: Processes, Network, Malware, Registry, Credentials, Files & Dumps, Kernel, System.
   - **Tìm kiếm tức thì (Search & Filter)**: Lọc plugin theo từ khóa hoặc click chọn theo danh mục.
   - **Form tùy chọn động**: Tự sinh các ô nhập `--pid`, `--dump`, `--key`, `-D`, v.v. cho từng plugin cụ thể.
   - **CLI Preview thời gian thực**: Tự động sinh ra câu lệnh CLI hoàn chỉnh phía dưới, có nút copy 1-click.
   - **Tùy biến không giới hạn**: Có ô "Custom CLI Arguments" để chèn thêm bất kỳ cờ nâng cao nào (`--virtaddr`, `--regex`, v.v.).

3. **Chọn file Memory Dump cực nhanh**:
   - Nút **📂 Browse** mở cửa sổ Windows File Explorer gốc, chọn file `.raw`, `.vmem`, `.dmp`, `.dd`, `.img`, `.bin`, `.mem` mà không phải upload hay tốn tài nguyên.
   - Hiển thị dung lượng file (MB/GB) ngay khi chọn.

4. **1-Click Fast Triage (Phân tích nhanh theo kịch bản)**:
   - 1 nút bấm tự động chạy chuỗi phân tích cốt lõi:
     `System Info ➔ Process Tree ➔ Active Processes ➔ Cmdline ➔ Network ➔ Injected Code (Malfind)`.

5. **Trực quan hóa kết quả đa tầng**:
   - **📊 Interactive Data Grid**: Xem bảng dữ liệu có thể tìm kiếm, sắp xếp theo cột (click tiêu đề cột), đếm số dòng, export ra **CSV** và **JSON**.
   - **🌳 Process Tree View**: Xem cây phân cấp cha-con (PPID ➔ PID) trực quan cho các plugin `pstree`.
   - **💻 Live Console & Logs**: Hiển thị log streaming theo thời gian thực (Server-Sent Events) với nút Stop/Kill tiến trình khi đang chạy.
   - **📁 Extracted Dumps**: Quản lý các file thực thi / artifact được trích xuất (với nút mở thư mục trực tiếp trong Windows Explorer).
   - **📜 Run History**: Lưu lại lịch sử các lần chạy trong phiên làm việc để click xem lại kết quả bất cứ lúc nào.

---

## 🚀 Cách khởi động ứng dụng

Trên Windows, mở PowerShell trong thư mục dự án và cài thư viện bằng Python 3.10 trở lên.

```powershell
python -m pip install -r requirements-gui.txt
```

Bạn có 2 cách khởi chạy cực kỳ tiện lợi:

### Cách 1: Click đúp chuột vào file `.bat`
- Mở thư mục dự án.
- Click đúp vào file:
  ```
  Run_Volatility_GUI.bat
  ```

### Cách 2: Chạy qua lệnh Terminal
```powershell
python run_gui.py
```

Ứng dụng tự mở trình duyệt tại `http://127.0.0.1:8888`. Nếu cổng này đang bận, launcher chọn cổng trống kế tiếp và in địa chỉ thực tế.

## Thiết lập và xử lý lỗi

Giao diện chỉ dùng nhãn chữ, không dùng icon/emoji. Khi phân tích, vùng Console có hiệu ứng mã xanh riêng biệt với log thật; nút **Hiệu ứng: Bật/Tắt** lưu lựa chọn của bạn. Hiệu ứng dừng khi tác vụ xong, khi đổi tab hoặc khi cửa sổ bị ẩn. Trong tab Bảng Dữ Liệu, dùng **Toàn màn hình** để phóng bảng và giữ các nút lọc/xuất file; nhấn **Esc** hoặc **Thoát toàn màn hình** để trở lại.

Giao diện sử dụng nền đen, chữ xanh lá và font monospace; lỗi, cảnh báo và trạng thái thất bại hiển thị đỏ. Catalog Vol3 có 91 mục Windows có thể nạp từ bản đang cài, bao gồm cmdscan/consoles, VAD, YARA, MFT, Registry và driver. Các ô tùy chọn, giá trị lựa chọn và trường bắt buộc được lấy từ requirements của plugin. Có thể cập nhật snapshot catalog bằng `python scripts/sync_vol3_catalog.py`, rồi khởi động lại GUI.

`memmap` (Vol2) và `windows.memmap` (Vol3) xuất trực tiếp `memmap.json` vào thư mục lần chạy và tự tải file khi hoàn tất. GUI chỉ hiển thị trạng thái cùng nút tải JSON, không dựng bảng/log chứa hàng chục nghìn dòng. Vol3 có tùy chọn `--dump` để tạo thêm file bộ nhớ `.dmp`; JSON là kết quả ánh xạ, không phải nội dung bộ nhớ tiến trình.

- Volatility 2 standalone trong `bin/vol2` được tự động nhận diện; không cần Python 2 khi dùng bản này.
- Catalog Volatility 2 gồm 112 mục, có `cmdscan`, `consoles`, `envars`, `dlllist`, `handles`, `hivelist`, `printkey`, `psxview`, các plugin dump và nhiều mục khác. Tìm theo tên plugin hoặc chọn nhóm **Dòng lệnh & Môi trường**. Các tùy chọn chuyên sâu có thể nhập trong ô Custom CLI Arguments. `volshell` (shell tương tác) và `patcher` (sửa trực tiếp dữ liệu) không đưa vào giao diện phân tích.
- Cấu hình được lưu trong `gui_config.json`. Đường dẫn engine là đường dẫn file thực thi, không kèm tham số.
- Đường dẫn WSL/UNC được hỗ trợ trực tiếp, kể cả dấu cách, như `\\wsl.localhost\Ubuntu\home\analyst\Memory Images\image.raw`. Volatility 3 dùng `--single-location` để giữ nguyên tên máy chủ UNC.
- Với Volatility 2, chạy `imageinfo` trước. GUI điền profile gợi ý đầu tiên nếu ô profile còn trống; bạn có thể sửa lại. Triage tự nhận diện profile trước các bước tiếp theo.
- Mỗi tác vụ có thư mục riêng trong `output`. Nút Dừng trong Triage hủy tiến trình đang chạy và các tác vụ đang chờ. Lịch sử tác vụ được giữ trong phiên server hiện tại.
- `windows.dumpfiles` tự thêm `.img` (ImageSectionObject), `.dat` (DataSectionObject) hoặc `.vacb` (SharedCacheMap). GUI chỉ lấy tên gốc từ tên bản dump để hiển thị; không tự đọc lại nội dung, đổi tên hay tạo bản sao recovered. File 0 byte không có dữ liệu để mở; tên file không xác nhận dữ liệu được khôi phục đầy đủ.
- GUI ưu tiên thư viện tương thích trong `.gui-deps` cho Volatility 3. Có thể cài riêng bằng `python -m pip install --target .gui-deps "capstone>=5.0.3,<6" "yara-python>=4.5.1,<5" "pycryptodome>=3.21,<4"`. Capstone 6 không tương thích với renderer của Volatility 3 2.28.2.
- Plugin vẫn có thể báo lỗi do dump không phù hợp, thiếu symbols hoặc tùy chọn bắt buộc; xem Console để biết lỗi cụ thể. Không phải plugin nào cũng áp dụng được cho mọi phiên bản Windows.

Kiểm thử backend: `python -m unittest discover -s tests -p test_gui.py -v`.
