# mijiaAPI

API cho thiết bị Xiaomi Mijia, có thể sử dụng mã để điều khiển trực tiếp các thiết bị Mijia.

[![GitHub](https://img.shields.io/badge/GitHub-Do1e%2Fmijia--api-blue)](https://github.com/Do1e/mijia-api)
[![PyPI](https://img.shields.io/badge/PyPI-mijiaAPI-blue)](https://pypi.org/project/mijiaAPI/)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-green.svg)](https://opensource.org/licenses/GPL-3.0)

## ⚠️ Lưu ý quan trọng

**Kể từ phiên bản v1.5.0, dự án này chứa nhiều thay đổi đột phá!**

Nếu bạn đang nâng cấp từ phiên bản cũ, vui lòng xem [CHANGELOG.md](CHANGELOG.md) để hiểu chi tiết về các thay đổi và hướng dẫn di chuyển.

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
# Hoặc `pip install -e .` cho chế độ chỉnh sửa
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

`mijiaLogin`: Đăng nhập tài khoản Xiaomi, lấy thông tin cần thiết để điều khiển thiết bị như `userId`, `ssecurity`, `deviceId`, `serviceToken`.

#### Phương thức đăng nhập:

* `QRlogin() -> dict`: Đăng nhập bằng quét mã QR (khuyến nghị)
  - Hiển thị mã QR trực tiếp trên terminal hỗ trợ tty
  - Hoặc xem file `qr.png` được tạo trong thư mục hiện tại
  
* `login(username: str, password: str) -> dict`: Đăng nhập bằng tài khoản mật khẩu
  - **Lưu ý: Phương thức này có khả năng cao cần xác thực bằng mã điện thoại, khuyến nghị ưu tiên sử dụng đăng nhập mã QR**


### API

`mijiaAPI`: Triển khai API cốt lõi, sử dụng thông tin trả về từ `mijiaLogin` để khởi tạo.

#### Khởi tạo và kiểm tra trạng thái:

* `__init__(auth_data: dict)`: Khởi tạo đối tượng API
  - `auth_data` phải chứa 4 trường `userId`, `deviceId`, `ssecurity`, `serviceToken`

* `available -> bool`: Kiểm tra xem `auth_data` được truyền vào có hợp lệ hay không, dựa trên trường `expireTime` trong `auth_data`

#### Lấy và điều khiển thiết bị & cảnh:

Các phương thức dưới đây có thể tham khảo ví dụ trong [demos/test_apis.py](demos/test_apis.py).

* `get_devices_list() -> list`: Lấy danh sách thiết bị
* `get_homes_list() -> list`: Lấy danh sách gia đình (bao gồm thông tin phòng)
* `get_scenes_list(home_id: str) -> list`: Lấy danh sách cảnh thủ công
  - Thiết lập trong ứng dụng Mijia thông qua **Mijia→Thêm→Điều khiển thủ công**
* `run_scene(scene_id: str) -> bool`: Chạy cảnh được chỉ định
* `get_consumable_items(home_id: str, owner_id: Optional[int] = None) -> list`: Lấy thông tin vật tư tiêu hao của thiết bị, nếu là gia đình được chia sẻ, cần chỉ định thêm tham số `owner_id`
* `get_devices_prop(data: list) -> list`: Lấy thuộc tính thiết bị
* `set_devices_prop(data: list) -> list`: Thiết lập thuộc tính thiết bị
* `run_action(data: dict) -> dict`: Thực hiện hành động cụ thể của thiết bị
* `get_statistics(data: dict) -> list`: Lấy thông tin thống kê của thiết bị, như lượng điện tiêu thụ hàng tháng của điều hòa, tham khảo [demos/test_get_statistics.py](demos/test_get_statistics.py)

Các tham số liên quan đến thuộc tính và hành động của thiết bị (`siid`, `piid`, `aiid`) có thể tra cứu từ [Thư viện sản phẩm Mijia](https://home.miot-spec.com):
* Truy cập `https://home.miot-spec.com/spec/{model}` (`model` lấy từ danh sách thiết bị)
* Ví dụ: [Đèn bàn Mijia 1S](https://home.miot-spec.com/spec/yeelink.light.lamp4)

**Lưu ý**: Không phải tất cả các phương thức được liệt kê trong thư viện sản phẩm Mijia đều có thể sử dụng, cần tự kiểm tra và xác minh.

### Lấy thông tin thiết bị

Sử dụng hàm `get_device_info()` có thể lấy từ điển thuộc tính thiết bị từ nền tảng thông số kỹ thuật Mijia trực tuyến:

```python
from mijiaAPI import get_device_info

# Lấy thông tin thông số kỹ thuật thiết bị
device_info = get_device_info('yeelink.light.lamp4')  # model của đèn bàn Mijia 1S
```

Ví dụ chi tiết: [demos/test_get_device_info.py](demos/test_get_device_info.py)

### Gói điều khiển thiết bị

`mijiaDevice`: Gói bọc cấp cao dựa trên `mijiaAPI`, cung cấp cách điều khiển thiết bị đơn giản hơn.

#### Khởi tạo:

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

#### 使用方法控制：

* `set(name: str, value: Union[bool, int, float, str], did: Optional[str] = None) -> bool`：设置设备属性
* `get(name: str, did: Optional[str] = None) -> Union[bool, int, float, str]`：获取设备属性
* `run_action(name: str, did: Optional[str] = None, value: Optional[Union[list, tuple]] = None, **kwargs) -> bool`：执行设备动作

#### 属性样式访问：

需在初始化时提供 `did` 或者使用 `dev_name` 初始化

```python
# 示例：控制台灯
device = mijiaDevice(api, dev_name='台灯')
device.on = True                 # 打开灯
device.brightness = 60           # 设置亮度
current_temp = device.color_temperature  # 获取色温
```

属性名规则：使用下划线替代连字符（如 `color-temperature` 变为 `color_temperature`）

#### 示例：

* 使用自然语言让小爱音箱执行：[demos/test_devices_wifispeaker.py](demos/test_devices_wifispeaker.py)
* 通过属性直接控制台灯：[demos/test_devices_v2_light.py](demos/test_devices_v2_light.py)

### Mijia API CLI
`mijiaAPI` 还提供了一个命令行工具，可以直接在终端中使用。

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
    get                 获取设备属性
    set                 设置设备属性

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        认证文件保存路径，默认保存在~/.config/mijia-api-auth.json
  -l, --list_devices    列出所有米家设备
  --list_homes          列出家庭列表
  --list_scenes         列出场景列表
  --list_consumable_items
                        列出耗材列表
  --run_scene SCENE_ID/SCENE_NAME [SCENE_ID/SCENE_NAME ...]
                        运行场景，指定场景ID或名称
  --get_device_info DEVICE_MODEL
                        获取设备信息，指定设备model，先使用 --list_devices 获取
  --run PROMPT          使用自然语言描述你的需求，如果你有小爱音箱的话
  --wifispeaker_name WIFISPEAKER_NAME
                        指定小爱音箱名称，默认是获取到的第一个小爱音箱
  --quiet               小爱音箱静默执行
```

```
> python -m mijiaAPI get --help
> mijiaAPI get --help
usage: __main__.py get [-h] [-p AUTH_PATH] --dev_name DEV_NAME --prop_name PROP_NAME

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        认证文件保存路径，默认保存在~/.config/mijia-api-auth.json
  --dev_name DEV_NAME   设备名称，指定为米家APP中设定的名称
  --prop_name PROP_NAME
                        属性名称，先使用 --get_device_info 获取
```

```
> python -m mijiaAPI set --help
> mijiaAPI set --help
usage: __main__.py set [-h] [-p AUTH_PATH] --dev_name DEV_NAME --prop_name PROP_NAME --value VALUE

options:
  -h, --help            show this help message and exit
  -p AUTH_PATH, --auth_path AUTH_PATH
                        认证文件保存路径，默认保存在~/.config/mijia-api-auth.json
  --dev_name DEV_NAME   设备名称，指定为米家APP中设定的名称
  --prop_name PROP_NAME
                        属性名称，先使用 --get_device_info 获取
  --value VALUE         需要设定的属性值
```

或者直接使用`uvx`忽略安装步骤：

```bash
uvx mijiaAPI --help
```

#### 示例：

```bash
mijiaAPI -l # 列出所有米家设备
mijiaAPI --list_homes # 列出家庭列表
mijiaAPI --list_scenes # 列出场景列表
mijiaAPI --list_consumable_items # 列出耗材列表
mijiaAPI --run_scene SCENE_ID/SCENE_NAME # 运行场景，指定场景ID或名称
mijiaAPI --get_device_info DEVICE_MODEL # 获取设备信息，指定设备model，先使用 --list_devices 获取
mijiaAPI get --dev_name DEV_NAME --prop_name PROP_NAME # 获取设备属性
mijiaAPI set --dev_name DEV_NAME --prop_name PROP_NAME --value VALUE # 设置设备属性
mijiaAPI --run 明天天气如何
mijiaAPI --run Thời tiết ngày mai như thế nào
mijiaAPI --run Bật đèn bàn và điều chỉnh độ sáng tối đa --quiet
```

## Lời cảm ơn

* [janzlan/mijia-api](https://gitee.com/janzlan/mijia-api/tree/master)

## Giấy phép mã nguồn mở

Dự án này sử dụng giấy phép mã nguồn mở [GPL-3.0](LICENSE).

## Tuyên bố miễn trách nhiệm

* Dự án này chỉ dành cho mục đích học tập và trao đổi, không được sử dụng cho mục đích thương mại, nếu có vi phạm bản quyền vui lòng liên hệ để xóa
* Bất kỳ hậu quả nào phát sinh từ việc người dùng sử dụng dự án này, người dùng cần tự chịu rủi ro
* Nhà phát triển không chịu trách nhiệm về bất kỳ thiệt hại trực tiếp hoặc gián tiếp nào phát sinh từ việc sử dụng dự án này
