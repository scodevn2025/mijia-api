# mijiaAPI

API cho thiết bị Xiaomi Mijia, cho phép điều khiển trực tiếp thiết bị Mijia bằng mã lệnh.

[![GitHub](https://img.shields.io/badge/GitHub-Do1e%2Fmijia--api-blue)](https://github.com/Do1e/mijia-api)
[![PyPI](https://img.shields.io/badge/PyPI-mijiaAPI-blue)](https://pypi.org/project/mijiaAPI/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

## ⚠️ Lưu ý quan trọng

**Từ phiên bản v1.5.0 trở đi, dự án này chứa nhiều thay đổi breaking changes!**

Nếu bạn đang nâng cấp từ phiên bản cũ, vui lòng xem [CHANGELOG.md](CHANGELOG.md) để hiểu chi tiết về nội dung thay đổi và hướng dẫn di chuyển.

## Cài đặt

### Cài đặt từ PyPI (khuyến nghị)

```bash
pip install mijiaAPI
```

### Cài đặt từ mã nguồn

```bash
git clone https://github.com/Do1e/mijia-api.git
cd mijia-api
pip install .
# Hoặc `pip install -e .` cho chế độ có thể chỉnh sửa
```

Hoặc sử dụng poetry:

```bash
poetry install
```

### aur
Nếu bạn sử dụng Arch Linux hoặc các bản phân phối dựa trên Arch, có thể cài đặt thông qua AUR:

```bash
yay -S python-mijia-api
```

## Sử dụng

Các ví dụ sử dụng có thể tham khảo mã mẫu trong thư mục `demos`, dưới đây là hướng dẫn sử dụng cơ bản.

### Đăng nhập

`mijiaLogin`: Đăng nhập tài khoản Xiaomi, lấy thông tin cần thiết để điều khiển thiết bị như `userId`, `ssecurity`, `deviceId`, `serviceToken`, v.v.

#### Phương thức đăng nhập:

* `QRlogin() -> dict`: Đăng nhập bằng mã QR (khuyến nghị)
  - Hiển thị mã QR trực tiếp trên terminal hỗ trợ tty
  - Hoặc xem file `qr.png` được tạo trong thư mục hiện tại
  
* `login(username: str, password: str) -> dict`: Đăng nhập bằng tài khoản mật khẩu
  - **Lưu ý: Phương thức này có khả năng cao cần xác minh mã OTP điện thoại, khuyến nghị ưu tiên sử dụng đăng nhập mã QR**


### API

`mijiaAPI`: Triển khai API cốt lõi, sử dụng thông tin trả về từ `mijiaLogin` để khởi tạo.

#### Khởi tạo và kiểm tra trạng thái:

* `__init__(auth_data: dict)`: Khởi tạo đối tượng API
  - `auth_data` phải chứa bốn trường `userId`, `deviceId`, `ssecurity`, `serviceToken`

* `available -> bool`: Kiểm tra `auth_data` được truyền vào có hợp lệ hay không, dựa trên trường `expireTime` trong `auth_data`

#### Lấy thông tin và điều khiển thiết bị & kịch bản:

Các phương thức dưới đây có thể tham khảo ví dụ trong [demos/test_apis.py](demos/test_apis.py).

* `get_devices_list() -> list`: Lấy danh sách thiết bị
* `get_homes_list() -> list`: Lấy danh sách gia đình (bao gồm thông tin phòng)
* `get_scenes_list(home_id: str) -> list`: Lấy danh sách kịch bản thủ công
  - Thiết lập trong ứng dụng Mijia thông qua **Mijia → Thêm → Điều khiển thủ công**
* `run_scene(scene_id: str) -> bool`: Chạy kịch bản được chỉ định
* `get_consumable_items(home_id: str, owner_id: Optional[int] = None) -> list`: Lấy thông tin vật tư tiêu hao của thiết bị, nếu là gia đình chia sẻ, cần chỉ định thêm tham số `owner_id`
* `get_devices_prop(data: list) -> list`: Lấy thuộc tính thiết bị
* `set_devices_prop(data: list) -> list`: Thiết lập thuộc tính thiết bị
* `run_action(data: dict) -> dict`: Thực hiện hành động cụ thể của thiết bị
* `get_statistics(data: dict) -> list`: Lấy thông tin thống kê của thiết bị, như lượng điện tiêu thụ hàng tháng của điều hòa, tham khảo [demos/test_get_statistics.py](demos/test_get_statistics.py)

Các tham số liên quan đến thuộc tính và hành động của thiết bị (`siid`, `piid`, `aiid`) có thể truy vấn từ [Thư viện sản phẩm Mijia](https://home.miot-spec.com):
* Truy cập `https://home.miot-spec.com/spec/{model}` (`model` lấy từ danh sách thiết bị)
* Ví dụ: [Đèn bàn Mijia 1S](https://home.miot-spec.com/spec/yeelink.light.lamp4)

**Lưu ý**: Không phải tất cả phương thức được liệt kê trong thư viện sản phẩm Mijia đều có thể sử dụng, cần tự kiểm tra và xác minh.

### Lấy thông tin thiết bị

Sử dụng hàm `get_device_info()` có thể lấy từ nền tảng đặc tả Mijia trực tuyến dictionary thuộc tính thiết bị:

```python
from mijiaAPI import get_device_info

# Lấy thông tin đặc tả thiết bị
device_info = get_device_info('yeelink.light.lamp4')  # model của Đèn bàn Mijia 1S
```

Ví dụ chi tiết: [demos/test_get_device_info.py](demos/test_get_device_info.py)

### Đóng gói điều khiển thiết bị

`mijiaDevice`: Đóng gói cấp cao dựa trên `mijiaAPI`, cung cấp cách điều khiển thiết bị thuận tiện hơn.

#### Khởi tạo:

```python
mijiaDevice(api: mijiaAPI, dev_info: dict = None, dev_name: str = None, did: str = None, sleep_time: float = 0.5)
```

* `api`: Đối tượng `mijiaAPI` đã được khởi tạo
* `dev_info`: Dictionary thuộc tính thiết bị (tùy chọn)
  - Có thể lấy thông qua hàm `get_device_info()`
  - **Lưu ý**: Nếu đã cung cấp `dev_info`, thì không cần cung cấp `dev_name`
* `dev_name`: Tên thiết bị, dùng để tự động tìm thiết bị (tùy chọn)
  - 例如：`dev_name='台灯'`，会自动查找名称包含“台灯”的设备
  - **Lưu ý**: Nếu đã cung cấp `dev_name`, thì không cần cung cấp `dev_info` và `did`
* `did`: ID thiết bị, thuận tiện cho việc truy cập trực tiếp thông qua tên thuộc tính (tùy chọn)
  - Nếu không cung cấp khi khởi tạo, không thể sử dụng kiểu truy cập thuộc tính, cần sử dụng phương thức `get()` và `set()` chỉ định `did`
  - Khi khởi tạo bằng `dev_name`, `did` sẽ được lấy tự động
* `sleep_time`: Thời gian khoảng cách thao tác thuộc tính, đơn vị giây (mặc định 0.5 giây)
  - **Quan trọng**: Lấy thuộc tính ngay sau khi thiết lập có thể không đúng như mong đợi, cần thiết lập độ trễ phù hợp

#### Sử dụng phương thức điều khiển:

* `set(name: str, value: Union[bool, int, float, str], did: Optional[str] = None) -> bool`: Thiết lập thuộc tính thiết bị
* `get(name: str, did: Optional[str] = None) -> Union[bool, int, float, str]`: Lấy thuộc tính thiết bị
* `run_action(name: str, did: Optional[str] = None, value: Optional[Union[list, tuple]] = None, **kwargs) -> bool`: Thực hiện hành động thiết bị

#### Truy cập kiểu thuộc tính:

Cần cung cấp `did` khi khởi tạo hoặc sử dụng `dev_name` để khởi tạo

```python
# Ví dụ: Điều khiển đèn bàn
device = mijiaDevice(api, dev_name='台灯')
device.on = True                 # Bật đèn
device.brightness = 60           # Thiết lập độ sáng
current_temp = device.color_temperature  # Lấy nhiệt độ màu
```

Quy tắc tên thuộc tính: Sử dụng dấu gạch dưới thay thế dấu gạch ngang (như `color-temperature` thành `color_temperature`)

#### Ví dụ:

* Sử dụng ngôn ngữ tự nhiên để XiaoAi thực hiện: [demos/test_devices_wifispeaker.py](demos/test_devices_wifispeaker.py)
* Điều khiển đèn bàn trực tiếp thông qua thuộc tính: [demos/test_devices_v2_light.py](demos/test_devices_v2_light.py)

### Mijia API CLI
`mijiaAPI` cũng cung cấp một công cụ dòng lệnh, có thể sử dụng trực tiếp trong terminal.

```
> python -m mijiaAPI --help
> mijiaAPI --help
usage: mijiaAPI [-h] [-p AUTH_PATH] [-l] [--list_homes] [--list_scenes] [--list_consumable_items]
                [--run_scene SCENE_ID/SCENE_NAME [SCENE_ID/SCENE_NAME ...]] [--get_device_info DEVICE_MODEL] [--run PROMPT]
                [--wifispeaker_name WIFISPEAKER_NAME] [--quiet]
                {get,set} ...

Mijia API CLI

positional arguments:
  {get,set}
    get                 Lấy thuộc tính thiết bị
    set                 Thiết lập thuộc tính thiết bị

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api-auth.json
  -l, --list_devices    Liệt kê tất cả thiết bị Mijia
  --list_homes          Liệt kê danh sách gia đình
  --list_scenes         Liệt kê danh sách kịch bản
  --list_consumable_items
                        Liệt kê danh sách vật tư tiêu hao
  --run_scene SCENE_ID/SCENE_NAME [SCENE_ID/SCENE_NAME ...]
                        Chạy kịch bản, chỉ định ID kịch bản hoặc tên
  --get_device_info DEVICE_MODEL
                        Lấy thông tin thiết bị, chỉ định model thiết bị, sử dụng --list_devices trước để lấy
  --run PROMPT          Sử dụng ngôn ngữ tự nhiên mô tả nhu cầu của bạn, nếu bạn có loa thông minh XiaoAi
  --wifispeaker_name WIFISPEAKER_NAME
                        Chỉ định tên loa thông minh XiaoAi, mặc định là loa đầu tiên được tìm thấy
  --quiet               Loa thông minh XiaoAi thực hiện im lặng
```

```
> python -m mijiaAPI get --help
> mijiaAPI get --help
usage: __main__.py get [-h] [-p AUTH_PATH] --dev_name DEV_NAME --prop_name PROP_NAME

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api-auth.json
  --dev_name DEV_NAME   Tên thiết bị, chỉ định theo tên đã đặt trong ứng dụng Mijia
  --prop_name PROP_NAME
                        Tên thuộc tính, sử dụng --get_device_info trước để lấy
```

```
> python -m mijiaAPI set --help
> mijiaAPI set --help
usage: __main__.py set [-h] [-p AUTH_PATH] --dev_name DEV_NAME --prop_name PROP_NAME --value VALUE

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api-auth.json
  --dev_name DEV_NAME   Tên thiết bị, chỉ định theo tên đã đặt trong ứng dụng Mijia
  --prop_name PROP_NAME
                        Tên thuộc tính, sử dụng --get_device_info trước để lấy
  --value VALUE         Giá trị thuộc tính cần thiết lập
```

Hoặc sử dụng trực tiếp `uvx` bỏ qua bước cài đặt:

```bash
uvx mijiaAPI --help
```

#### Ví dụ:

```bash
mijiaAPI -l # Liệt kê tất cả thiết bị Mijia
mijiaAPI --list_homes # Liệt kê danh sách gia đình
mijiaAPI --list_scenes # Liệt kê danh sách kịch bản
mijiaAPI --list_consumable_items # Liệt kê danh sách vật tư tiêu hao
mijiaAPI --run_scene SCENE_ID/SCENE_NAME # Chạy kịch bản, chỉ định ID kịch bản hoặc tên
mijiaAPI --get_device_info DEVICE_MODEL # Lấy thông tin thiết bị, chỉ định model thiết bị, sử dụng --list_devices trước để lấy
mijiaAPI get --dev_name DEV_NAME --prop_name PROP_NAME # Lấy thuộc tính thiết bị
mijiaAPI set --dev_name DEV_NAME --prop_name PROP_NAME --value VALUE # Thiết lập thuộc tính thiết bị
mijiaAPI --run 明天天气如何
mijiaAPI --run 打开台灯并将亮度调至最大 --quiet
```

## Lời cảm ơn

* [janzlan/mijia-api](https://gitee.com/janzlan/mijia-api/tree/master)

## Giấy phép mã nguồn mở

Dự án này sử dụng giấy phép mã nguồn mở [GPL-3.0](LICENSE).

## Tuyên bố miễn trừ trách nhiệm

* Dự án này chỉ dành cho mục đích học tập và trao đổi, không được sử dụng cho mục đích thương mại, nếu có vi phạm bản quyền vui lòng liên hệ để xóa
* Người dùng sử dụng dự án này phải tự chịu rủi ro cho bất kỳ hậu quả nào phát sinh
* Nhà phát triển không chịu trách nhiệm về bất kỳ thiệt hại trực tiếp hoặc gián tiếp nào phát sinh từ việc sử dụng dự án này
