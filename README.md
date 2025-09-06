# mijiaAPI

API Python để điều khiển các thiết bị trong hệ sinh thái **Xiaomi Mijia**.

[![GitHub](https://img.shields.io/badge/GitHub-Do1e%2Fmijia--api-blue)](https://github.com/Do1e/mijia-api)
[![PyPI](https://img.shields.io/badge/PyPI-mijiaAPI-blue)](https://pypi.org/project/mijiaAPI/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

## ⚠️ Lưu ý quan trọng

**Từ phiên bản v1.5.0 trở đi dự án có nhiều thay đổi phá vỡ tương thích.**
Nếu bạn đang nâng cấp từ phiên bản cũ hãy đọc kỹ [CHANGELOG.md](CHANGELOG.md).

## Cài đặt

### Từ PyPI (khuyến nghị)

```bash
pip install mijiaAPI
```

### Cài từ mã nguồn

```bash
git clone https://github.com/scodevn2025/mijia-api.git
cd mijia-api
pip install .
# hoặc `pip install -e .` để cài dạng editable
```

Sử dụng poetry:

```bash
poetry install
```

### AUR

Nếu dùng Arch Linux có thể cài qua AUR:

```bash
yay -S python-mijia-api
```

## Sử dụng

Các ví dụ đầy đủ nằm trong thư mục `demos`. Dưới đây là hướng dẫn cơ bản.

### Đăng nhập

`mijiaLogin` hỗ trợ đăng nhập tài khoản Mi:

* `QRlogin() -> dict`: quét mã QR đăng nhập.
* `login(username, password) -> dict`: đăng nhập bằng tài khoản/mật khẩu.

### API chính

`mijiaAPI` sử dụng dữ liệu trả về từ `mijiaLogin` để điều khiển thiết bị.
Một số phương thức:

* `get_devices_list()` – lấy danh sách thiết bị.
* `get_homes_list()` – lấy danh sách nhà/phòng.
* `get_scenes_list(home_id)` – lấy các kịch bản thủ công.
* `run_scene(scene_id)` – thực thi kịch bản.
* `get_devices_prop(data)` / `set_devices_prop(data)` – lấy/đặt thuộc tính.
* `run_action(data)` – thực thi hành động cụ thể.

### Bao gói thiết bị

`mijiaDevice` cung cấp giao diện thân thiện hơn cho việc điều khiển. Ví dụ:

```python
device = mijiaDevice(api, dev_name='Đèn')
device.on = True
device.brightness = 60
```

### CLI

Có thể sử dụng ngay trên dòng lệnh:

```bash
mijiaAPI --help
mijiaAPI get --dev_name Tên --prop_name Thuộc_tính
mijiaAPI set --dev_name Tên --prop_name Thuộc_tính --value Giá_trị
```

## Giao diện đồ họa

Thư mục `demos` chứa ví dụ `gui.py` minh họa đăng nhập bằng QR và liệt kê thiết
bị thông qua Tkinter.

## Ghi công

* [janzlan/mijia-api](https://gitee.com/janzlan/mijia-api/tree/master)

## Giấy phép

Phát hành theo giấy phép [GPL-3.0](LICENSE).

## Miễn trừ trách nhiệm

* Dự án chỉ phục vụ mục đích học tập, không sử dụng cho mục đích thương mại.
* Người dùng tự chịu trách nhiệm với mọi rủi ro khi sử dụng.
* Tác giả không chịu trách nhiệm cho bất kỳ thiệt hại nào phát sinh.

