# Câu hỏi thường gặp

### Đăng nhập bằng tài khoản mật khẩu thất bại

Hiện tại việc đăng nhập dường như 100% gặp phải mã xác nhận, khuyến nghị sử dụng đăng nhập bằng mã QR.

### Làm thế nào để lấy/thiết lập XXX của thiết bị XXX?

Tôi sở hữu thiết bị có hạn, không thể đảm bảo có thể giải đáp loại câu hỏi này, nhưng cũng hoan nghênh gửi [issue](https://github.com/Do1e/mijia-api/issues), có thể cần bạn chia sẻ thiết bị cho tôi để bắt gói tin hoặc tự bắt gói tin cung cấp cho tôi request và response, nếu cung cấp file har thì lưu ý tự xóa cookie và các thông tin nhạy cảm khác.

### Làm thế nào để bắt gói tin?

Xiaomi chính thức đã cung cấp một [hướng dẫn bắt gói tin](https://iot.mi.com/new/doc/accesses/direct-access/extension-development/troubleshooting/packet_capture), tôi chưa thử, không chắc có được hay không, nếu bắt gói tin thành công mà dữ liệu bị mã hóa, có thể sử dụng [demos/decrypt.py](demos/decrypt.py) để giải mã.

Giải pháp của tôi là sử dụng điện thoại đã root, cài đặt [reqable](https://reqable.com/zh-CN/) để bắt gói tin, sau khi xuất file HAR sử dụng [demos/decrypt_har.py](demos/decrypt_har.py) để giải mã.

### Có thể hỗ trợ callback thiết bị không?

Do yêu cầu của [giấy phép mã nguồn mở ha_xiaomi_home](https://github.com/XiaoMi/ha_xiaomi_home/blob/main/LICENSE.md), sẽ không hỗ trợ các chức năng liên quan.
