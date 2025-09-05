# Nhật ký thay đổi

Tài liệu này ghi lại các thay đổi quan trọng của dự án kể từ v1.3.7.

## [2.0.1](https://github.com/Do1e/mijia-api/compare/v2.0.0...v2.0.1) - 2025-06-29
### bugfix
* Xử lý trường hợp hơn 200 thiết bị trong một gia đình, sửa lỗi phương thức `get_devices_list` có thể không lấy được tất cả thiết bị
### improvement
* Tất cả nội dung in đều sử dụng tiếng Trung

## [2.0.0](https://github.com/Do1e/mijia-api/compare/v1.5.0...v2.0.0) - 2025-06-27
#### Phiên bản này có nhiều thay đổi đột phá, vui lòng tham khảo hướng dẫn dưới đây để sửa chữa sau khi nâng cấp
### new feature
* Thêm API: `get_statistics`, dùng để lấy thông tin thống kê của thiết bị, cách sử dụng xem [demos/test_get_statistics.py](demos/test_get_statistics.py)
* Thêm file [demos/decrypt.py](demos/decrypt.py) và [demos/decrypt_har.py](demos/decrypt_har.py), dùng để giải mã gói tin bắt từ ứng dụng Mijia
* `get_homes_list` hỗ trợ lấy gia đình được chia sẻ
* `get_consumable_items` hỗ trợ lấy danh sách vật tư tiêu hao của gia đình được chia sẻ, cần chỉ định thêm tham số `owner_id`
* `get_devices_list` hỗ trợ lấy danh sách thiết bị của gia đình được chia sẻ
### improvement
* File xác thực lưu `cUserId`, có thể dùng thay thế cho `userId`, tạm thời chưa sử dụng
* **Phiên bản này đã loại bỏ hoàn toàn `mijiaDevices`, vui lòng kịp thời thay thế bằng `mijiaDevice`**
* **Phương thức `set` của `mijiaDevice` đã thay đổi thứ tự tham số, vui lòng kịp thời sửa chữa**
* **Một số API sau khi gọi cần đọc từ điển giá trị trả về, như `api.get_devices_list()['list']`, giờ trả về trực tiếp danh sách, vui lòng chú ý sửa đổi, như `api.get_devices_list()`, danh sách cụ thể như sau:**
  * `api.get_devices_list()['list']` -> `api.get_devices_list()`
  * `api.get_homes_list()['homelist']` -> `api.get_homes_list()`
  * `api.get_scenes_list(home_id)['scene_info_list']` -> `api.get_scenes_list(home_id)`
  * `api.get_consumable_items(home_id)['items']` -> `api.get_consumable_items(home_id)`

## [1.5.0](https://github.com/Do1e/mijia-api/compare/v1.4.5...v1.5.0) - 2025-06-19
### new feature
* Đổi tên `mijiaDevices` thành `mijiaDevice`

## [1.4.5](https://github.com/Do1e/mijia-api/compare/v1.4.4...v1.4.5) - 2025-06-16
### bugfix
* Xử lý lỗi liên quan khi không thể lấy thông tin người dùng trong quá trình đăng nhập

## [1.4.4](https://github.com/Do1e/mijia-api/compare/v1.4.3...v1.4.4) - 2025-06-14
### new feature
* `get_device_info` hỗ trợ mô tả tiếng Trung trong [https://home.miot-spec.com/](https://home.miot-spec.com/)
### bugfix
* CLI sửa lỗi phải đăng nhập trước khi thực hiện `get_device_info`
### improvement
* Tối ưu đầu ra log
* Cảnh báo sử dụng phương thức `login` được sửa đổi rõ ràng hơn

## [1.4.3](https://github.com/Do1e/mijia-api/compare/v1.4.2...v1.4.3) - 2025-05-22
### bugfix
* Đối với một số thiết bị đặc biệt, sửa TypeError của `get_device_info`

## [1.4.2](https://github.com/Do1e/mijia-api/compare/v1.4.1...v1.4.2) - 2025-05-19
### new feature
* `get_device_info`支持缓存结果以加速

## [1.4.1](https://github.com/Do1e/mijia-api/compare/v1.4.0...v1.4.1) - 2025-05-19
### new feature
* cli支持`--run`以使用自然语言描述需求，交给小爱音箱执行

## [1.4.0](https://github.com/Do1e/mijia-api/compare/v1.3.14...v1.4.0) - 2025-05-19
### new feature
* 新增`mijiaAPI`的cli支持，运行`mijiaAPI --help`查看帮助

## [1.3.14](https://github.com/Do1e/mijia-api/compare/v1.3.13...v1.3.14) - 2025-05-18
### bugfix
* `available`属性判断错误，始终返回False

## [1.3.13](https://github.com/Do1e/mijia-api/compare/v1.3.12...v1.3.13) - 2025-05-18
### new feature
* 新增从cookie中提取有效期并保存在凭据中
### improvement
* `available`属性根据有效期判断

## [1.3.12](https://github.com/Do1e/mijia-api/compare/v1.3.11...v1.3.12) - 2025-05-16
### improvement
* 简化`mijiaLogin`的初始化参数，根据`save_path`的值自动判断是否需要保存凭据
* 重构了对象初始化和方法的注释

## [1.3.11](https://github.com/Do1e/mijia-api/compare/v1.3.10...v1.3.11) - 2025-05-16
### bugfix
* 验证保存路径并确保在保存验证数据之前确保目录存在

## [1.3.10](https://github.com/Do1e/mijia-api/compare/v1.3.9...v1.3.10) - 2025-05-16
### improvement
* 使用logging模块替代print函数

## [1.3.9](https://github.com/Do1e/mijia-api/compare/v1.3.8...v1.3.9) - 2025-05-16
### new feature
* 新增用户个人信息查询
* 新增用户凭据的可选保存
### improvement
* 支持非tty的二维码打印
* 优化二维码图片的删除逻辑

## [1.3.8](https://github.com/Do1e/mijia-api/compare/v1.3.7...v1.3.8) - 2025-05-14
### improvement
* 新增了devices里所有方法的注释
* 新增了`mijiaDevice`实例化时的断言检查
* 新增了操作失败时的错误提示抛出与错误代码的详情
* 优化了`mijiaDevice`实例化时的内部变量的赋值逻辑
* 优化了多处代码的可读性与简洁性
### bugfix
* 修复多处由于数据类型更新而引发的警告

## [1.3.7](https://github.com/Do1e/mijia-api/compare/v1.3.6...v1.3.7) - 2025-05-14
### new feature
* 新增自定义`run_action`参数，`in`等python关键字，可在前面加上下划线`_`
* `mijiaDevice`支持传入设备名称(米家中自定义的名称)进行初始化
