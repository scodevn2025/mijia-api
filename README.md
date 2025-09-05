# mijiaAPI

API cho thiết bị Xiaomi Mijia, cho phép điều khiển trực tiếp các thiết bị Mijia bằng mã lệnh.

[![GitHub](https://img.shields.io/badge/GitHub-Do1e%2Fmijia--api-blue)](https://github.com/Do1e/mijia-api)
[![PyPI](https://img.shields.io/badge/PyPI-mijiaAPI-blue)](https://pypi.org/project/mijiaAPI/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

## ⚠️ Lưu ý quan trọng

**Từ phiên bản v1.5.0 trở đi, dự án này chứa nhiều thay đổi không tương thích ngược!**

Nếu bạn đang nâng cấp từ phiên bản cũ, vui lòng xem [CHANGELOG.md](CHANGELOG.md) để hiểu chi tiết về các thay đổi và hướng dẫn di chuyển.

## Cài đặt

### Cài đặt từ PyPI (Khuyến nghị)

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
Nếu bạn sử dụng Arch Linux hoặc các distro dựa trên Arch, có thể cài đặt qua AUR:

```bash
yay -S python-mijia-api
```

## Sử dụng

Ví dụ sử dụng có thể tham khảo trong thư mục `demos`, dưới đây là hướng dẫn sử dụng cơ bản.

### Đăng nhập

`mijiaLogin`: Đăng nhập tài khoản Xiaomi để lấy thông tin cần thiết như `userId`, `ssecurity`, `deviceId`, `serviceToken` để điều khiển thiết bị.

#### Phương thức đăng nhập:

* `QRlogin() -> dict`: Đăng nhập bằng mã QR (Khuyến nghị)
  - Hiển thị mã QR trực tiếp trên terminal hỗ trợ tty
  - Hoặc xem file `qr.png` được tạo trong thư mục hiện tại
  
* `login(username: str, password: str) -> dict`: Đăng nhập bằng tài khoản và mật khẩu
  - **Lưu ý: Phương thức này rất có thể cần xác thực bằng mã điện thoại, khuyến nghị ưu tiên sử dụng đăng nhập mã QR**


### API

`mijiaAPI`: Triển khai API cốt lõi, được khởi tạo bằng thông tin trả về từ `mijiaLogin`.

#### Khởi tạo và kiểm tra trạng thái:

* `__init__(auth_data: dict)`: Khởi tạo đối tượng API
  - `auth_data` phải chứa 4 trường `userId`, `deviceId`, `ssecurity`, `serviceToken`

* `available -> bool`: Kiểm tra xem `auth_data` được truyền vào có hợp lệ không, dựa trên trường `expireTime` trong `auth_data`

#### Lấy và điều khiển thiết bị & cảnh:

Các phương thức dưới đây có thể tham khảo ví dụ trong [demos/test_apis.py](demos/test_apis.py).

* `get_devices_list() -> list`: Lấy danh sách thiết bị
* `get_homes_list() -> list`: Lấy danh sách nhà (bao gồm thông tin phòng)
* `get_scenes_list(home_id: str) -> list`: Lấy danh sách cảnh thủ công
  - Được thiết lập trong ứng dụng Mijia qua **Mijia → Thêm → Điều khiển thủ công**
* `run_scene(scene_id: str) -> bool`: Chạy cảnh được chỉ định
* `get_consumable_items(home_id: str, owner_id: Optional[int] = None) -> list`: Lấy thông tin vật tư tiêu hao của thiết bị, nếu là nhà chia sẻ, cần chỉ định thêm tham số `owner_id`
* `get_devices_prop(data: list) -> list`: Lấy thuộc tính thiết bị
* `set_devices_prop(data: list) -> list`: Thiết lập thuộc tính thiết bị
* `run_action(data: dict) -> dict`: Thực hiện hành động cụ thể của thiết bị
* `get_statistics(data: dict) -> list`: Lấy thông tin thống kê của thiết bị, như lượng điện tiêu thụ hàng tháng của máy lạnh, tham khảo [demos/test_get_statistics.py](demos/test_get_statistics.py)

Các tham số liên quan đến thuộc tính và hành động của thiết bị (`siid`, `piid`, `aiid`) có thể được tra cứu từ [Thư viện sản phẩm Mijia](https://home.miot-spec.com):
* Truy cập `https://home.miot-spec.com/spec/{model}` (`model` được lấy từ danh sách thiết bị)
* Ví dụ: [Đèn bàn Mijia 1S](https://home.miot-spec.com/spec/yeelink.light.lamp4)

**Lưu ý**: Không phải tất cả phương thức được liệt kê trong thư viện sản phẩm Mijia đều có thể sử dụng, cần tự kiểm tra và xác minh.

### 设备信息获取

使用 `get_device_info()` 函数可从米家规格平台在线获取设备属性字典：

```python
from mijiaAPI import get_device_info

# 获取设备规格信息
device_info = get_device_info('yeelink.light.lamp4')  # 米家台灯 1S 的 model
```

详细示例：[demos/test_get_device_info.py](demos/test_get_device_info.py)

### 设备控制封装

`mijiaDevice`：基于 `mijiaAPI` 的高级封装，提供更简便的设备控制方式。

#### 初始化：

```python
mijiaDevice(api: mijiaAPI, dev_info: dict = None, dev_name: str = None, did: str = None, sleep_time: float = 0.5)
```

* `api`：已初始化的 `mijiaAPI` 对象
* `dev_info`：设备属性字典（可选）
  - 可通过 `get_device_info()` 函数获取
  - **注意**：如果提供了 `dev_info`，则不需要提供 `dev_name`
* `dev_name`：设备名称，用于自动查找设备（可选）
  - 例如：`dev_name='台灯'`，会自动查找名称包含“台灯”的设备
  - **注意**：如果提供了 `dev_name`，则不需要提供 `dev_info` 和 `did`
* `did`：设备ID，便于直接通过属性名访问（可选）
  - 如果初始化时未提供，无法使用属性样式访问，需要使用 `get()` 和 `set()` 方法指定 `did`
  - 使用 `dev_name` 初始化时，`did` 会自动获取
* `sleep_time`：属性操作间隔时间，单位秒（默认0.5秒）
  - **重要**：设置属性后立即获取可能不符合预期，需设置适当延迟

#### Điều khiển bằng phương thức:

* `set(name: str, value: Union[bool, int, float, str], did: Optional[str] = None) -> bool`: Thiết lập thuộc tính thiết bị
* `get(name: str, did: Optional[str] = None) -> Union[bool, int, float, str]`: Lấy thuộc tính thiết bị
* `run_action(name: str, did: Optional[str] = None, value: Optional[Union[list, tuple]] = None, **kwargs) -> bool`: Thực hiện hành động thiết bị

#### Truy cập kiểu thuộc tính:

Cần cung cấp `did` khi khởi tạo hoặc sử dụng khởi tạo `dev_name`

```python
# Ví dụ: điều khiển đèn bàn
device = mijiaDevice(api, dev_name='Đèn bàn')
device.on = True                 # Bật đèn
device.brightness = 60           # Thiết lập độ sáng
current_temp = device.color_temperature  # Lấy nhiệt độ màu
```

Quy tắc tên thuộc tính: Sử dụng dấu gạch dưới thay thế dấu gạch ngang (như `color-temperature` thành `color_temperature`)

#### Ví dụ:

* Sử dụng ngôn ngữ tự nhiên để điều khiển loa thông minh Xiao Ai: [demos/test_devices_wifispeaker.py](demos/test_devices_wifispeaker.py)
* Điều khiển trực tiếp đèn bàn thông qua thuộc tính: [demos/test_devices_v2_light.py](demos/test_devices_v2_light.py)

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
  --list_homes          Liệt kê danh sách nhà
  --list_scenes         Liệt kê danh sách cảnh
  --list_consumable_items
                        Liệt kê danh sách vật tư tiêu hao
  --run_scene SCENE_ID/SCENE_NAME [SCENE_ID/SCENE_NAME ...]
                        Chạy cảnh, chỉ định ID cảnh hoặc tên cảnh
  --get_device_info DEVICE_MODEL
                        Lấy thông tin thiết bị, chỉ định model thiết bị, sử dụng --list_devices để lấy trước
  --run PROMPT          Sử dụng ngôn ngữ tự nhiên mô tả nhu cầu của bạn, nếu bạn có loa thông minh Xiao Ai
  --wifispeaker_name WIFISPEAKER_NAME
                        Chỉ định tên loa thông minh Xiao Ai, mặc định là loa Xiao Ai đầu tiên được tìm thấy
  --quiet               Loa Xiao Ai thực hiện im lặng
```

```
> python -m mijiaAPI get --help
> mijiaAPI get --help
usage: __main__.py get [-h] [-p AUTH_PATH] --dev_name DEV_NAME --prop_name PROP_NAME

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api-auth.json
  --dev_name DEV_NAME   Tên thiết bị, chỉ định tên được thiết lập trong ứng dụng Mijia
  --prop_name PROP_NAME
                        Tên thuộc tính, sử dụng --get_device_info để lấy trước
```

```
> python -m mijiaAPI set --help
> mijiaAPI set --help
usage: __main__.py set [-h] [-p AUTH_PATH] --dev_name DEV_NAME --prop_name PROP_NAME --value VALUE

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api-auth.json
  --dev_name DEV_NAME   Tên thiết bị, chỉ định tên được thiết lập trong ứng dụng Mijia
  --prop_name PROP_NAME
                        Tên thuộc tính, sử dụng --get_device_info để lấy trước
  --value VALUE         Giá trị thuộc tính cần thiết lập
```

Hoặc sử dụng trực tiếp `uvx` bỏ qua bước cài đặt:

```bash
uvx mijiaAPI --help
```

#### Ví dụ:

```bash
mijiaAPI -l # Liệt kê tất cả thiết bị Mijia
mijiaAPI --list_homes # Liệt kê danh sách nhà
mijiaAPI --list_scenes # Liệt kê danh sách cảnh
mijiaAPI --list_consumable_items # Liệt kê danh sách vật tư tiêu hao
mijiaAPI --run_scene SCENE_ID/SCENE_NAME # Chạy cảnh, chỉ định ID cảnh hoặc tên cảnh
mijiaAPI --get_device_info DEVICE_MODEL # Lấy thông tin thiết bị, chỉ định model thiết bị, sử dụng --list_devices để lấy trước
mijiaAPI get --dev_name DEV_NAME --prop_name PROP_NAME # Lấy thuộc tính thiết bị
mijiaAPI set --dev_name DEV_NAME --prop_name PROP_NAME --value VALUE # Thiết lập thuộc tính thiết bị
mijiaAPI --run Thời tiết ngày mai như thế nào
mijiaAPI --run Bật đèn bàn và điều chỉnh độ sáng tối đa --quiet
```

## Lời cảm ơn

* [janzlan/mijia-api](https://gitee.com/janzlan/mijia-api/tree/master)

## Giấy phép mã nguồn mở

Dự án này sử dụng giấy phép mã nguồn mở [GPL-3.0](LICENSE).

## Tuyên bố miễn trừ trách nhiệm

* Dự án này chỉ dành cho mục đích học tập và trao đổi, không được sử dụng cho mục đích thương mại, nếu có vi phạm bản quyền vui lòng liên hệ để xóa
* Người dùng phải tự chịu trách nhiệm về mọi hậu quả phát sinh từ việc sử dụng dự án này
* Nhà phát triển không chịu trách nhiệm về bất kỳ thiệt hại trực tiếp hoặc gián tiếp nào phát sinh từ việc sử dụng dự án này
