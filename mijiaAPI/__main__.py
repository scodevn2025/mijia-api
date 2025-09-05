from typing import Optional
import argparse
import json
import os
import sys
import time

from .apis import mijiaAPI
from .devices import mijiaDevice, get_device_info
from .login import mijiaLogin

def parse_args(args):
    parser = argparse.ArgumentParser(description="Mijia API CLI")
    subparsers = parser.add_subparsers(dest='command')
    parser.add_argument(
        '-p', '--auth_path',
        type=str,
        default=os.path.join(os.path.expanduser("~"), ".config/mijia-api", "mijia-api-auth.json"),
        help="Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api/mijia-api-auth.json",
    )
    parser.add_argument(
        '-l', '--list_devices',
        action='store_true',
        help="Liệt kê tất cả thiết bị Mijia",
    )
    parser.add_argument(
        '--list_homes',
        action='store_true',
        help="Liệt kê danh sách nhà",
    )
    parser.add_argument(
        '--list_scenes',
        action='store_true',
        help="Liệt kê danh sách cảnh",
    )
    parser.add_argument(
        '--list_consumable_items',
        action='store_true',
        help="Liệt kê danh sách vật tư tiêu hao",
    )
    parser.add_argument(
        '--run_scene',
        type=str,
        help="Chạy cảnh, chỉ định ID cảnh hoặc tên cảnh",
        nargs='+',
        metavar='SCENE_ID/SCENE_NAME',
    )
    parser.add_argument(
        '--get_device_info',
        type=str,
        help="Lấy thông tin thiết bị, chỉ định model thiết bị, sử dụng --list_devices để lấy trước",
        metavar='DEVICE_MODEL',
    )
    parser.add_argument(
        '--run',
        type=str,
        help="Sử dụng ngôn ngữ tự nhiên mô tả nhu cầu của bạn, nếu bạn có loa thông minh Xiao Ai",
        metavar='PROMPT',
    )
    parser.add_argument(
        '--wifispeaker_name',
        type=str,
        help="Chỉ định tên loa thông minh Xiao Ai, mặc định là loa Xiao Ai đầu tiên được tìm thấy",
        default=None,
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help="Loa Xiao Ai thực hiện im lặng",
    )

    get = subparsers.add_parser(
        'get',
        help="Lấy thuộc tính thiết bị",
    )
    get.set_defaults(func='get')
    get.add_argument(
        '-p', '--auth_path',
        type=str,
        default=os.path.join(os.path.expanduser("~"), ".config/mijia-api", "mijia-api-auth.json"),
        help="Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api/mijia-api-auth.json",
    )
    get.add_argument(
        '--dev_name',
        type=str,
        help="Tên thiết bị, chỉ định tên được thiết lập trong ứng dụng Mijia",
        required=True,
    )
    get.add_argument(
        '--prop_name',
        type=str,
        help="Tên thuộc tính, sử dụng --get_device_info để lấy trước",
        required=True,
    )

    set = subparsers.add_parser(
        'set',
        help="Thiết lập thuộc tính thiết bị",
    )
    set.set_defaults(func='set')
    set.add_argument(
        '-p', '--auth_path',
        type=str,
        default=os.path.join(os.path.expanduser("~"), ".config/mijia-api", "mijia-api-auth.json"),
        help="Đường dẫn lưu file xác thực, mặc định lưu tại ~/.config/mijia-api/mijia-api-auth.json",
    )
    set.add_argument(
        '--dev_name',
        type=str,
        help="Tên thiết bị, chỉ định tên được thiết lập trong ứng dụng Mijia",
        required=True,
    )
    set.add_argument(
        '--prop_name',
        type=str,
        help="Tên thuộc tính, sử dụng --get_device_info để lấy trước",
        required=True,
    )
    set.add_argument(
        '--value',
        type=str,
        help="Giá trị thuộc tính cần thiết lập",
        required=True,
    )
    return parser.parse_args(args)

def init_api(auth_path: str) -> mijiaAPI:
    if os.path.isdir(auth_path):
        auth_path = os.path.join(auth_path, "mijia-api-auth.json")
    if os.path.exists(auth_path):
        try:
            with open(auth_path, 'r') as f:
                auth = json.load(f)
            api = mijiaAPI(auth_data=auth)
            if not api.available:
                raise ValueError("Thông tin xác thực đã hết hạn")
        except (json.JSONDecodeError, ValueError):
            api = mijiaLogin(save_path=auth_path)
            auth = api.QRlogin()
            api = mijiaAPI(auth_data=auth)
    else:
        api = mijiaLogin(save_path=auth_path)
        auth = api.QRlogin()
        api = mijiaAPI(auth_data=auth)
    return api

def get_devices_list(api: mijiaAPI, verbose: bool = True) -> dict:
    devices = api.get_devices_list()
    if verbose:
        print("Danh sách thiết bị:")
        for device in devices:
            print(f"  - {device['name']}\n"
                    f"    did: {device['did']}\n"
                    f"    model: {device['model']}\n"
                    f"    online: {device['isOnline']}")
    device_mapping = {device['did']: device for device in devices}
    return device_mapping

def get_homes_list(api: mijiaAPI, verbose: bool = True, device_mapping: Optional[dict] = None) -> dict:
    if verbose:
        if device_mapping is None:
            device_mapping = get_devices_list(api, verbose=False)
    homes = api.get_homes_list()
    if verbose:
        print("Danh sách nhà:")
        for home in homes:
            print(f"  - {home['name']}\n"
                  f"    ID: {home['id']}\n"
                  f"    Địa chỉ: {home['address']}\n"
                  f"    Số lượng phòng: {len(home['roomlist'])}\n"
                  f"    Thời gian tạo: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(home['create_time']))}")
            print( "    Danh sách phòng:")
            for room in home['roomlist']:
                devices_name = []
                if room['dids']:
                    for did in room['dids']:
                        if did in device_mapping:
                            devices_name.append(device_mapping[did]['name'])
                        else:
                            devices_name.append(did)
                dids = ', '.join(devices_name)
                print(f"    - {room['name']}\n"
                      f"      ID: {room['id']}\n"
                      f"      Danh sách thiết bị: {dids}\n"
                      f"      Thời gian tạo: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(room['create_time']))}")
    home_mapping = {home['id']: home for home in homes}
    return home_mapping

def get_scenes_list(api: mijiaAPI, verbose: bool = True, home_mapping: Optional[dict] = None) -> dict:
    if home_mapping is None:
        home_mapping = get_homes_list(api, verbose=False)
    scene_mapping = {}
    for home_id, home in home_mapping.items():
        scenes = api.get_scenes_list(home_id)
        if scenes and verbose:
            print(f"Cảnh trong {home['name']} ({home_id}):")
            for scene in scenes:
                print(f"  - {scene['name']}\n"
                      f"    ID: {scene['scene_id']}\n"
                      f"    Thời gian tạo: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(scene['create_time'])))}\n"
                      f"    Thời gian cập nhật: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(scene['update_time'])))}")
        scene_mapping.update({scene['scene_id']: scene for scene in scenes})
    return scene_mapping

def get_consumable_items(api: mijiaAPI, home_mapping: Optional[dict] = None):
    if home_mapping is None:
        home_mapping = get_homes_list(api, verbose=False)
    for home_id, home in home_mapping.items():
        items = api.get_consumable_items(home_id, home['uid'])
        print(f"Vật tư tiêu hao trong {home['name']} ({home_id}):")
        for item in items:
            for consumes_data in item['consumes_data']:
                print(f"  - {consumes_data['details'][0]['description']} trong {consumes_data['name']}({consumes_data['did']})\n"
                      f"    Giá trị: {consumes_data['details'][0]['value']}")

def run_scene(api: mijiaAPI, scene_id: str, scene_mapping: Optional[dict] = None) -> bool:
    if scene_mapping is None:
        scene_mapping = get_scenes_list(api, verbose=False)
    if scene_id not in scene_mapping:
        scene_name_to_find = scene_id
        found = False
        for sid, scene in scene_mapping.items():
            if scene['name'] == scene_name_to_find:
                scene_id = sid
                found = True
                break
        if not found:
            print(f"Cảnh {scene_name_to_find} không tìm thấy")
            return False
    scene_name = scene_mapping[scene_id]['name']
    ret = api.run_scene(scene_id)
    if ret:
        print(f"Cảnh {scene_name}({scene_id}) chạy thành công")
        return True
    else:
        print(f"Chạy cảnh {scene_name}({scene_id}) thất bại")
        return False

def get(args):
    api = init_api(args.auth_path)
    device = mijiaDevice(api, dev_name=args.dev_name)
    value = device.get(args.prop_name)
    unit = device.prop_list[args.prop_name].unit
    print(f"Giá trị {args.prop_name} của {args.dev_name} là {value} {unit if unit else ''}")

def set(args):
    api = init_api(args.auth_path)
    device = mijiaDevice(api, dev_name=args.dev_name)
    ret = device.set(args.prop_name, args.value)
    unit = device.prop_list[args.prop_name].unit
    if ret:
        print(f"Giá trị {args.prop_name} của {args.dev_name} đã được thiết lập thành {args.value} {unit if unit else ''}")
    else:
        print(f"Thiết lập giá trị {args.prop_name} của {args.dev_name} thành {args.value} thất bại")


def main(args):
    args = parse_args(args)

    if args.get_device_info:
        device_info = get_device_info(args.get_device_info)
        print(json.dumps(device_info, indent=2, ensure_ascii=False))
    if not (args.list_devices or
            args.list_homes or
            args.list_scenes or
            args.list_consumable_items or
            args.run_scene or
            args.run or
            hasattr(args, 'func') and args.func is not None):
        return

    api = init_api(args.auth_path)
    device_mapping = None
    home_mapping = None
    scenes_mapping = None

    if args.list_devices:
        device_mapping = get_devices_list(api)
    if args.list_homes:
        home_mapping = get_homes_list(api, device_mapping=device_mapping)
    if args.list_scenes:
        scenes_mapping = get_scenes_list(api, home_mapping=home_mapping)
    if args.list_consumable_items:
        get_consumable_items(api, home_mapping=home_mapping)
    if args.run_scene:
        for scene_id in args.run_scene:
            run_scene(api, scene_id, scene_mapping=scenes_mapping)
    if args.run:
        if device_mapping is None:
            device_mapping = get_devices_list(api, verbose=False)
        if args.wifispeaker_name is None:
            wifispeaker = None
            for device in device_mapping.values():
                if 'xiaomi.wifispeaker' in device['model']:
                    wifispeaker = mijiaDevice(api, dev_name=device['name'])
                    break
            if wifispeaker is None:
                raise ValueError("Không tìm thấy thiết bị loa thông minh Xiao Ai")
        else:
            wifispeaker = mijiaDevice(api, dev_name=args.wifispeaker_name)
        wifispeaker.run_action('execute-text-directive', _in=[args.run, args.quiet])
    if hasattr(args, 'func') and args.func is not None:
        if args.func == 'get':
            get(args)
        if args.func == 'set':
            set(args)

def cli():
    main(sys.argv[1:])

if __name__ == "__main__":
    main(sys.argv[1:])
