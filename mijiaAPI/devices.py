from typing import Union, Optional
import json
import os
import re
import requests
from time import sleep
from .apis import mijiaAPI
from .code import ERROR_CODE
from .consts import deviceURL
from .logger import get_logger

logger = get_logger(__name__)

class DevProp(object):
    def __init__(self, prop_dict: dict):
        """
        Khởi tạo đối tượng thuộc tính.

        Args:
            prop_dict (dict): Từ điển thuộc tính.

        Raises:
            ValueError: Nếu loại thuộc tính không được hỗ trợ.
        """
        self.name = prop_dict['name']
        self.desc = prop_dict['description']
        self.type = prop_dict['type']
        if self.type not in ['bool', 'int', 'uint', 'float', 'string']:
            raise ValueError(f'Loại không được hỗ trợ: {self.type}, các loại có thể chọn: bool, int, uint, float, string')
        self.rw = prop_dict['rw']
        self.unit = prop_dict['unit']
        self.range = prop_dict['range']
        self.value_list = prop_dict.get('value-list', None)
        self.method = prop_dict['method']

    def __str__(self):
        """
        Trả về biểu diễn chuỗi của thuộc tính.

        Returns:
            str: Tên thuộc tính, mô tả, loại, quyền đọc/ghi, đơn vị và phạm vi.
        """
        lines = [
            f"  {self.name}: {self.desc}",
            f"    valuetype: {self.type}, rw: {self.rw}, unit: {self.unit}, range: {self.range}"
        ]

        if self.value_list:
            value_lines = [f"    {item['value']}: {item['description']}" for item in self.value_list]
            lines.extend(value_lines)

        return '\n'.join(lines)


class DevAction(object):
    def __init__(self, act_dict: dict):
        """
        Khởi tạo đối tượng hành động.

        Args:
            act_dict (dict): Từ điển hành động.
        """
        self.name = act_dict['name']
        self.desc = act_dict['description']
        self.method = act_dict['method']

    def __str__(self):
        """
        Trả về biểu diễn chuỗi của hành động.

        Returns:
            str: Tên và mô tả của hành động.
        """
        return f'  {self.name}: {self.desc}'


class mijiaDevice(object):
    def __init__(
            self,
            api: mijiaAPI,
            dev_info: Optional[dict] = None,
            dev_name: Optional[str] = None,
            did: Optional[str] = None,
            sleep_time: Optional[Union[int, float]] = 0.5
    ):
        """
        Khởi tạo đối tượng thiết bị.

        Nếu không cung cấp thông tin thiết bị, sẽ lấy thông tin thiết bị theo tên thiết bị. Nếu cả hai đều không được cung cấp, sẽ ném ra ngoại lệ.
        Nếu đồng thời cung cấp thông tin thiết bị và tên thiết bị, sẽ ưu tiên thông tin thiết bị.

        Args:
            api (mijiaAPI): Đối tượng Mijia API.
            dev_info (dict, optional): Từ điển thông tin thiết bị, lấy từ get_device_info. Mặc định là None.
            dev_name (str, optional): Tên thiết bị, lấy từ get_devices_list. Mặc định là None.
            did (str, optional): ID thiết bị, nếu không chỉ định, cần chỉ định khi gọi get/set. Mặc định là None.
            sleep_time ([int, float], optional): Khoảng thời gian gọi thuộc tính thiết bị. Mặc định là 0.5 giây.

        Raises:
            RuntimeError: Nếu cả dev_info và dev_name đều không được cung cấp.
            ValueError: Nếu không tìm thấy thiết bị được chỉ định hoặc tìm thấy nhiều thiết bị cùng tên.

        Note:
            - Nếu đồng thời cung cấp dev_info và dev_name, sẽ ưu tiên dev_info.
            - Nếu chỉ cung cấp dev_name, sẽ tự động lấy thông tin thiết bị theo tên.
            - Nếu chỉ cung cấp dev_info, sẽ sử dụng trực tiếp thông tin đó.
        """
        if dev_info is None and dev_name is None:
            raise RuntimeError("Phải cung cấp một trong các tham số 'dev_info' hoặc 'dev_name'.")
        if dev_info is not None and dev_name is not None:
            logger.warning("Đã cung cấp cả 'dev_info' và 'dev_name'. Sẽ sử dụng 'dev_info' để khởi tạo.")

        self.api = api
        if dev_info is None:
            devices_list = self.api.get_devices_list()
            matches = [device for device in devices_list if device['name'] == dev_name]
            if not matches:
                raise ValueError(f"Không tìm thấy thiết bị {dev_name}")
            elif len(matches) > 1:
                raise ValueError(f"Tìm thấy nhiều thiết bị có tên {dev_name}")
            else:
                dev_info = get_device_info(matches[0]['model'])
                did = matches[0]['did']
        self.name = dev_info['name']
        self.model = dev_info['model']

        self.prop_list = {}
        for prop in dev_info.get('properties', []):
            prop_obj = DevProp(prop)
            name = prop['name']
            self.prop_list[name] = prop_obj
            if '-' in name:
                self.prop_list[name.replace('-', '_')] = prop_obj

        self.action_list = {
            act['name']: DevAction(act)
            for act in dev_info.get('actions', [])
        }
        self.did = did
        self.sleep_time = sleep_time

    def __str__(self) -> str:
        """
        Trả về biểu diễn chuỗi của thiết bị.

        Returns:
            str: Danh sách thuộc tính và hành động của thiết bị.
        """
        prop_list_str = '\n'.join(filter(None, (str(v) for k, v in self.prop_list.items() if '_' not in k)))
        action_list_str = '\n'.join(map(str, self.action_list.values()))
        return (f"{self.name} ({self.model})\n"
                f"Properties:\n{prop_list_str if prop_list_str else 'No properties available'}\n"
                f"Actions:\n{action_list_str if action_list_str else 'No actions available'}")

    def set(self, name: str, value: Union[bool, int, float, str], did: Optional[str] = None) -> bool:
        """
        Thiết lập giá trị thuộc tính của thiết bị.

        Args:
            name (str): Tên thuộc tính.
            value (Union[bool, int, float, str]): Giá trị thuộc tính.
            did (str, optional): ID thiết bị. Nếu không chỉ định, sẽ sử dụng did khi khởi tạo. Mặc định là None.

        Returns:
            bool: Kết quả thực hiện (True/False).

        Raises:
            ValueError: Nếu thuộc tính không tồn tại, thuộc tính chỉ đọc hoặc giá trị không hợp lệ.
            RuntimeError: Nếu thiết lập thuộc tính thất bại.
        """
        if did is None:
            did = self.did
        if did is None:
            raise ValueError('Vui lòng chỉ định ID thiết bị (did)')
        if name not in self.prop_list:
            raise ValueError(f'Thuộc tính không được hỗ trợ: {name}, thuộc tính có sẵn: {list(self.prop_list.keys())}')
        prop = self.prop_list[name]
        if 'w' not in prop.rw:
            raise ValueError(f'Thuộc tính {name} không thể ghi')
        if prop.value_list:
            if value not in [item['value'] for item in prop.value_list]:
                raise ValueError(f'Giá trị không hợp lệ: {value}, vui lòng sử dụng {prop.value_list}')
        if prop.type == 'bool':
            if isinstance(value, str):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value in ['0', '1']:
                    value = bool(int(value))
                else:
                    raise ValueError(f'Giá trị boolean không hợp lệ: {value}')
            elif isinstance(value, int):
                if value == 0:
                    value = False
                elif value == 1:
                    value = True
                else:
                    raise ValueError(f'Giá trị boolean không hợp lệ: {value}')
            elif not isinstance(value, bool):
                raise ValueError(f'Giá trị boolean không hợp lệ: {value}')
        elif prop.type in ['int', 'uint']:
            value = int(value)
            if prop.range:
                if value < prop.range[0] or value > prop.range[1]:
                    raise ValueError(f'{value} vượt quá phạm vi số, phải nằm trong khoảng {prop.range[:2]}')
                if len(prop.range) >= 3 and prop.range[2] != 1:
                    if (value - prop.range[0]) % prop.range[2] != 0:
                        raise ValueError(
                            f'Giá trị không hợp lệ: {value}, phải nằm trong phạm vi {prop.range[:2]} và có bước nhảy {prop.range[2]}')
        elif prop.type == 'float':
            value = float(value)
            if prop.range:
                if value < prop.range[0] or value > prop.range[1]:
                    raise ValueError(f'{value} vượt quá phạm vi số, phải nằm trong khoảng {prop.range[:2]}')
                if len(prop.range) >= 3 and isinstance(prop.range[2], int):
                    if int(value - prop.range[0]) % prop.range[2] != 0:
                        raise ValueError(
                            f'Giá trị không hợp lệ: {value}, phải nằm trong phạm vi {prop.range[:2]} và có bước nhảy {prop.range[2]}')
        elif prop.type == 'string':
            if not isinstance(value, str):
                raise ValueError(f'Giá trị chuỗi không hợp lệ: {value}')
        else:
            raise ValueError(f'Loại không được hỗ trợ: {prop.type}, loại có thể sử dụng: bool, int, uint, float, string')
        method = prop.method.copy()
        method['did'] = did
        method['value'] = value
        result = self.api.set_devices_prop([method])[0]
        if result['code'] != 0:
            raise RuntimeError(
                f"Thiết lập thuộc tính {name} thất bại, "
                f"mã lỗi: {result['code']}, "
                f"thông báo lỗi: {ERROR_CODE.get(str(result['code']), 'lỗi không xác định')}"
            )
        sleep(self.sleep_time)
        logger.debug(f"Thiết lập thuộc tính: {self.name} -> {name}, giá trị: {value}, kết quả: {result}")
        return result['code'] == 0

    def get(self, name: str, did: Optional[str] = None) -> Union[bool, int, float, str]:
        """
        Lấy giá trị thuộc tính của thiết bị.

        Args:
            name (str): Tên thuộc tính.
            did (str, optional): ID thiết bị. Nếu không chỉ định, sẽ sử dụng did khi khởi tạo. Mặc định là None.

        Returns:
            Union[bool, int, float, str]: Giá trị thuộc tính.

        Raises:
            ValueError: Nếu không chỉ định ID thiết bị, thuộc tính không tồn tại hoặc thuộc tính chỉ ghi.
            RuntimeError: Nếu lấy thuộc tính thất bại.
        """
        if did is None:
            did = self.did
        if did is None:
            raise ValueError('Vui lòng chỉ định ID thiết bị (did)')
        if name not in self.prop_list:
            raise ValueError(f'Thuộc tính không được hỗ trợ: {name}, thuộc tính có sẵn: {list(self.prop_list.keys())}')
        prop = self.prop_list[name]
        if 'r' not in prop.rw:
            raise ValueError(f'Thuộc tính {name} không thể đọc')
        method = prop.method.copy()
        method['did'] = did
        result = self.api.get_devices_prop([method])[0]
        if result['code'] != 0:
            raise RuntimeError(
                f"Lấy thuộc tính {name} thất bại, "
                f"mã lỗi: {result['code']}, "
                f"thông báo lỗi: {ERROR_CODE.get(str(result['code']), 'lỗi không xác định')}"
            )
        sleep(self.sleep_time)
        logger.debug(f"Lấy thuộc tính: {self.name} -> {name}, kết quả: {result}")
        return result['value']

    def __setattr__(self, name: str, value: Union[bool, int, float, str]) -> None:
        """
        Thiết lập giá trị thuộc tính của thiết bị (thông qua phương thức thuộc tính đối tượng, cần chỉ định did khi khởi tạo).

        Args:
            name (str): Tên thuộc tính.
            value (Union[bool, int, float, str]): Giá trị thuộc tính.

        Raises:
            RuntimeError: Nếu thiết lập thuộc tính thất bại.
        """
        if 'prop_list' in self.__dict__ and name in self.prop_list:
            if not self.set(name, value):
                raise RuntimeError(f'Thiết lập thuộc tính {name} thất bại')
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Union[bool, int, float, str]:
        """
        Lấy giá trị thuộc tính của thiết bị (thông qua phương thức thuộc tính đối tượng, cần chỉ định did khi khởi tạo).

        Args:
            name (str): Tên thuộc tính.

        Returns:
            Union[bool, int, float, str]: Giá trị thuộc tính.
        """
        if 'prop_list' in self.__dict__ and name in self.prop_list:
            return self.get(name)
        else:
            return super().__getattr__(name)

    def run_action(
            self,
            name: str,
            did: Optional[str] = None,
            value: Optional[Union[list, tuple]] = None,
            **kwargs
    ) -> bool:
        """
        Chạy hành động thiết bị.

        Args:
            name (str): Tên hành động.
            did (Optional[str], optional): ID thiết bị. Nếu không chỉ định, sẽ sử dụng did khi khởi tạo. Mặc định là None.
            value (Optional[Union[list, tuple]], optional): Tham số hành động. Nếu hành động không cần tham số, thì không cần chỉ định. Mặc định là None.
            **kwargs: Các tham số hành động khác, như tham số in của loa thông minh [run_action('execute-text-directive', _in=['Điều hòa 26 độ', True])].

        Returns:
            bool: Kết quả thực hiện (True/False).

        Raises:
            ValueError: Nếu không chỉ định ID thiết bị, hành động không tồn tại hoặc tham số không hợp lệ.
            RuntimeError: Nếu chạy hành động thất bại.
        """
        if did is None:
            did = self.did
        if did is None:
            raise ValueError('Vui lòng chỉ định ID thiết bị (did)')
        if name not in self.action_list:
            raise ValueError(f'Hành động không được hỗ trợ: {name}, hành động có sẵn: {list(self.action_list.keys())}')
        act = self.action_list[name]
        method = act.method.copy()
        method['did'] = did
        if value is not None:
            method['value'] = value
        if kwargs:
            for k, v in kwargs.items():
                if k.startswith("_"):
                    k = k[1:]
                if k in method:
                    raise ValueError(f'Tham số không hợp lệ: {k}. Vui lòng không sử dụng các tham số sau ({", ".join(method.keys())})')
                method[k] = v
        result = self.api.run_action(method)
        if result['code'] != 0:
            raise RuntimeError(
                f"Thực hiện hành động {name} thất bại, "
                f"mã lỗi: {result['code']}, "
                f"thông báo lỗi: {ERROR_CODE.get(str(result['code']), 'lỗi không xác định')}"
            )
        sleep(self.sleep_time)
        logger.debug(f"Thực hiện hành động: {self.name} -> {name}, kết quả: {result}")
        return result['code'] == 0


def get_device_info(device_model: str, cache_path: Optional[str] = os.path.join(os.path.expanduser("~"), ".config/mijia-api")) -> dict:
    """
    Lấy thông tin thiết bị, dùng để khởi tạo đối tượng mijiaDevice.

    Args:
        device_model (str): Model thiết bị, lấy từ get_devices_list.
        cache_path (str, optional): Đường dẫn file cache. Mặc định là ~/.config/mijia-api, thiết lập None thì không sử dụng cache.

    Returns:
        dict: Từ điển thông tin thiết bị.

    Raises:
        RuntimeError: Nếu lấy thông tin thiết bị thất bại.
    """
    if cache_path is not None:
        cache_file = os.path.join(cache_path, f'{device_model}.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    response = requests.get(deviceURL + device_model)
    if response.status_code != 200:
        raise RuntimeError(f'Lấy thông tin thiết bị thất bại')
    content = re.search(r'data-page="(.*?)">', response.text)
    if content is None:
        raise RuntimeError(f'Lấy thông tin thiết bị thất bại')
    content = content.group(1)
    content = json.loads(content.replace('&quot;', '"'))

    if content['props']['product']:
        name = content['props']['product']['name']
        model = content['props']['product']['model']
    else:
        name = content['props']['spec']['name']
        model = device_model
    result = {
        'name': name,
        'model': model,
        'properties': [],
        'actions': []
    }
    services = content['props']['spec']['services']

    properties_name = []
    actions_name = []
    for siid in services:
        if 'properties' in services[siid]:
            for piid in services[siid]['properties']:
                prop = services[siid]['properties'][piid]
                if prop['format'].startswith('int'):
                    prop_type = 'int'
                elif prop['format'].startswith('uint'):
                    prop_type = 'uint'
                else:
                    prop_type = prop['format']
                item = {
                    'name': prop['name'],
                    'description': f"{prop.get('description', '')} / {prop.get('desc_zh_cn', '')}",
                    'type': prop_type,
                    'rw': ''.join([
                        'r' if 'read' in prop['access'] else '',
                        'w' if 'write' in prop['access'] else ''
                    ]),
                    'unit': prop.get('unit', None),
                    'range': prop.get('value-range', None),
                    'value-list': prop.get('value-list', None),
                    'method': {
                        'siid': int(siid),
                        'piid': int(piid)
                    }
                }
                if item['name'] in properties_name:
                    item["name"] = f'{services[siid]["name"]}-{item["name"]}'
                properties_name.append(item['name'])
                result['properties'].append({k: None if v == 'none' else v for k, v in item.items()})
        if 'actions' in services[siid]:
            for aiid in services[siid]['actions']:
                act = services[siid]['actions'][aiid]
                if act['name'] in actions_name:
                    act['name'] = f'{services[siid]["name"]}-{act["name"]}'
                actions_name.append(act['name'])
                result['actions'].append({
                    'name': act['name'],
                    'description': f"{act.get('description', '')} / {act.get('desc_zh_cn', '')}",
                    'method': {
                        'siid': int(siid),
                        'aiid': int(aiid)
                    }
                })
    if cache_path is not None:
        cache_file = os.path.join(cache_path, f'{device_model}.json')
        os.makedirs(cache_path, exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    return result
