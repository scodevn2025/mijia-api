# Câu hỏi thường gặp

### Đăng nhập bằng tài khoản mật khẩu thất bại

Hiện tại đăng nhập dường như 100% gặp phải mã xác thực, khuyến nghị sử dụng đăng nhập bằng mã QR.

### Làm thế nào để lấy/thiết lập XXX của thiết bị XXX?

Tôi có số lượng thiết bị hạn chế, không thể đảm bảo trả lời được loại câu hỏi này, nhưng cũng hoan nghênh tạo [issue](https://github.com/Do1e/mijia-api/issues), có thể cần bạn chia sẻ thiết bị cho tôi để capture packet hoặc tự capture packet cung cấp cho tôi request và response, nếu cung cấp file har thì chú ý tự xóa cookie và thông tin nhạy cảm khác.

### Làm thế nao để capture packet?

Xiaomi chính thức cung cấp một [hướng dẫn capture packet](https://iot.mi.com/new/doc/accesses/direct-access/extension-development/troubleshooting/packet_capture), tôi chưa thử, không chắc có thể thực hiện được không, nếu capture packet thành công mà dữ liệu bị mã hóa, có thể sử dụng [demos/decrypt.py](demos/decrypt.py) để giải mã.

Giải pháp của tôi là sử dụng điện thoại đã root, cài đặt [reqable](https://reqable.com/zh-CN/) để capture packet, xuất file HAR sau đó sử dụng [demos/decrypt_har.py](demos/decrypt_har.py) để giải mã.

### Có thể hỗ trợ callback thiết bị không?

Do yêu cầu của [giấy phép mã nguồn mở ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home/blob/main/LICENSE.md), sẽ không hỗ trợ chức năng liên quan.
