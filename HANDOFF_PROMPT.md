# Prompt bàn giao — sao chép phần dưới cho agent tiếp theo

```text
Bạn tiếp tục dự án OP15 Camera Enhance:
https://github.com/quyetbkhoa/OP15CameraEnhance.git

Hãy clone nhánh dev (main hiện chỉ có trang hướng dẫn):
git clone --branch dev https://github.com/quyetbkhoa/OP15CameraEnhance.git

Mục tiêu của tôi: enhance camera GỐC trên OnePlus 15. Trước đây port Find X8 Ultra
sang OP13 còn nhiều vấn đề; lần này không mặc định bê port/thư viện/tuning OP13
hay X8U sang OP15. Tôi cần hiệu quả và ổn định có chứng cứ trên máy thật.

Đọc theo thứ tự: AGENTS.md, .ai/PROJECT.md, .ai/NOW.md, HANDOFF.md, GUIDE.md,
op15/AUDIT.md, op15/reference.json và source liên quan. Kiểm tra Git trước khi sửa.

Trạng thái đã có:
- Candidate offline 0.1.0-rc1 trong artifacts/0.1.0-rc1/.
- SHA256 ZIP: 90eb0eddfbd23f52b1f9c4d6a7cf322309097c8e2fd7bce910b3ced6426831d0.
- Tham chiếu ODM stock CPH2745_16.0.10.601(EX01), SM8850. CHƯA biết firmware,
  nhận dạng hiện tại hay root manager trên OP15 của tôi.
- Chỉ 30 SharpLevel 50 -> 40 tại 5 hàng ISO <= 800 đang dùng của hai bảng
  aps.params.snapshot.couplehdr và .face, trong infinitimain/infinititele/
  infinitiultrawide. Các byte khác giữ nguyên; không thay thư viện hay model AI.
- 30/30 kiểm tra offline đạt khi tạo candidate. Test mount/rollback là mô phỏng.
- CHƯA cài module, chưa boot/test camera, chưa chứng minh thuật toán dùng bảng
  chỉnh sửa, chưa chứng minh chất lượng ảnh tăng. Có thể dùng chung bảng giữa
  nhiều UI mode; không suy ra chỉ Photo chịu ảnh hưởng.
- Module kiểm tra identity/hashes/SELinux Enforcing trước install và trước bind
  ba file ở post-fs-data. skip_mount là có chủ đích. Mount trong namespace script
  không chứng minh camera/cameraserver nhìn thấy hoặc dùng cấu hình đó.

Việc cần làm tiếp:
1. Chạy lại self-test theo GUIDE.md bằng cấu hình tham chiếu đã kèm repo, xác minh
   hash ZIP. Không bỏ qua test trên môi trường mới; ghi rõ shell Android chưa thử.
2. Tôi sẽ cắm OP15 có ADB/root. Khi tôi xác nhận đã cắm máy, lấy adb devices -l,
   dùng serial mới đọc được cho mọi lệnh. Thu thập chỉ đọc bằng enhance.py capture;
   không tự restart adbd/camera, xóa dữ liệu/log, đẩy file, cài module hay reboot.
3. Đối chiếu model/SoC/build/config hash, root manager, module đang hoạt động,
   SELinux context và mount namespace. Capture có thể thấy overlay, không mặc
   định coi dữ liệu từ shell là stock. Không lấy serial/model từ ghi chú cũ.
4. Nếu khác firmware hoặc schema, lấy đúng stock của máy và làm candidate mới,
   giữ nguyên rc1 và các bản gốc. Không sửa giả identity hoặc bỏ guard để ép cài.
5. Trước khi cài/reboot, trình bày thay đổi cụ thể và cách hoàn tác rồi chờ tôi
   cho phép; yêu cầu upload/bàn giao này không phải cho phép sửa điện thoại.
6. Khi được cho phép, xác minh mount/hash/context trong process camera thực tế,
   giữ SELinux Enforcing, kiểm tra crash/denial, chụp và lưu ảnh, chuyển lens,
   HDR/portrait/video/selfie/zoom và so sánh A/B cùng cảnh/phơi sáng. Không coi
   property, file map, return code hoặc ảnh đơn lẻ là chứng minh thuật toán hoạt động.

Không tắt SELinux, không ghi persist property, không ép clock/bandwidth/buffer,
không thay calibration/AWB/ISP, không xóa dữ liệu Camera hoặc phục hồi module OP13.
Không ghi đè artifacts/inputs/captures, không promote code lên main trước khi
nghiệm thu chính xác candidate. Làm việc trên task branch từ dev, self-test,
cập nhật NOW và báo rõ áp dụng/chờ reboot/chưa kiểm tra. Nếu cần push, tuân thủ
phạm vi cho phép hiện tại; việc tôi bảo upload lần trước không phải quyền push
vô hạn cho các thay đổi tương lai.

Nếu tôi chưa cắm máy, hoàn thành phần đọc repo/self-test rồi báo sẵn sàng để tôi
cắm máy. Không tự bịa trạng thái thiết bị hoặc tuyên bố enhance đã hoàn thiện.
```
