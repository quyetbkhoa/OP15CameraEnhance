# OP15 Camera Enhance

Enhance camera gốc OnePlus 15. **Bản thử hiện tại chưa được cài hoặc xác nhận
trên điện thoại.** Repo này được công bố để bàn giao phát triển, không phải bản
phát hành đã được nghiệm thu.

## Bắt đầu ở nhánh `dev`

`main` hiện là trang hướng dẫn. Toàn bộ source, test, cấu hình tham chiếu và ZIP
**0.1.0-rc1** nằm ở [nhánh dev](https://github.com/quyetbkhoa/OP15CameraEnhance/tree/dev).
Code thử nghiệm chưa được đưa lên `main` như một bản ổn định.

```powershell
git clone --branch dev https://github.com/quyetbkhoa/OP15CameraEnhance.git
cd OP15CameraEnhance
```

- [Hướng dẫn build, test và đối chiếu máy](https://github.com/quyetbkhoa/OP15CameraEnhance/blob/dev/GUIDE.md)
- [Trạng thái và thông tin bàn giao](https://github.com/quyetbkhoa/OP15CameraEnhance/blob/dev/HANDOFF.md)
- [Prompt gửi cho agent tiếp theo](HANDOFF_PROMPT.md)
- [ZIP bản thử cùng hash và báo cáo](https://github.com/quyetbkhoa/OP15CameraEnhance/tree/dev/artifacts/0.1.0-rc1)
- [Chi tiết kỹ thuật](https://github.com/quyetbkhoa/OP15CameraEnhance/blob/dev/op15/README.md)

## Phạm vi rc1

Tham chiếu **CPH2745_16.0.10.601(EX01), SM8850**; không suy ra đây là firmware
trên OP15 của chủ máy. Chỉ đổi **30 giá trị `SharpLevel` từ 50 thành 40** trong
các hàng ISO ≤ 800 của hai bảng coupleHDR, trên ba camera sau. Không port thư viện
Find X8 Ultra hoặc dùng cấu hình cảm biến OP13.

**30/30 kiểm tra offline đạt** ở lần tạo candidate. Bind mount/rollback trong
test được mô phỏng; chưa thử cài, boot, SELinux, namespace của camera, thuật toán,
độ ổn định hoặc chất lượng ảnh trên OP15 thật. Giảm giá trị tuning không phải
bằng chứng rằng ảnh tốt hơn hoặc thuật toán đã dùng bảng đó.

Chủ máy sẽ cắm OP15 có ADB/root sau. Agent tiếp theo cần đọc trạng thái, thu thập
chỉ đọc và đối chiếu trước; việc upload repo không cấp phép cài module/reboot.

Nguồn tham khảo: [OP13-OCVM](https://github.com/quyetbkhoa/OP13-OCVM), main
`09391e981a6874cbee395214e673f50e49b033dd`, dev đã xem
`88dcbfc286f6e2f103e50228100e5c1c03efc1da`.
