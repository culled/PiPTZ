import os
import threading
from enum import Enum
from typing import List
import time

from ThirdParty.Gamepad.Gamepad import Gamepad, available, gamepad


class ControllerAxis(Enum):
    LEFT_STICK_X = 0,
    LEFT_STICK_Y = 1,
    RIGHT_STICK_X = 2,
    RIGHT_STICK_Y = 3,
    LEFT_TRIGGER = 4,
    RIGHT_TRIGGER = 5

class ControllerButton(Enum):
    A = 0,
    B = 1,
    X = 2,
    Y = 3,
    LEFT_SHOULDER = 4,
    RIGHT_SHOULDER = 5,
    DPAD_LEFT = 6,
    DPAD_RIGHT = 7,
    DPAD_UP = 8,
    DPAD_DOWN = 9

class Controller:
    class UpdateThread(threading.Thread):
        def __init__(self, controller):
            self.controller = controller
            self.is_running = False
            threading.Thread.__init__(self)

        def run(self):
            self.is_running = True
            while self.is_running and self.controller.current_gamepad is not None:
                try:
                    self.controller.current_gamepad.updateState()

                    dpad_x = self.controller.current_gamepad.axis(6)
                    dpad_y = self.controller.current_gamepad.axis(7)

                    if dpad_x > -0.1:
                        self.controller.dpad_was_pressed_map[ControllerButton.DPAD_LEFT] = False

                    if dpad_x < 0.1:
                        self.controller.dpad_was_pressed_map[ControllerButton.DPAD_RIGHT] = False

                    if dpad_y > -0.1:
                        self.controller.dpad_was_pressed_map[ControllerButton.DPAD_UP] = False

                    if dpad_y < 0.1:
                        self.controller.dpad_was_pressed_map[ControllerButton.DPAD_DOWN] = False

                except Exception as ex:
                    print(f"Error updating gamepad state: {ex}")

    def __init__(self):
        self.current_gamepad: Gamepad | None = None
        self.gamepad_index = -1

        self.dpad_was_pressed_map = {
            ControllerButton.DPAD_LEFT: False,
            ControllerButton.DPAD_RIGHT: False,
            ControllerButton.DPAD_UP: False,
            ControllerButton.DPAD_DOWN: False,
        }

        self.axis_mapping = {
            ControllerAxis.LEFT_STICK_X: 0,
            ControllerAxis.LEFT_STICK_Y: 1,
            ControllerAxis.RIGHT_STICK_X: 3,
            ControllerAxis.RIGHT_STICK_Y: 4,
            ControllerAxis.LEFT_TRIGGER: 2,
            ControllerAxis.RIGHT_TRIGGER: 5,
        }

        self.button_mapping = {
            ControllerButton.A: 0,
            ControllerButton.B: 1,
            ControllerButton.X: 2,
            ControllerButton.Y: 3,
            ControllerButton.LEFT_SHOULDER: 4,
            ControllerButton.RIGHT_SHOULDER: 5,
        }

        self.update_thread : Controller.UpdateThread | None = None

    def __del__(self):
        self.disconnect()

    @staticmethod
    def get_available_gamepads():
        files = os.listdir('/dev/input')
        gamepads : List[int] = []

        for file in files:
            if not file.startswith('js'):
                continue

            gamepads.append(int(file.lstrip('js')))

        gamepads.sort()

        return gamepads

    def connect_to_gamepad(self, gamepad_index: int):
        if not available(gamepad_index):
            print(f"Gamepad index {gamepad_index} is invalid")
            return False

        self.disconnect()

        self.gamepad_index = gamepad_index

        try:
            self.current_gamepad = Gamepad(gamepad_index)

            # Setup joystick axes to prevent errors until they're used
            for axis in self.axis_mapping.values():
                self.current_gamepad.axisMap[axis] = 0.0

            self.current_gamepad.axisMap[6] = 0.0
            self.current_gamepad.axisMap[7] = 0.0

            self.current_gamepad.waitReady()

            self.update_thread = Controller.UpdateThread(self)
            self.update_thread.start()

            print(f"Connected to gamepad {gamepad_index}")
            return True
        except Exception as ex:
            self.current_gamepad = None
            print(f"Failed to connect to gamepad {gamepad_index}: {ex}")
            return False

    def is_connected(self):
        return self.current_gamepad is not None and self.current_gamepad.isConnected()

    def get_axis(self, axis: ControllerAxis):
        if not self.is_connected():
            return 0.0

        axis_index = self.axis_mapping[axis]
        axis_value = self.current_gamepad.axis(axis_index)

        return axis_value

    def was_button_pressed(self, button: ControllerButton):
        if not self.is_connected():
            return False

        if (button == ControllerButton.DPAD_LEFT or button == ControllerButton.DPAD_RIGHT or
            button == ControllerButton.DPAD_UP or button == ControllerButton.DPAD_DOWN):
            if self.dpad_was_pressed_map[button]:
                return False

            axis = 6 if button == ControllerButton.DPAD_LEFT or button == ControllerButton.DPAD_RIGHT else 7
            value = self.current_gamepad.axis(axis)

            if (((button == ControllerButton.DPAD_RIGHT or button == ControllerButton.DPAD_DOWN) and value > 0.1) or
                    ((button == ControllerButton.DPAD_LEFT or button == ControllerButton.DPAD_UP) and value < -0.1)):
                self.dpad_was_pressed_map[button] = True
                return True

            return False

        button_index = self.button_mapping[button]
        return self.current_gamepad.beenPressed(button_index)

    def disconnect(self):
        if self.update_thread:
            self.update_thread.is_running = False
            self.update_thread.join()

        if self.current_gamepad:
            self.current_gamepad.disconnect()
