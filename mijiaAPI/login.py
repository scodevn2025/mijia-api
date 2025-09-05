import hashlib
import json
import os
import random
import re
import string
import time
from datetime import datetime, timedelta
from typing import Optional
from urllib import parse

import requests
from qrcode import QRCode

from .logger import get_logger
from .consts import msgURL, loginURL, qrURL, accountURL, defaultUA

logger = get_logger(__name__)

class LoginError(Exception):
    def __init__(self, code: int, message: str):
        """
        Khởi tạo ngoại lệ lỗi đăng nhập.

        Args:
            code (int): Mã lỗi.
            message (str): Thông báo lỗi.
        """
        self.code = code
        self.message = message
        super().__init__(f'Error code: {code}, message: {message}')


class mijiaLogin(object):
    def __init__(self, save_path: Optional[str] = None):
        """
        Khởi tạo đối tượng đăng nhập Mijia.

        Args:
            save_path (str, optional): Đường dẫn lưu dữ liệu xác thực. Mặc định là None.
        """
        self.auth_data = None
        self.save_path = save_path

        self.deviceId = ''.join(random.sample(string.digits + string.ascii_letters, 16))
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': defaultUA,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cookie': f'deviceId={self.deviceId}; sdkVersion=3.4.1'
        })

    def _get_index(self) -> dict[str, str]:
        """
        Lấy dữ liệu trang index.

        Returns:
            dict[str, str]: Từ điển chứa ID thiết bị và các tham số cần thiết khác.

        Raises:
            LoginError: Ném ra khi yêu cầu trang index thất bại.
        """
        ret = self.session.get(msgURL)
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Lấy trang index thất bại, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        data = {'deviceId': self.deviceId}
        data.update({
            k: v for k, v in ret_data.items()
            if k in ['qs', '_sign', 'callback', 'location']
        })
        return data

    def _get_account_info(self, user_id: str) -> dict[str, str]:
        """
        Lấy thông tin tài khoản.

        Args:
            user_id (str): ID người dùng.

        Returns:
            dict[str, str]: Từ điển chứa thông tin tài khoản.

        Raises:
            LoginError: Ném ra khi lấy thông tin tài khoản thất bại.
        """
        try:
            ret = self.session.get(accountURL + str(user_id))
            if ret.status_code != 200:
                raise LoginError(ret.status_code, f'Lấy trang tài khoản thất bại, {ret.text}')
            data = json.loads(ret.text[11:])['data']
        except (KeyError, json.JSONDecodeError) as e:
            data = {}
        return data

    @staticmethod
    def _extract_latest_gmt_datetime(data: dict) -> datetime:
        """
        Trích xuất thời gian hết hạn và chuyển đổi sang múi giờ Trung Quốc.

        Args:
            data (dict): Dữ liệu thông tin đăng nhập người dùng, chứa các cặp key-value có thời gian GMT.

        Returns:
            datetime: Thời gian múi giờ Trung Quốc sau khi chuyển đổi.

        Raises:
            LoginError: Nếu không tìm thấy key thời gian GMT hoặc phân tích thất bại, ném ra lỗi đăng nhập.
        """

        gmt_time_keys = [
            k for k in data.keys() if
            isinstance(k, str) and re.match(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2} GMT', k)
        ]

        if not gmt_time_keys:
            raise LoginError(-1, 'Không tìm thấy key thời gian GMT trong cookie')
        parsed_times = [datetime.strptime(k, '%d-%b-%Y %H:%M:%S GMT') for k in gmt_time_keys]
        latest_utc_time = max(parsed_times)
        china_time = latest_utc_time + timedelta(hours=8)

        # [FIXME] Thực tế thời gian hết hạn ở đây không chính xác, thời gian hết hạn thực tế có thể lớn hơn thời gian lấy được ở đây
        #         serviceToken duy nhất được sử dụng trong cookie không có thời gian hết hạn
        return china_time

    def _save_auth(self) -> None:
        """
        Lưu dữ liệu xác thực vào file.

        Nếu đã thiết lập đường dẫn lưu và có dữ liệu xác thực, sẽ lưu dưới định dạng JSON vào đường dẫn đã chỉ định.
        """
        if self.save_path is not None and self.auth_data is not None:
            if not os.path.isabs(self.save_path):
                self.save_path = os.path.abspath(self.save_path)
            if os.path.exists(self.save_path) and not os.path.isfile(self.save_path):
                raise ValueError(f'[{self.save_path}] không phải là file')
            if not os.path.exists(os.path.dirname(self.save_path)):
                os.makedirs(os.path.dirname(self.save_path))
            with open(self.save_path, 'w') as f:
                json.dump(self.auth_data, f, indent=2)
            logger.info(f'File xác thực đã được lưu tại [{self.save_path}]')
        else:
            logger.info('File xác thực chưa được lưu')

    def login(self, username: str, password: str) -> dict:
        """
        Đăng nhập bằng tên người dùng và mật khẩu.

        Args:
            username (str): Tên người dùng tài khoản Xiaomi (email/số điện thoại/Xiaomi ID).
            password (str): Mật khẩu tài khoản Xiaomi.

        Returns:
            dict: Dữ liệu ủy quyền, bao gồm userId, ssecurity, deviceId và serviceToken.

        Raises:
            LoginError: Ném ra khi đăng nhập thất bại.
        """
        logger.warning('Đăng nhập bằng tài khoản mật khẩu rất có thể cần mã xác thực. Vui lòng thử sử dụng phương thức `QRlogin`.')
        data = self._get_index()
        post_data = {
            'qs': data['qs'],
            '_sign': data['_sign'],
            'callback': data['callback'],
            'sid': 'xiaomiio',
            '_json': 'true',
            'user': username,
            'hash': (hashlib.md5(password.encode()).hexdigest().upper() + '0' * 32)[:32],
        }
        ret = self.session.post(loginURL, data=post_data)
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Gửi trang đăng nhập thất bại, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])
        if 'location' not in ret_data:
            raise LoginError(-1, 'Lấy vị trí chuyển hướng thất bại')
        if 'notificationUrl' in ret_data:
            raise LoginError(-1, 'Cần mã xác thực, vui lòng thử sử dụng phương thức `QRlogin`')
        ret = self.session.get(ret_data['location'])
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Lấy vị trí chuyển hướng thất bại, {ret.text}')
        cookies = self.session.cookies.get_dict()

        self.auth_data = {
            'userId': ret_data['userId'],
            'ssecurity': ret_data['ssecurity'],
            'deviceId': data['deviceId'],
            'serviceToken': cookies['serviceToken'],
            'cUserId': cookies['cUserId'],
            'expireTime': self._extract_latest_gmt_datetime(cookies).strftime('%Y-%m-%d %H:%M:%S'),
            'account_info': self._get_account_info(ret_data['userId'])
        }

        self._save_auth()
        return self.auth_data

    @staticmethod
    def _print_qr(loginurl: str, box_size: int = 10) -> None:
        """
        In và lưu mã QR.

        Args:
            loginurl (str): URL chứa thông tin đăng nhập.
            box_size (int, optional): Kích thước mã QR. Mặc định là 10.
        """
        logger.info('Vui lòng sử dụng ứng dụng Mijia để quét mã QR dưới đây')
        qr = QRCode(border=1, box_size=box_size)
        qr.add_data(loginurl)
        qr.make_image().save('qr.png')
        try:
            qr.print_ascii(invert=True, tty=True)
        except OSError:
            qr.print_ascii(invert=True, tty=False)
            logger.info('Nếu không thể quét mã QR, '
                        'vui lòng thay đổi font chữ của terminal, '
                        'như "Maple Mono", "Fira Code", v.v.\n'
                        'Hoặc sử dụng trực tiếp file qr.png trong thư mục hiện tại.')

    def QRlogin(self) -> dict:
        """
        Đăng nhập bằng mã QR.

        Returns:
            dict: Dữ liệu ủy quyền, bao gồm userId, ssecurity, deviceId và serviceToken.

        Raises:
            LoginError: Ném ra khi đăng nhập thất bại.
        """
        data = self._get_index()
        location = data['location']
        location_parsed = parse.parse_qs(parse.urlparse(location).query)
        params = {
            '_qrsize': 240,
            'qs': data['qs'],
            'bizDeviceType': '',
            'callback': data['callback'],
            '_json': 'true',
            'theme': '',
            'sid': 'xiaomiio',
            'needTheme': 'false',
            'showActiveX': 'false',
            'serviceParam': location_parsed['serviceParam'][0],
            '_local': 'zh_CN',
            '_sign': data['_sign'],
            '_dc': str(int(time.time() * 1000)),
        }
        url = qrURL + '?' + parse.urlencode(params)
        ret = self.session.get(url)
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Lấy URL mã QR thất bại, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])
        loginurl = ret_data['loginUrl']
        self._print_qr(loginurl)
        try:
            ret = self.session.get(ret_data['lp'], timeout=60, headers={'Connection': 'keep-alive'})
        except requests.exceptions.Timeout:
            raise LoginError(-1, 'Hết thời gian chờ, vui lòng thử lại')
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Chờ đăng nhập thất bại, {ret.text}')
        ret_data = json.loads(ret.text[11:])
        if ret_data['code'] != 0:
            raise LoginError(ret_data['code'], ret_data['desc'])
        ret = self.session.get(ret_data['location'])
        if ret.status_code != 200:
            raise LoginError(ret.status_code, f'Lấy vị trí chuyển hướng thất bại, {ret.text}')
        cookies = self.session.cookies.get_dict()

        self.auth_data = {
            'userId': ret_data['userId'],
            'ssecurity': ret_data['ssecurity'],
            'deviceId': data['deviceId'],
            'serviceToken': cookies['serviceToken'],
            'cUserId': cookies['cUserId'],
            'expireTime': self._extract_latest_gmt_datetime(cookies).strftime('%Y-%m-%d %H:%M:%S'),
            'account_info': self._get_account_info(ret_data['userId'])
        }

        self._save_auth()
        return self.auth_data

    def __del__(self):
        """
        Hàm hủy, dọn dẹp file mã QR đã tạo.
        """
        if os.path.exists('qr.png'):
            os.remove('qr.png')
