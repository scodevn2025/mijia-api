from datetime import datetime
from typing import Union, Optional

import requests
import requests.cookies

from .consts import defaultUA
from .utils import post_data


class mijiaAPI(object):
    def __init__(self, auth_data: dict):
        """
        Khởi tạo đối tượng mijiaAPI.

        Args:
            auth_data (dict): Từ điển chứa thông tin ủy quyền, phải bao gồm 'userId', 'deviceId', 'ssecurity' và 'serviceToken'.

        Raises:
            Exception: Ném ra ngoại lệ khi dữ liệu ủy quyền không đầy đủ.
        """
        if any(k not in auth_data for k in ['userId', 'deviceId', 'ssecurity', 'serviceToken']):
            raise Exception('Dữ liệu ủy quyền không hợp lệ')
        self.userId = auth_data['userId']
        self.ssecurity = auth_data['ssecurity']
        self.session = requests.Session()
        self.expireTime = auth_data.get('expireTime', None)
        self.session.headers.update({
            'User-Agent': defaultUA,
            'x-xiaomi-protocal-flag-cli': 'PROTOCAL-HTTP2',
            'Cookie': f'PassportDeviceId={auth_data["deviceId"]};'
                      f'userId={auth_data["userId"]};'
                      f'serviceToken={auth_data["serviceToken"]};',
        })

    @staticmethod
    def _post_process(data: dict) -> Union[list, bool]:
        if data['code'] != 0:
            raise Exception(f'Lấy dữ liệu thất bại, {data["message"]}')
        return data['result']

    @property
    def available(self) -> bool:
        """
        Kiểm tra API có khả dụng hay không.

        Returns:
            bool: API khả dụng trả về True, ngược lại trả về False.
        """
        if self.expireTime:
            expire_time = datetime.strptime(self.expireTime, '%Y-%m-%d %H:%M:%S')
            if expire_time < datetime.now():
                return False
            return True
        return False

    def get_devices_list(self) -> list:
        """
        Lấy danh sách thiết bị.

        Returns:
            dict: Danh sách thiết bị.
        """
        uri = '/home/home_device_list'
        home_list = self.get_homes_list()
        devices = []
        for home in home_list:
            start_did = ''
            has_more = True
            while has_more:
                data = {
                    "home_owner": home['uid'],
                    "home_id": int(home['id']),
                    "limit": 200,
                    "start_did": start_did,
                    "get_split_device": True,
                    "support_smart_home": True,
                    "get_cariot_device": True,
                    "get_third_device": True
                }
                ret = self._post_process(post_data(self.session, self.ssecurity, uri, data))
                if ret and ret.get('device_info'):
                    devices.extend(ret['device_info'])
                    start_did = ret.get('max_did', '')
                    has_more = ret.get('has_more', False) and start_did != ''
                else:
                    has_more = False
        return devices

    def get_homes_list(self) -> list:
        """
        Lấy danh sách nhà.

        Returns:
            list: Danh sách nhà, bao gồm thông tin phòng.
        """
        uri = '/v2/homeroom/gethome_merged'
        data = {"fg": True, "fetch_share": True, "fetch_share_dev": True, "limit": 300, "app_ver": 7}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))['homelist']

    def get_scenes_list(self, home_id: str) -> list:
        """
        Lấy danh sách cảnh.

        Được thiết lập trong ứng dụng Mijia qua "Thêm -> Điều khiển thủ công".

        Args:
            home_id (str): ID nhà, lấy từ get_homes_list.

        Returns:
            list: Danh sách cảnh.
        """
        uri = '/appgateway/miot/appsceneservice/AppSceneService/GetSceneList'
        data = {"home_id": home_id}
        ret = self._post_process(post_data(self.session, self.ssecurity, uri, data))
        if ret and 'scene_info_list' in ret:
            return ret['scene_info_list']
        return []

    def run_scene(self, scene_id: str) -> bool:
        """
        Chạy cảnh.

        Args:
            scene_id (str): ID cảnh, lấy từ get_scenes_list.

        Returns:
            bool: Kết quả thao tác.
        """
        uri = '/appgateway/miot/appsceneservice/AppSceneService/RunScene'
        data = {"scene_id": scene_id, "trigger_key": "user.click"}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def get_consumable_items(self, home_id: str, owner_id: Optional[int] = None) -> list:
        """
        Lấy danh sách vật tư tiêu hao.

        Args:
            home_id (str): ID nhà, lấy từ get_homes_list.
            owner_id (str, optional): ID người dùng, mặc định là None, nếu `home_id` là nhà chia sẻ, cần cung cấp owner_id.

        Returns:
            list: Danh sách vật tư tiêu hao.
        """
        uri = '/v2/home/standard_consumable_items'
        data = {"home_id": int(home_id), "owner_id": int(owner_id) if owner_id else self.userId}
        ret = self._post_process(post_data(self.session, self.ssecurity, uri, data))
        if ret and 'items' in ret:
            return ret['items']
        return []

    def get_devices_prop(self, data: list) -> list:
        """
        Lấy thuộc tính thiết bị.

        Args:
            data (list): Danh sách yêu cầu thuộc tính thiết bị, mỗi mục là từ điển chứa các key sau:
                - did: ID thiết bị, lấy từ get_devices_list
                - siid: ID dịch vụ, lấy từ https://home.miot-spec.com/spec/{model}, model từ get_devices_list
                - piid: ID thuộc tính, lấy từ https://home.miot-spec.com/spec/{model}, model từ get_devices_list

                Ví dụ(yeelink.light.lamp4):
                [
                    {"did": "1234567890", "siid": 2, "piid": 2}, # Lấy độ sáng
                    {"did": "1234567890", "siid": 2, "piid": 3}, # Lấy nhiệt độ màu
                ]

        Returns:
            list: Danh sách thông tin thuộc tính thiết bị.
        """
        uri = '/miotspec/prop/get'
        data = {"params": data}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def set_devices_prop(self, data: list) -> list:
        """
        Thiết lập thuộc tính thiết bị.

        Args:
            data (list): Danh sách thiết lập thuộc tính thiết bị, mỗi mục là từ điển chứa các key sau:
                - did: ID thiết bị, lấy từ get_devices_list
                - siid: ID dịch vụ, lấy từ https://home.miot-spec.com/spec/{model}, model từ get_devices_list
                - piid: ID thuộc tính, lấy từ https://home.miot-spec.com/spec/{model}, model từ get_devices_list
                - value: Giá trị cần thiết lập

                Ví dụ(yeelink.light.lamp4):
                [
                    {"did": "1234567890", "siid": 2, "piid": 2, "value": 50},  # Thiết lập độ sáng 50%
                    {"did": "1234567890", "siid": 2, "piid": 3, "value": 2700} # Thiết lập nhiệt độ màu 2700K
                ]

        Returns:
            list: Kết quả thao tác.
        """
        uri = '/miotspec/prop/set'
        data = {"params": data}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def run_action(self, data: dict) -> dict:
        """
        执行设备动作。

        Args:
            data (dict): 动作请求，包含以下键：
                - did: 设备ID，从get_devices_list获取
                - siid: 服务ID，从 https://home.miot-spec.com/spec/{model} 获取，model从get_devices_list获取
                - aiid: 动作ID，从 https://home.miot-spec.com/spec/{model} 获取，model从get_devices_list获取
                - value: 参数列表

                示例(xiaomi.feeder.pi2001)：
                {"did": "1234567890", "siid": 2, "aiid": 1, "value": [2]} # 远程喂食2份

        Returns:
            dict: 操作结果。
        """
        uri = '/miotspec/action'
        data = {"params": data}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def get_statistics(self, data: dict) -> list:
        """
        获取设备的统计信息。

        Args:
            data (dict): 请求参数，包含以下键：
                - did: 设备ID，从get_devices_list获取
                - key: siid.piid，表示要获取统计数据的属性
                - data_type: 统计类型，可选值包括：
                    - 'stat_hour_v3': 按小时统计
                    - 'stat_day_v3': 按天统计
                    - 'stat_week_v3': 按周统计
                    - 'stat_month_v3': 按月统计
                - limit: 返回的最大条目数，可选参数
                - time_start: 开始时间戳，单位为秒
                - time_end: 结束时间戳，单位为秒

                示例(lumi.acpartner.mcn04 的 power-consumption)：
                {
                    "did": "1234567890",
                    "key": "7.1",
                    "data_type": "stat_month_v3",
                    "limit": 24,
                    "time_start": 1685548800,
                    "time_end": 1750694400,
                } # 2023-06-01 00:00:00 到 2025-06-24 00:00:00 的月度统计数据

        Returns:
            list: 统计信息列表。
        """
        uri = '/v2/user/statistics'
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))
