from datetime import datetime
from typing import Union, Optional

import requests
import requests.cookies

from .consts import defaultUA
from .utils import post_data


class mijiaAPI(object):
    def __init__(self, auth_data: dict):
        """
        Khởi tạo đối tượng **mijiaAPI**.

        Args:
            auth_data (dict): Từ điển chứa thông tin ủy quyền, bắt buộc phải có
            ``userId``, ``deviceId``, ``ssecurity`` và ``serviceToken``.

        Raises:
            Exception: Ném ra khi dữ liệu ủy quyền không đầy đủ.
        """
        if any(k not in auth_data for k in ['userId', 'deviceId', 'ssecurity', 'serviceToken']):
            raise Exception('授权数据无效')
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
            raise Exception(f'获取数据失败, {data["message"]}')
        return data['result']

    @property
    def available(self) -> bool:
        """
        Kiểm tra tính khả dụng của API.

        Returns:
            bool: ``True`` nếu API vẫn còn hiệu lực, ngược lại ``False``.
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
        Lấy danh sách "nhà".

        Returns:
            list: Danh sách nhà bao gồm thông tin phòng.
        """
        uri = '/v2/homeroom/gethome_merged'
        data = {"fg": True, "fetch_share": True, "fetch_share_dev": True, "limit": 300, "app_ver": 7}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))['homelist']

    def get_scenes_list(self, home_id: str) -> list:
        """
        Lấy danh sách kịch bản (scene).

        Các kịch bản được thiết lập trong ứng dụng Mi Home qua
        "Thêm -> Điều khiển thủ công".

        Args:
            home_id (str): ID của nhà, lấy từ ``get_homes_list``.

        Returns:
            list: Danh sách kịch bản.
        """
        uri = '/appgateway/miot/appsceneservice/AppSceneService/GetSceneList'
        data = {"home_id": home_id}
        ret = self._post_process(post_data(self.session, self.ssecurity, uri, data))
        if ret and 'scene_info_list' in ret:
            return ret['scene_info_list']
        return []

    def run_scene(self, scene_id: str) -> bool:
        """
        Chạy một kịch bản đã định nghĩa.

        Args:
            scene_id (str): ID của kịch bản, lấy từ ``get_scenes_list``.

        Returns:
            bool: Kết quả thực thi.
        """
        uri = '/appgateway/miot/appsceneservice/AppSceneService/RunScene'
        data = {"scene_id": scene_id, "trigger_key": "user.click"}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def get_consumable_items(self, home_id: str, owner_id: Optional[int] = None) -> list:
        """
        Lấy danh sách vật tư tiêu hao của thiết bị.

        Args:
            home_id (str): ID của nhà, lấy từ ``get_homes_list``.
            owner_id (str, optional): ID người dùng, cần thiết nếu ``home_id``
            thuộc nhà được chia sẻ.

        Returns:
            list: Danh sách vật tư.
        """
        uri = '/v2/home/standard_consumable_items'
        data = {"home_id": int(home_id), "owner_id": int(owner_id) if owner_id else self.userId}
        ret = self._post_process(post_data(self.session, self.ssecurity, uri, data))
        if ret and 'items' in ret:
            return ret['items']
        return []

    def get_devices_prop(self, data: list) -> list:
        """
        Lấy thuộc tính của thiết bị.

        Args:
            data (list): Danh sách yêu cầu thuộc tính, mỗi phần tử là một
            dict gồm các khóa:
                - did: ID thiết bị, lấy từ ``get_devices_list``
                - siid: ID dịch vụ, tra cứu tại https://home.miot-spec.com/spec/{model}
                - piid: ID thuộc tính, tra cứu tương tự

                Ví dụ (yeelink.light.lamp4):
                [
                    {"did": "1234567890", "siid": 2, "piid": 2}, # độ sáng
                    {"did": "1234567890", "siid": 2, "piid": 3}, # nhiệt độ màu
                ]

        Returns:
            list: Thông tin thuộc tính của thiết bị.
        """
        uri = '/miotspec/prop/get'
        data = {"params": data}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def set_devices_prop(self, data: list) -> list:
        """
        Thiết lập thuộc tính cho thiết bị.

        Args:
            data (list): Danh sách thuộc tính cần đặt, mỗi phần tử gồm:
                - did: ID thiết bị
                - siid: ID dịch vụ
                - piid: ID thuộc tính
                - value: Giá trị cần thiết lập

                Ví dụ (yeelink.light.lamp4):
                [
                    {"did": "1234567890", "siid": 2, "piid": 2, "value": 50},  # đặt độ sáng 50%
                    {"did": "1234567890", "siid": 2, "piid": 3, "value": 2700} # đặt nhiệt độ màu 2700K
                ]

        Returns:
            list: Kết quả thao tác.
        """
        uri = '/miotspec/prop/set'
        data = {"params": data}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def run_action(self, data: dict) -> dict:
        """
        Thực thi một hành động của thiết bị.

        Args:
            data (dict): Yêu cầu hành động với các khóa:
                - did: ID thiết bị
                - siid: ID dịch vụ
                - aiid: ID hành động
                - value: Danh sách tham số

                Ví dụ (xiaomi.feeder.pi2001):
                {"did": "1234567890", "siid": 2, "aiid": 1, "value": [2]}
                # cho ăn 2 phần từ xa

        Returns:
            dict: Kết quả hành động.
        """
        uri = '/miotspec/action'
        data = {"params": data}
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))

    def get_statistics(self, data: dict) -> list:
        """
        Lấy số liệu thống kê của thiết bị.

        Args:
            data (dict): Tham số yêu cầu gồm:
                - did: ID thiết bị
                - key: ``siid.piid`` chỉ ra thuộc tính cần thống kê
                - data_type: Loại thống kê, có thể là:
                    - 'stat_hour_v3': theo giờ
                    - 'stat_day_v3': theo ngày
                    - 'stat_week_v3': theo tuần
                    - 'stat_month_v3': theo tháng
                - limit: Số mục tối đa trả về
                - time_start: Thời điểm bắt đầu (timestamp, giây)
                - time_end: Thời điểm kết thúc (timestamp, giây)

                Ví dụ (lumi.acpartner.mcn04 - power-consumption):
                {
                    "did": "1234567890",
                    "key": "7.1",
                    "data_type": "stat_month_v3",
                    "limit": 24,
                    "time_start": 1685548800,
                    "time_end": 1750694400,
                } # Dữ liệu theo tháng từ 2023-06-01 đến 2025-06-24

        Returns:
            list: Danh sách dữ liệu thống kê.
        """
        uri = '/v2/user/statistics'
        return self._post_process(post_data(self.session, self.ssecurity, uri, data))
