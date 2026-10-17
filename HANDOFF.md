# Bàn giao OP15 Camera Enhance

## Mục tiêu và trạng thái

Chủ máy chuyển từ OP13 sang OP15 và muốn enhance camera gốc. Yêu cầu hiện tại:
chuẩn bị trước, báo để chủ máy cắm OP15 có ADB/root; sau đó kiểm tra trên máy.
Repo được upload theo yêu cầu riêng để bàn giao cho agent khác.

**AWAITING_USER: chờ kết nối máy để thu thập chỉ đọc.** Chưa cài hoặc kiểm tra
camera trên thiết bị. Không có nghiệm thu chất lượng ảnh.

Repo độc lập: `quyetbkhoa/OP15CameraEnhance`. `main` chỉ bootstrap tài liệu;
`dev` chứa source/bản thử. Đường làm việc tiếp theo: task branch từ `dev`.
Repo OP13-OCVM gốc không bị thay remote, commit hoặc push.

## Candidate đã đóng băng

- Phiên bản: **0.1.0-rc1**.
- ZIP: `artifacts/0.1.0-rc1/OP15-Camera-Enhance-0.1.0-rc1-CPH2745-601.zip`.
- SHA256: `90eb0eddfbd23f52b1f9c4d6a7cf322309097c8e2fd7bce910b3ced6426831d0`.
- Tham chiếu: stock **CPH2745_16.0.10.601(EX01), SM8850**.
- **Model/build/serial/root manager của điện thoại hiện tại: UNKNOWN.**

Chỉ 30 giá trị `SharpLevel` 50 → 40, trong năm hàng ISO ≤ 800 đang dùng của hai
bảng `aps.params.snapshot.couplehdr` và `.face`, tại `infinitimain`,
`infinititele`, `infinitiultrawide`. Header/Count, các byte khác, high ISO và
denoise giữ nguyên. Không bổ sung thư viện, model AI, routing, AWB/calibration,
clock/bandwidth/buffer hoặc property. Đây là thử nghiệm chống sharpening quá tay,
chưa phải toàn bộ tính năng enhance từ OP13.

## Bằng chứng

30/30 regression tests đạt khi tạo candidate trên Windows/Python 3.11.9/Git Bash.
Kiểm tra schema, vị trí scalar, giữ nguyên byte, sai stock, ZIP tái lập, hash và
gói bị sửa, shell syntax, guard sai model/SoC/SELinux/config, ADB explicit serial
và từ chối thiếu root. Mount thành công/rollback/sai nguồn là mô phỏng file tạm.
`op15/VALIDATION.json` lưu kết quả gốc; `PUBLISH_VALIDATION.json` ghi kết quả của
gói bàn giao sau khi thử lại trong clone sạch.

| Kiểm tra thực tế | Trạng thái |
|---|---|
| ADB/nhận dạng máy hiện tại | NOT RUN |
| Root manager install, boot, SELinux access | NOT RUN |
| Bind mount/rollback trên Android | NOT RUN |
| Camera/cameraserver nhìn thấy đúng config | NOT RUN |
| Thuật toán thực sự tiêu thụ các bảng đã đổi | NOT RUN |
| Chụp/lưu/chuyển lens, ảnh A/B, độ ổn định | NOT RUN |

File/map/property hoặc return code không phải chứng minh thuật toán hay ảnh tốt.
Giá trị giảm 20% không tương đương mức sharpening thực tế giảm đúng 20%.

## Thiết kế và điểm cần kiểm tra

- `skip_mount` có chủ đích. Script post-fs-data kiểm tra toàn bộ trước, rồi bind
  riêng ba file. Không cài metamodule; tương thích root manager còn cần xác minh.
- Pin hash 10 config/build.prop và 3 payload, chặn CPH2745/SM8850/OnePlus không
  khớp hoặc SELinux không Enforcing. Đây không phải kiểm chứng toàn firmware.
- Installer sao chép SELinux context từ file gốc và readback. Cần xác minh Android
  thực tế; PC shell không chứng minh context hợp lệ hay namespace đúng.
- Thất bại ở giữa mount/readback sẽ thử unmount các bind vừa tạo; nếu unmount lỗi
  ghi rõ ERROR và yêu cầu tắt module/reboot. Chưa thử rollback trên Android.
- Guard tên module camera chỉ là heuristic; module có tên khác vẫn có thể sửa
  thư viện/property. Capture module + mountinfo cần được đọc thủ công.
- `matches_reference` của collector chỉ so sánh config hash, không phải toàn bộ
  tương thích hoặc lệnh cho phép cài.

## Nguồn và tính di động

Nguồn OP13 đã xem: main `09391e981a6874cbee395214e673f50e49b033dd`, dev
`88dcbfc286f6e2f103e50228100e5c1c03efc1da`. Main cũ trộn nhiều port hooks,
`setenforce 0`, clear Camera data và forced clock/buffer; không đóng gói lại.

Stock OP15 đến từ bản extract đã lưu của ROM CPH2745 .601. `reference-stock/`
kèm đúng 10 file byte-pinned (677,196 byte), đủ build/test; không có toàn bộ ROM,
thư viện, partition dump hay dữ liệu live. Các path H: trong audit là nguồn gốc
lịch sử, không phải điều kiện chạy; dùng `GUIDE.md` để tái lập trên máy khác.

## Quyền và việc tiếp theo

Đã được phép publish **gói bàn giao này** tới repo mới. Chưa được phép cài module,
restart adbd/camera, clear app data/log, flash hoặc reboot máy. Không suy ra quyền
device mutation từ việc cắm máy/root, và không suy ra quyền push tương lai vô hạn.

Đọc repo → self-test → chờ chủ máy cắm → ADB chỉ đọc với serial mới → review model,
build/module/context/namespace → nếu cần thì build candidate mới → trình bày kế
hoạch cụ thể và rollback → chờ chủ máy cho phép cài/reboot → thử thực tế và ghi
nghiệm thu chính xác ZIP. Giữ rc1, nguồn stock và các capture cục bộ; không ghi đè.
