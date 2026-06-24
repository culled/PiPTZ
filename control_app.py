import json
import threading
import time
from typing import List, Callable, Dict, Any
from operator import indexOf

from camera_controller import CameraController
from camera_settings import CameraSettings
from controller import Controller, ControllerButton, ControllerAxis


class ControlApp:
    def __init__(self, callback_func: Callable[[Dict[str, Any]], None]):
        self.controller = Controller()
        self.lock = threading.Lock()
        self.camera_controller = CameraController()
        self.cameras : List[CameraSettings] = []
        self.state_changed_callback = callback_func

    def run(self):
        while True:
            # Wait for a gamepad connection/reconnection
            if not self.controller.is_connected():
                gamepads = Controller.get_available_gamepads()
                if len(gamepads) > 0:
                    self.controller.connect_to_gamepad(gamepads[-1])
                    if not self.controller.is_connected():
                        continue
                else:
                    time.sleep(0.5)
                    continue

            # Early out if we lost gamepad connection
            if not self.controller.is_connected():
                print(f"Lost connection to gamepad")
                self.camera_controller.stop_moving()
                continue

            state_changed = False
            with self.lock:
                try:
                    state_changed = self.tick()
                except Exception as ex:
                    print(f"Error ticking: {ex}")

            if state_changed:
                self.state_changed_callback(self.get_state())
                self.save_config_file()

            time.sleep(0.1)

        self.camera_controller.stop_moving()

    def switch_to_next_camera(self, forward: bool):
        if len(self.cameras) == 0:
            self.camera_controller.disconnect()
            return
        current_index = indexOf(self.cameras, self.camera_controller.current_camera) if self.camera_controller.current_camera else -1

        if forward or current_index == -1:
            new_index = (current_index + 1) % len(self.cameras)
        else:
            new_index = current_index - 1
            if new_index < 0:
                new_index += len(self.cameras)

        if current_index != new_index:
            self.camera_controller.control_camera(self.cameras[new_index])

    def tick(self) -> bool:
        state_changed = False

        if self.controller.was_button_pressed(ControllerButton.LEFT_SHOULDER):
            print("Switch backwards")
            self.switch_to_next_camera(False)
            state_changed = True

        if self.controller.was_button_pressed(ControllerButton.RIGHT_SHOULDER):
            print("Switch forwards")
            self.switch_to_next_camera(True)
            state_changed = True

        if self.camera_controller.current_camera:
            if self.controller.was_button_pressed(ControllerButton.DPAD_RIGHT):
                new_pan_tilt_speed = self.camera_controller.current_camera.pan_tilt_speed + 1
                new_pan_tilt_speed = min(new_pan_tilt_speed, 24)
                self.camera_controller.current_camera.pan_tilt_speed = new_pan_tilt_speed
                print(f"Increased pan/tilt speed to {new_pan_tilt_speed}")
                state_changed = True
            elif self.controller.was_button_pressed(ControllerButton.DPAD_LEFT):
                new_pan_tilt_speed = self.camera_controller.current_camera.pan_tilt_speed - 1
                new_pan_tilt_speed = max(new_pan_tilt_speed, 1)
                self.camera_controller.current_camera.pan_tilt_speed = new_pan_tilt_speed
                print(f"Decreased pan/tilt speed to {new_pan_tilt_speed}")
                state_changed = True

            if self.controller.was_button_pressed(ControllerButton.DPAD_UP):
                new_zoom_speed = self.camera_controller.current_camera.zoom_speed + 1
                new_zoom_speed = min(new_zoom_speed, 24)
                self.camera_controller.current_camera.zoom_speed = new_zoom_speed
                print(f"Increased zoom speed to {new_zoom_speed}")
                state_changed = True
            elif self.controller.was_button_pressed(ControllerButton.DPAD_DOWN):
                new_zoom_speed = self.camera_controller.current_camera.zoom_speed - 1
                new_zoom_speed = max(new_zoom_speed, 1)
                self.camera_controller.current_camera.zoom_speed = new_zoom_speed
                print(f"Decreased zoom speed to {new_zoom_speed}")
                state_changed = True

            pan_input = self.controller.get_axis(ControllerAxis.RIGHT_STICK_X)
            tilt_input = -self.controller.get_axis(ControllerAxis.RIGHT_STICK_Y)
            self.camera_controller.pan_tilt_input(pan_input, tilt_input)

            zoom_input = self.controller.get_axis(ControllerAxis.RIGHT_TRIGGER) - self.controller.get_axis(ControllerAxis.LEFT_TRIGGER)
            self.camera_controller.zoom_input(zoom_input)

        return state_changed

    def add_camera(self, camera_name: str, camera_ip: str):
        cam = CameraSettings(camera_name, camera_ip)
        with self.lock:
            self.cameras.append(cam)

            if not self.camera_controller.current_camera:
                self.switch_to_next_camera(True)

        print(f"Added camera {camera_name} at {camera_ip}")
        self.save_config_file()
        self.state_changed_callback(self.get_state())
        return cam

    def find_camera_via_ip(self, camera_ip: str):
        for c in self.cameras:
            if c.ip == camera_ip:
                return c

        return None

    def find_camera_via_name(self, camera_name: str):
        for c in self.cameras:
            if c.name == camera_name:
                return c

        return None

    def remove_camera(self, camera_ip: str):
        with self.lock:
            if self.camera_controller.current_camera and self.camera_controller.current_camera.ip == camera_ip:
                if len(self.cameras) > 1:
                    self.switch_to_next_camera(True)
                else:
                    self.camera_controller.disconnect()

            current_cam = self.find_camera_via_ip(camera_ip)
            if not current_cam:
                print(f"Could not find camera {camera_ip}")
                return

            current_cam_index = indexOf(self.cameras, current_cam)
            self.cameras.pop(current_cam_index)
        print(f"Removed camera {camera_ip}")
        self.save_config_file()
        self.state_changed_callback(self.get_state())

    def get_state(self):
        with self.lock:
            cameras = []
            for c in self.cameras:
                camera_data = {
                    'name': c.name,
                    'ip': c.ip,
                    'pan_tilt_speed': c.pan_tilt_speed,
                    'zoom_speed': c.zoom_speed,
                    'is_active': c == self.camera_controller.current_camera
                }

                cameras.append(camera_data)

            return {
                'type': 'state',
                'pan_tilt_response': self.camera_controller.pan_tilt_response,
                'invert_pan': self.camera_controller.invert_pan,
                'invert_tilt': self.camera_controller.invert_tilt,
                'zoom_response': self.camera_controller.zoom_response,
                'invert_zoom': self.camera_controller.invert_zoom,
                'cameras': cameras
            }

    def set_global_settings(self, pan_tilt_response: float | None = None, invert_pan: bool | None = None, invert_tilt: bool | None = None, zoom_response: float | None = None, invert_zoom: bool | None = None):
        with self.lock:
            if pan_tilt_response is not None:
                self.camera_controller.pan_tilt_response = pan_tilt_response

            if invert_pan is not None:
                self.camera_controller.invert_pan = invert_pan

            if invert_tilt is not None:
                self.camera_controller.invert_tilt = invert_tilt

            if zoom_response is not None:
                self.camera_controller.zoom_response = zoom_response

            if invert_zoom is not None:
                self.camera_controller.invert_zoom = invert_zoom

        self.save_config_file()
        self.state_changed_callback(self.get_state())

    def set_camera_settings(self, camera_ip: str, pan_tilt_speed: int | None, zoom_speed: int | None):
        with self.lock:
            cam = self.find_camera_via_ip(camera_ip)

            if not cam:
                print(f"Camera {camera_ip} does not exist")
                return

            if pan_tilt_speed is not None:
                cam.pan_tilt_speed = pan_tilt_speed

            if zoom_speed is not None:
                cam.zoom_speed = zoom_speed

        self.save_config_file()
        self.state_changed_callback(self.get_state())

    def save_config_file(self):
        with self.lock:
            cam_datas = []
            for cam in self.cameras:
                cam_data = {
                    'name': cam.name,
                    'ip': cam.ip,
                    'pan_tilt_speed': cam.pan_tilt_speed,
                    'zoom_speed': cam.zoom_speed,
                    'is_active': cam == self.camera_controller.current_camera
                }
                cam_datas.append(cam_data)

            config_data = {
                'pan_tilt_response': self.camera_controller.pan_tilt_response,
                'invert_pan': self.camera_controller.invert_pan,
                'invert_tilt': self.camera_controller.invert_tilt,
                'zoom_response_slider': self.camera_controller.zoom_response,
                'invert_zoom': self.camera_controller.invert_zoom,
                'cameras': cam_datas
            }

            try:
                with open('config.json', 'w') as file:
                    json.dump(config_data, file, indent=4)

                print('Saved config settings')
            except Exception as ex:
                print(f"Failed to save config file: {ex}")

    def load_config_file(self):
        print("Loading config...")

        try:
            with open('config.json', 'r') as file:
                config = json.load(file)
                active_cam : CameraSettings | None = None

                with self.lock:
                    self.camera_controller.pan_tilt_response = config['pan_tilt_response']
                    self.camera_controller.invert_pan = config['invert_pan']
                    self.camera_controller.invert_tilt = config['invert_tilt']

                    self.camera_controller.zoom_response = config['zoom_response_slider']
                    self.camera_controller.invert_zoom = config['invert_zoom']

                    for cam_data in config['cameras']:
                        self.cameras.append(CameraSettings(cam_data['name'], cam_data['ip']))
                        cam = self.cameras[-1]
                        cam.pan_tilt_speed = cam_data['pan_tilt_speed']
                        cam.zoom_speed = cam_data['zoom_speed']

                        if cam_data['is_active']:
                            active_cam = cam

                if active_cam:
                    self.camera_controller.control_camera(active_cam)

                print(f"Loaded config settings with {len(self.cameras)} camera(s)")
        except FileNotFoundError:
            print("No config file found")
