import json
import time
import sys
sys.path.extend(['.', '..'])
from mijiaAPI import mijiaAPI

with open('jsons/auth.json') as f:
    auth = json.load(f)
with open('jsons/devices.json') as f:
    devices = json.load(f)
    did = devices[2]['did']
api = mijiaAPI(auth)
# Tham khảo https://iot.mi.com/new/doc/accesses/direct-access/extension-development/extension-functions/statistical-interface
ret = api.get_statistics({
    "did": did,
    "key": "7.1",                 # siid.piid, ở đây 7.1 biểu thị power-consumption của lumi.acpartner.mcn04
    "data_type": "stat_month_v3", # Thống kê theo tháng, tùy chọn: giờ (stat_hour_v3), ngày (stat_day_v3), tuần (stat_week_v3), tháng (stat_month_v3)
    "limit": 24,                  # Số mục tối đa trả về
    "time_start": 1685548800,     # 2023-06-01 00:00:00
    "time_end": 1750694400,       # 2025-06-24 00:00:00
})
"""
Vấn đề đã biết:
Các thiết bị cũ hơn sử dụng API khác, cần bỏ `_v3` trong `data_type`.
Và `key` cũng khác, ví dụ như key thống kê tiêu thụ điện của Mijia Air Conditioner Companion 2 là `powerCost`.
Xem chi tiết https://github.com/Do1e/mijia-api/issues/46
"""

for item in ret:
    value = eval(item['value'])[0]
    ts = item['time']
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
    print(f'{date}: {value}')
