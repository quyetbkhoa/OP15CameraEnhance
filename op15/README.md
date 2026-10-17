# OP15 Camera Enhance — 0.1.0-rc1

**Bản thử offline, chờ đối chiếu OP15 thật. Chưa cài lên điện thoại.**

Phát triển độc lập trong `op15/`, dựa trên ý tưởng enhance của OP13-OCVM.
Repo OP13-OCVM cũ và `addon/` của nó chỉ là nguồn tham khảo; chúng không có
trong repo OP15 độc lập hoặc ZIP OP15. Đọc thêm `GUIDE.md` và `HANDOFF.md` ở gốc.

## Bản đầu thay đổi gì?

Dùng cấu hình OP15 gốc từ **CPH2745_16.0.10.601(EX01), SM8850**, không dùng
cấu hình `dodge` của OP13. Mục tiêu thử nghiệm: giảm viền gắt do sharpening trong
ảnh HDR ở ISO thấp, để đánh giá khả năng giữ kết cấu tự nhiên.

| Phạm vi | Thay đổi |
|---|---|
| `infinitimain`, `infinititele`, `infinitiultrawide` | 3 file cấu hình gốc OP15 |
| `aps.params.snapshot.couplehdr`, `aps.params.snapshot.couplehdr.face` | Mỗi bảng sửa 5 hàng ISO ≤ 800 đang dùng |
| `SharpLevel` | `50` → `40`, tổng 30 giá trị |
| ISO cao, các giá trị khử nhiễu và cờ bật/tắt | Giữ nguyên |
| Bảng riêng của portrait, camera trước, video | Giữ nguyên byte |
| Thư viện, model AI, màu/AWB, topology cảm biến, kích thước/buffer/clock | Không có payload thay thế |

Giảm giá trị tuning 20% **không có nghĩa ảnh giảm sharpening đúng 20%**.
Đường xử lý có thể dùng bảng chung cho nhiều chế độ UI; chưa chứng minh việc áp
dụng chỉ giới hạn ở Photo. Chưa xác nhận thuật toán có dùng các bảng này trong
cảnh chụp cụ thể hoặc ảnh thực tế sẽ tốt hơn. Cần so sánh A/B và kiểm tra runtime.
Đây là phạm vi rc1 có chủ đích; không tuyên bố đã chuyển mọi tính năng enhance
của OP13 sang OP15.

## Cơ chế cài và hoàn tác

ZIP cài từ trình quản lý root trong Android. Không có recovery installer.
Không chạy `customize.sh` ở gốc repo OP13. Module có `skip_mount`: bỏ qua mount
tự động, script `post-fs-data.sh` kiểm tra trước rồi bind từng file vào `/odm`.
Không cần cài thêm metamodule cho cách bind này, nhưng khả năng nhìn thấy mount
trong namespace của Camera/cameraserver và tương thích với root manager **chưa
được thử trên máy thật**.

Bộ cài và mỗi lần boot đều kiểm tra nhận dạng ODM CPH2745/SM8850/OnePlus,
SELinux Enforcing, hash 10 file gốc và 3 payload. Sai firmware hoặc đang có
overlay thay đổi file thì từ chối. Có kiểm tra tên module camera xung đột phổ
biến; việc này không phát hiện được mọi module có tên tùy ý. Phải xem danh sách
module và trạng thái thực tế trước khi cài.

Không xóa dữ liệu Camera, ghi persist property, tắt SELinux, sửa chính sách,
restart cameraserver hay tự reboot. Phân vùng gốc không bị ghi đè.
`runtime-status.txt` chỉ báo kết quả mount ở namespace của script boot.

Hoàn tác: tắt/gỡ `op15_camera_enhance` bằng root manager rồi reboot. Cần reboot
để chắc chắn các bind mount không còn trong mọi namespace. Sau OTA phải đối chiếu
lại, không bỏ chặn hash để ép cài. Không dùng module OP13 làm phương án rollback.

## Build và kiểm tra trên PC

Python 3.11+, thư viện chuẩn. Chạy từ thư mục gốc repo OP15CameraEnhance (nhánh `dev`):

```powershell
python op15/enhance.py import-stock --odm reference-stock/CPH2745-601-odm --out op15/inputs/CPH2745-601-odm
python -m unittest discover -s op15/tests -v
python op15/enhance.py build --stock op15/inputs/CPH2745-601-odm --out op15/dist/0.1.0-rc1
python op15/enhance.py validate op15/dist/0.1.0-rc1/OP15-Camera-Enhance-0.1.0-rc1-CPH2745-601.zip
```

Không chạy lại `import-stock`/`build` với output đã tồn tại; dùng thư mục phiên
bản mới. `reference.json` pin hash, nguồn và commit đã tham khảo. Inputs, captures
và dist được ignore; snapshot tham chiếu tối thiểu nằm trong `reference-stock/`.
Các bản OEM gốc trên máy ban đầu chỉ được đọc, không sửa. `changes.diff`,
`candidate.json`, `SHA256SUMS.txt` ở cạnh ZIP phục vụ review.

30 regression tests ban đầu dùng các file OP15 thật, kiểm tra chỉ sửa đúng scalar,
giữ nguyên các byte khác, count/schema, sai nguồn, ZIP tái lập, gói bị sửa,
guard sai model/SoC/hash/SELinux và capture root. Thử mount/rollback trong test là
**mô phỏng bằng file tạm**, không phải mount trên Android. Shell syntax được kiểm
tra bằng Git Bash; môi trường shell/SELinux Android chưa được kiểm tra.

## Khi người dùng cắm OP15

Người dùng yêu cầu báo trước để họ cắm máy sau bước offline. Chưa chạy ADB trong
bước chuẩn bị. Khi có máy, xác định lại `adb devices -l`, dùng serial rõ ràng:

```powershell
python op15/enhance.py capture --serial SERIAL_THUC_TE --out op15/captures/SESSION_MOI
```

Collector chỉ đọc qua ADB root hiện có hoặc `su -c sh`; không restart adbd để xin
root, không đẩy script/file lên máy, không clear log, không mở app hay tự cài ZIP.
Ghi nhận model/build, các config đang nhìn thấy, package Camera, module và mount
info. Capture lưu cục bộ, có serial/fingerprint/diagnostics; không push lên Git.
File lấy từ namespace của shell có thể đã bị module khác thay đổi.

Nếu máy dùng build khác (ví dụ ODM CPH2747 hoặc ROM CN), lấy đúng config gốc,
review schema/thay đổi và làm candidate phiên bản mới; không sửa nhận dạng giả để
qua guard. Nếu khớp vẫn phải review overlay/root manager trước khi xin cài.

Sau khi được cho phép cài/reboot: xác nhận hash và SELinux context trong namespace
của **process camera thực sự**, xem lỗi native/SELinux và kiểm tra chụp/lưu ảnh.
Không coi file đã map hay hash readback là chứng minh thuật toán đã chạy.

Kiểm tra ảnh stock/enhance cùng cảnh, ánh sáng, tiêu cự, phơi sáng và chế độ:
main/UW/tele; ngoài trời/trong nhà/thiếu sáng; vật có kết cấu/da mặt/đối tượng động;
Photo HDR on/off, portrait, video, selfie, zoom cao, mở camera từ app khác.
So sánh viền halo, kết cấu, nhiễu, màu da, ghosting, thời gian lưu và lỗi chuyển
ống kính. Giữ ảnh gốc/EXIF, không dùng ảnh qua ứng dụng nén. Chỉ chấp nhận chính
xác candidate được thử; một ảnh đẹp không chứng minh mọi chế độ ổn định.

## Tài liệu nền đã đối chiếu

- [Repo OP13-OCVM](https://github.com/quyetbkhoa/OP13-OCVM)
- [Magisk module guide](https://topjohnwu.github.io/Magisk/guides.html)
- [KernelSU module guide](https://kernelsu.org/guide/module.html)

Gói này dùng cơ chế script bind riêng nên không tuyên bố tương thích mount tự
động với mọi root manager dựa trên hai tài liệu trên.
