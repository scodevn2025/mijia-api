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
            prop_dict (dict): Dictionary thuộc tính.

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
            str: Tên, mô tả, loại, quyền đọc/ghi, đơn vị và phạm vi của thuộc tính.
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
            act_dict (dict): Dictionary hành động.
        """
        self.name = act_dict['name']
        self.desc = act_dict['description']
        self.method = act_dict['method']

    def __str__(self):
        """
        返回动作的字符串表示。

        Returns:
            str: 动作的名称和描述。
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

        Nếu không cung cấp thông tin thiết bị, sẽ lấy thông tin thiết bị dựa trên tên thiết bị. Nếu cả hai đều không được cung cấp, sẽ ném ngoại lệ.
        Nếu cung cấp cả thông tin thiết bị và tên thiết bị, sẽ ưu tiên thông tin thiết bị.

        Args:
            api (mijiaAPI): Đối tượng Mijia API.
            dev_info (dict, optional): Dictionary thông tin thiết bị, lấy từ get_device_info. Mặc định là None.
            dev_name (str, optional): Tên thiết bị, lấy từ get_devices_list. Mặc định là None.
            did (str, optional): ID thiết bị, nếu không chỉ định, cần chỉ định khi gọi get/set. Mặc định là None.
            sleep_time ([int, float], optional): Thời gian khoảng cách gọi thuộc tính thiết bị. Mặc định là 0.5 giây.

        Raises:
            RuntimeError: Nếu cả dev_info và dev_name đều không được cung cấp.
            ValueError: Nếu không tìm thấy thiết bị được chỉ định hoặc tìm thấy nhiều thiết bị cùng tên.

        Note:
            - Nếu cung cấp cả dev_info và dev_name, sẽ ưu tiên dev_info.
            - Nếu chỉ cung cấp dev_name, sẽ tự động lấy thông tin thiết bị dựa trên tên.
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
        返回设备的字符串表示。

        Returns:
            str: 设备的属性和动作列表。
        """
        prop_list_str = '\n'.join(filter(None, (str(v) for k, v in self.prop_list.items() if '_' not in k)))
        action_list_str = '\n'.join(map(str, self.action_list.values()))
        return (f"{self.name} ({self.model})\n"
                f"Properties:\n{prop_list_str if prop_list_str else 'No properties available'}\n"
                f"Actions:\n{action_list_str if action_list_str else 'No actions available'}")

    def set(self, name: str, value: Union[bool, int, float, str], did: Optional[str] = None) -> bool:
        """
        设置设备的属性值。

        Args:
            name (str): 属性名称。
            value (Union[bool, int, float, str]): 属性值。
            did (str, optional): 设备ID。如未指定，则使用实例化时的did。默认为None。

        Returns:
            bool: 执行结果（True/False）。

        Raises:
            ValueError: 如果属性不存在、属性为只读或值无效。
            RuntimeError: 如果设置属性失败。
        """
        if did is None:
            did = self.did
        if did is None:
            raise ValueError('请指定设备ID (did)')
        if name not in self.prop_list:
            raise ValueError(f'不支持的属性: {name}, 可用属性: {list(self.prop_list.keys())}')
        prop = self.prop_list[name]
        if 'w' not in prop.rw:
            raise ValueError(f'属性 {name} 不可写入')
        if prop.value_list:
            if value not in [item['value'] for item in prop.value_list]:
                raise ValueError(f'无效值: {value}, 请使用 {prop.value_list}')
        if prop.type == 'bool':
            if isinstance(value, str):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value in ['0', '1']:
                    value = bool(int(value))
                else:
                    raise ValueError(f'无效布尔值: {value}')
            elif isinstance(value, int):
                if value == 0:
                    value = False
                elif value == 1:
                    value = True
                else:
                    raise ValueError(f'无效布尔值: {value}')
            elif not isinstance(value, bool):
                raise ValueError(f'无效布尔值: {value}')
        elif prop.type in ['int', 'uint']:
            value = int(value)
            if prop.range:
                if value < prop.range[0] or value > prop.range[1]:
                    raise ValueError(f'{value} 超出数值范围, 应该在 {prop.range[:2]} 之间')
                if len(prop.range) >= 3 and prop.range[2] != 1:
                    if (value - prop.range[0]) % prop.range[2] != 0:
                        raise ValueError(
                            f'无效的值: {value}, 应该在范围 {prop.range[:2]} 内且步长为 {prop.range[2]}')
        elif prop.type == 'float':
            value = float(value)
            if prop.range:
                if value < prop.range[0] or value > prop.range[1]:
                    raise ValueError(f'{value} 超出数值范围, 应该在 {prop.range[:2]} 之间')
                if len(prop.range) >= 3 and isinstance(prop.range[2], int):
                    if int(value - prop.range[0]) % prop.range[2] != 0:
                        raise ValueError(
                            f'无效的值: {value}, 应该在范围 {prop.range[:2]} 内且步长为 {prop.range[2]}')
        elif prop.type == 'string':
            if not isinstance(value, str):
                raise ValueError(f'无效字符串值: {value}')
        else:
            raise ValueError(f'不支持的类型: {prop.type}, 可用类型: bool, int, uint, float, string')
        method = prop.method.copy()
        method['did'] = did
        method['value'] = value
        result = self.api.set_devices_prop([method])[0]
        if result['code'] != 0:
            raise RuntimeError(
                f"设置属性 {name} 失败, "
                f"错误码: {result['code']}, "
                f"错误信息: {ERROR_CODE.get(str(result['code']), '未知错误')}"
            )
        sleep(self.sleep_time)
        logger.debug(f"设置属性: {self.name} -> {name}, 值: {value}, 结果: {result}")
        return result['code'] == 0

    def get(self, name: str, did: Optional[str] = None) -> Union[bool, int, float, str]:
        """
        获取设备的属性值。

        Args:
            name (str): 属性名称。
            did (str, optional): 设备ID。如未指定，则使用实例化时的did。默认为None。

        Returns:
            Union[bool, int, float, str]: 属性值。

        Raises:
            ValueError: 如果未指定设备ID、属性不存在或属性为只写。
            RuntimeError: 如果获取属性失败。
        """
        if did is None:
            did = self.did
        if did is None:
            raise ValueError('请指定设备ID (did)')
        if name not in self.prop_list:
            raise ValueError(f'不支持的属性: {name}, 可用属性: {list(self.prop_list.keys())}')
        prop = self.prop_list[name]
        if 'r' not in prop.rw:
            raise ValueError(f'属性 {name} 不可读取')
        method = prop.method.copy()
        method['did'] = did
        result = self.api.get_devices_prop([method])[0]
        if result['code'] != 0:
            raise RuntimeError(
                f"获取属性 {name} 失败, "
                f"错误码: {result['code']}, "
                f"错误信息: {ERROR_CODE.get(str(result['code']), '未知错误')}"
            )
        sleep(self.sleep_time)
        logger.debug(f"获取属性: {self.name} -> {name}, 结果: {result}")
        return result['value']

    def __setattr__(self, name: str, value: Union[bool, int, float, str]) -> None:
        """
        设置设备的属性值（通过对象属性方式，需在实例化时指定did）。

        Args:
            name (str): 属性名称。
            value (Union[bool, int, float, str]): 属性值。

        Raises:
            RuntimeError: 如果设置属性失败。
        """
        if 'prop_list' in self.__dict__ and name in self.prop_list:
            if not self.set(name, value):
                raise RuntimeError(f'设置属性 {name} 失败')
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name: str) -> Union[bool, int, float, str]:
        """
        获取设备的属性值（通过对象属性方式，需在实例化时指定did）。

        Args:
            name (str): 属性名称。

        Returns:
            Union[bool, int, float, str]: 属性值。
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
        运行设备动作。

        Args:
            name (str): 动作名称。
            did (Optional[str], optional): 设备ID。如未指定，则使用实例化时的did。默认为None。
            value (Optional[Union[list, tuple]], optional): 动作参数。如动作不需要参数，则不需指定。默认为None。
            **kwargs: 其它动作参数，如智能音箱的in参数[run_action('execute-text-directive', _in=['空调调至26度', True])]。

        Returns:
            bool: 执行结果（True/False）。

        Raises:
            ValueError: 如果未指定设备ID、动作不存在或参数无效。
            RuntimeError: 如果运行动作失败。
        """
        if did is None:
            did = self.did
        if did is None:
            raise ValueError('请指定设备ID (did)')
        if name not in self.action_list:
            raise ValueError(f'不支持的动作: {name}, 可用动作: {list(self.action_list.keys())}')
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
                    raise ValueError(f'无效的参数: {k}. 请勿使用以下参数 ({", ".join(method.keys())})')
                method[k] = v
        result = self.api.run_action(method)
        if result['code'] != 0:
            raise RuntimeError(
                f"执行动作 {name} 失败, "
                f"错误码: {result['code']}, "
                f"错误信息: {ERROR_CODE.get(str(result['code']), '未知错误')}"
            )
        sleep(self.sleep_time)
        logger.debug(f"执行动作: {self.name} -> {name}, 结果: {result}")
        return result['code'] == 0


def get_device_info(device_model: str, cache_path: Optional[str] = os.path.join(os.path.expanduser("~"), ".config/mijia-api")) -> dict:
    """
    获取设备信息，用于初始化mijiaDevice对象。

    Args:
        device_model (str): 设备型号，从get_devices_list获取。
        cache_path (str, optional): 缓存文件路径。默认为~/.config/mijia-api，设置为None则不使用缓存。

    Returns:
        dict: 设备信息字典。

    Raises:
        RuntimeError: 如果获取设备信息失败。
    """
    if cache_path is not None:
        cache_file = os.path.join(cache_path, f'{device_model}.json')
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    response = requests.get(deviceURL + device_model)
    if response.status_code != 200:
        raise RuntimeError(f'获取设备信息失败')
    content = re.search(r'data-page="(.*?)">', response.text)
    if content is None:
        raise RuntimeError(f'获取设备信息失败')
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
