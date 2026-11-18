# VolForensics Studio

VolForensics Studio cung cấp giao diện web cục bộ trên Windows để phân tích ảnh bộ nhớ bằng Volatility 2 và Volatility 3. Bạn có thể chọn plugin, chỉnh tham số, theo dõi log và xuất kết quả ngay trong trình duyệt.

## Cài đặt và khởi chạy

Yêu cầu Windows 64-bit và Python 3.10 trở lên. Mở PowerShell trong thư mục dự án rồi chạy:

```powershell
python -m pip install -r requirements-gui.txt
python run_gui.py
```

Sau khi cài thư viện, bạn cũng có thể mở ứng dụng bằng `Run_Volatility_GUI.bat`.

Trình duyệt tự mở tại `http://127.0.0.1:8888`. Nếu cổng 8888 đang bận, hãy dùng địa chỉ được in trong PowerShell.

- **Volatility 3** được cài từ `requirements-gui.txt`. Nếu ứng dụng chưa tìm thấy `vol.exe`, nhập đường dẫn đến tệp thực thi trong **Cài đặt**.
- **Volatility 2** dùng bản standalone đi kèm trong `bin/vol2`. Nếu chạy bản mã nguồn `vol.py`, cấu hình đường dẫn Python 2.7 và `vol.py` trong **Cài đặt**.

## Phân tích ảnh bộ nhớ

1. Chọn Volatility 2 hoặc Volatility 3, sau đó bấm **Chọn file** hoặc nhập đường dẫn ảnh bộ nhớ. Có thể dùng tệp trên máy, đường dẫn UNC hoặc thư mục chia sẻ qua WSL.
2. Với Volatility 2, chạy `imageinfo` để tìm profile Windows nếu chưa biết. Giao diện điền profile gợi ý đầu tiên khi ô **Profile** còn trống.
3. Tìm plugin theo tên hoặc nhóm. Ví dụ, tìm `consoles` trong nhóm **Dòng lệnh & Môi trường** để đọc lịch sử lệnh và nội dung console khi dump có dữ liệu tương ứng.
4. Điền các tùy chọn của plugin. Dùng ô **Tham số bổ sung** nếu cần nhập cờ CLI, xem lệnh đã tạo ở dòng **Lệnh**, rồi bấm **Chạy**.

Bấm **Chạy Triage** để kiểm tra lần lượt thông tin hệ thống, tiến trình, dòng lệnh, kết nối mạng và vùng nhớ đáng ngờ. Trên Volatility 2, bước đầu tiên là `imageinfo`. Triage dùng profile gợi ý cho các bước tiếp theo nếu bạn để trống ô **Profile**.

## Xem và xuất kết quả

- **Bảng dữ liệu** hỗ trợ lọc, sắp xếp theo cột và xuất CSV hoặc JSON. Nhấn `Esc` để thoát chế độ toàn màn hình.
- **Cây tiến trình** hiển thị quan hệ cha–con từ kết quả `pstree`.
- **Log** hiển thị đầu ra trong lúc plugin chạy. Bấm **Dừng** để hủy tác vụ đang chạy.
- **Tệp trích xuất** liệt kê các tệp trong thư mục kết quả của tác vụ. Mặc định, mỗi tác vụ có một thư mục riêng trong `output/`.
- **Lịch sử** cho phép mở lại kết quả trong phiên chạy hiện tại.

`memmap` trên Volatility 2 và `windows.memmap` trên Volatility 3 lưu bảng ánh xạ vào `memmap.json` trong thư mục tác vụ. Với Volatility 3, bật `--dump` nếu cần xuất thêm nội dung bộ nhớ tiến trình ra tệp `.dmp`.

## Xử lý sự cố

- **Engine chưa sẵn sàng.** Kiểm tra đường dẫn tệp thực thi trong **Cài đặt**. Chỉ nhập đường dẫn, bỏ các tham số CLI. Cấu hình được lưu trong `gui_config.json`.
- **Plugin báo lỗi.** Xem tab **Log** để kiểm tra profile, symbol và tham số bắt buộc. Khả năng chạy plugin phụ thuộc vào phiên bản Windows và dữ liệu có trong ảnh bộ nhớ.
- **Tệp từ `windows.dumpfiles` có hậu tố lạ.** Plugin dùng `.img` cho `ImageSectionObject`, `.dat` cho `DataSectionObject` và `.vacb` cho `SharedCacheMap`.

## Kiểm thử và cập nhật danh mục plugin

Chạy bộ kiểm thử từ thư mục dự án:

```powershell
python -m unittest discover -s tests -v
```

Sau khi đổi phiên bản engine, chạy `python scripts/sync_vol3_catalog.py` để cập nhật danh mục plugin Windows của Volatility 3 hoặc `python scripts/sync_vol2_catalog.py` để cập nhật danh mục từ bản Volatility 2 standalone. Khởi động lại ứng dụng để nạp danh mục mới.

## Giấy phép của Volatility 2

Xem [giấy phép mã nguồn Volatility 2](volatility-master/LICENSE.txt) và [giấy phép của bản standalone](bin/vol2/volatility_2.6_win64_standalone/LICENSE.txt).
