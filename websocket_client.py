import queue
import asyncio
import json

from quart import websocket

from camera_settings import CameraSettings
from control_app import ControlApp

class WebsocketClient:
    def __init__(self, control_app: ControlApp):
        self.send_queue = queue.Queue()
        #self.receive_queue = asyncio.Queue()
        self.control_app = control_app

    def send_data(self, data):
        json_data = json.dumps(data)
        self.send_queue.put(json_data)

    async def send_loop(self):
        while True:
            if self.send_queue.empty():
                await asyncio.sleep(0.25)
                continue

            await websocket.send(self.send_queue.get())

    def process_update(self, data):
        match data['var']:
            case 'pan_tilt_response':
                v = float(data['value'])
                self.control_app.set_global_settings(pan_tilt_response=v)
                print(f"Pan tilt response set to {v}")
            case 'invert_pan':
                v = bool(data['value'])
                self.control_app.set_global_settings(invert_pan=v)
                print(f"Invert pan set to {v}")
            case 'invert_tilt':
                v = bool(data['value'])
                self.control_app.set_global_settings(invert_tilt=v)
                print(f"Invert tilt set to {v}")
            case 'zoom_response':
                v = float(data['value'])
                self.control_app.set_global_settings(zoom_response=v)
                print(f"Zoom response set to {v}")
            case 'invert_zoom':
                v = bool(data['value'])
                self.control_app.set_global_settings(invert_zoom=v)
                print(f"Invert zoom set to {v}")

    def process_camera_update(self, data):
        camera_ip = data['cameraIP']

        match data['var']:
            case 'pan_tilt_speed':
                v = int(data['value'])
                self.control_app.set_camera_settings(camera_ip, v, None)
                print(f"Pan tilt speed set to {v} for camera {camera_ip}")
            case 'zoom_speed':
                v = int(data['value'])
                self.control_app.set_camera_settings(camera_ip, None, v)
                print(f"Zoom speed set to {v} for camera {camera_ip}")

    def switch_active_camera(self, data):
        cam : CameraSettings | None = None

        if 'camera_name' in data:
            camera_name = data['camera_name']
            cam = self.control_app.find_camera_via_name(camera_name)
            if not cam:
                print(f'Could not find a camera named {camera_name} to switch to')
                return
        elif 'camera_ip' in data:
            camera_ip = data['camera_ip']
            cam = self.control_app.find_camera_via_ip(camera_ip)
            if not cam:
                print(f'Could not find a camera at {camera_ip} to switch to')
                return
        else:
            print(f'No data given to switch cameras')
            return

        self.control_app.camera_controller.control_camera(cam)
        self.send_data(self.control_app.get_state())

    def process_data(self, json_data):
        if not 'type' in json_data:
            print('Invalid message received. Disregarding...')
            return

        match json_data['type']:
            case 'state':
                self.send_data(self.control_app.get_state())
            case 'update':
                self.process_update(json_data)
            case 'cameraUpdate':
                self.process_camera_update(json_data)
            case 'set_active_camera':
                self.switch_active_camera(json_data)

    async def receive_loop(self):
        while True:
            #data = await self.receive_queue.get()
            data = await websocket.receive()
            json_data = json.loads(data)
            self.process_data(json_data)