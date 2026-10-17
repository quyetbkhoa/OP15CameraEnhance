# Hướng dẫn cho người dùng và agent

## 1. Lấy đúng nhánh

```powershell
git clone --branch dev https://github.com/quyetbkhoa/OP15CameraEnhance.git
cd OP15CameraEnhance
git status --short --branch
```

Nếu đã clone nhánh `main`, bảo toàn thay đổi hiện tại rồi chuyển sang `dev`.
Đọc `AGENTS.md`, `.ai/NOW.md` và `HANDOFF.md` trước khi sửa. Không chạy script từ
repo OP13 cũ để cài ZIP mới này.

## 2. Nội dung repo

| Đường dẫn | Nội dung |
|---|---|
| `op15/enhance.py` | Import stock có pin hash, patch, build/validate ZIP và thu thập ADB chỉ đọc |
| `op15/module/` | Script/metadata riêng cho OP15 |
| `op15/tests/` | 30 regression tests; mount/rollback được mô phỏng |
| `reference-stock/CPH2745-601-odm/` | 10 file cấu hình OEM tối thiểu để tái lập build/test; 677,196 byte |
| `op15/reference.json` | Hash nguồn và payload đã review |
| `artifacts/0.1.0-rc1/` | ZIP đã chốt, SHA256SUMS, candidate.json và changes.diff |
| `op15/VALIDATION.json` | Kết quả lần tạo candidate ban đầu |
| `HANDOFF_PROMPT.md` | Prompt sao chép nguyên phần text cho agent khác |

Đây là nguồn tham chiếu CPH2745 .601, không phải bản dump của điện thoại hiện tại.
Repo không kèm firmware đầy đủ, thư viện camera hoặc dữ liệu cá nhân của máy.
Các cấu hình OEM giữ nguyên nguồn gốc, không được tuyên bố là mã do dự án tự tạo.

## 3. Tự kiểm tra trên PC

Cần Python 3.11 trở lên; không có package pip bắt buộc. Test shell cần Bash:
trên Windows mặc định `C:\Program Files\Git\bin\bash.exe`, Linux `/bin/bash`.
Nếu Bash ở vị trí khác, đặt `OP15_TEST_BASH` trỏ đến file thực thi Bash của bạn.
Không dùng kết quả shell PC để kết luận SELinux/Android shell hoạt động.

Chạy từ gốc repo:

```powershell
python op15/enhance.py import-stock --odm reference-stock/CPH2745-601-odm --out op15/inputs/CPH2745-601-odm
python -m unittest discover -s op15/tests -v
python op15/enhance.py validate artifacts/0.1.0-rc1/OP15-Camera-Enhance-0.1.0-rc1-CPH2745-601.zip
python op15/enhance.py build --stock op15/inputs/CPH2745-601-odm --out op15/dist/rebuild-rc1
```

Expected: **30 tests PASS, không skip**, validate PASS và ZIP build lại có SHA256:

```text
90eb0eddfbd23f52b1f9c4d6a7cf322309097c8e2fd7bce910b3ced6426831d0
```

Windows kiểm hash:

```powershell
Get-FileHash op15/dist/rebuild-rc1/OP15-Camera-Enhance-0.1.0-rc1-CPH2745-601.zip -Algorithm SHA256
```

`import-stock` và `build` không ghi đè thư mục đã tồn tại. Lần sau giữ nguyên
snapshot đã import nếu hash còn khớp, và chọn output build mới. Đọc lỗi thật;
không xóa dữ liệu cũ chỉ để chạy lại lệnh. Input, captures, dist và Python cache
được ignore. Không đưa capture hoặc ảnh thật lên Git.

## 4. Khi chủ máy cắm OP15

Chờ chủ máy báo đã cắm và cho phép ADB/root. Sau đó xác định serial mới:

```powershell
adb devices -l
python op15/enhance.py capture --serial SERIAL_THUC_TE --out op15/captures/SESSION_MOI
```

Collector dùng root shell có sẵn hoặc `su -c sh`, không tự chạy `adb root` để
restart daemon. Nó chỉ đọc model/build, 10 config, trạng thái package/service,
module, SELinux context và mount info. Không push script/file lên máy. Nếu thiếu
root hoặc thu thập chưa đủ, giữ lại output và kiểm tra `capture.json`.

**Capture khớp hash chưa đủ để cài ngay.** Cần xem firmware, root manager, module
khác và dữ liệu đang bị overlay hay không. Sau đó trình bày kế hoạch cài/rollback
cho chủ máy và chờ cho phép sửa thiết bị. Upload repo không phải quyền cài/reboot.

Nếu khác CPH2745 .601 hoặc khác schema: lấy đúng nguồn gốc của máy, review lại,
làm candidate phiên bản mới. Không bỏ guard hay sửa giả model để ép chạy rc1.

## 5. Thử trên điện thoại — chỉ sau khi được cho phép

1. Chụp bộ stock chuẩn trước khi áp dụng, ghi build, trạng thái module và EXIF.
2. Cài bằng root manager trong Android, không recovery. Bộ cài kiểm nhận dạng,
   SELinux Enforcing, hash 10 file tham chiếu và 3 payload. Chỉ reboot khi đã được
   chủ máy đồng ý. Không xóa Camera data hoặc tự restart cameraserver.
3. Sau reboot đọc `runtime-status.txt` của module, xác minh file/hash/context
   trong namespace của process camera thực tế, không chỉ namespace của shell.
4. Kiểm tra crash/SELinux denial, mở/chụp/lưu/chuyển lens; so sánh stock/enhance
   cùng ánh sáng, tiêu cự, chế độ, phơi sáng: texture/da mặt/đối tượng động;
   main/UW/tele; HDR on/off, portrait, video, selfie, zoom cao và camera app khác.
5. So sánh halo, chi tiết, nhiễu, màu da, ghosting, thời gian lưu. Giữ ảnh gốc,
   không ảnh qua ứng dụng nén. Một cảnh đẹp không chứng minh mọi chế độ ổn định.

Các bảng coupleHDR có thể dùng chung giữa nhiều mode. Tên `SharpLevel` và sửa
scalar là cơ sở thử nghiệm, không chứng minh thuật toán đã dùng giá trị mới.

## 6. Hoàn tác

Tắt/gỡ `op15_camera_enhance` trong root manager rồi reboot khi được chủ máy cho
phép. Các file gốc không bị ghi đè; bind mounts biến mất khi reboot. Không phục
hồi module OP13. Sau OTA phải đối chiếu/build lại; không vượt chặn hash.

Nếu boot script báo rollback mount thất bại, không giả định máy đã về stock:
tắt module và xử lý reboot đã được cho phép, rồi xác minh lại namespace/hash.
