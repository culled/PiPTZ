from visca_over_ip import Camera

from camera_settings import CameraSettings

class CameraController:
    def __init__(self):
        self.camera_conn : Camera | None = None
        self.current_camera : CameraSettings | None = None
        self.last_pan_input = 0
        self.last_tilt_input = 0
        self.last_zoom_input = 0
        self.pan_tilt_response = 1.0
        self.invert_pan = False
        self.invert_tilt = False
        self.zoom_response = 1.0
        self.invert_zoom = False

    def is_connected(self):
        return self.current_camera is not None

    def disconnect(self):
        if not self.current_camera:
            return

        self.last_pan_input = 0
        self.last_tilt_input = 0
        self.last_zoom_input = 0
        self.camera_conn.pantilt(0, 0)
        self.camera_conn.zoom(0)
        self.camera_conn.close_connection()
        self.camera_conn = None
        self.current_camera = None

    def control_camera(self, camera: CameraSettings) -> bool:
        if self.current_camera:
            self.disconnect()

        if not camera:
            return False

        self.last_pan_input = 0
        self.last_tilt_input = 0
        self.last_zoom_input = 0

        try:
            self.camera_conn = Camera(camera.ip)
            self.current_camera = camera
            print(f"Switched to camera {camera.ip}")
        except Exception as ex:
            print(f"Error connecting to camera {camera.ip}: {ex}")
            self.camera_conn = None
            self.current_camera = None
            return False

        return self.is_connected()

    def pan_tilt_input(self, pan_input: float, tilt_input: float):
        if not self.is_connected():
            return

        pan_input = self.adjust_axis(pan_input, self.pan_tilt_response)
        tilt_input = -self.adjust_axis(tilt_input, self.pan_tilt_response)

        pan = self.get_speed(pan_input, self.current_camera.pan_tilt_speed)
        tilt = self.get_speed(tilt_input, self.current_camera.pan_tilt_speed)

        if self.invert_pan:
            pan = -pan

        if self.invert_tilt:
            tilt = -tilt

        if pan == self.last_pan_input and tilt == self.last_tilt_input:
            return

        self.camera_conn.pantilt(pan, tilt)
        #print(f"Pan/tilt: {pan}, {tilt}")
        self.last_pan_input = pan
        self.last_tilt_input = tilt

    def zoom_input(self, zoom_input: float):
        if not self.is_connected():
            return

        zoom_input = self.adjust_axis(zoom_input, self.zoom_response)
        zoom = self.get_speed(zoom_input, self.current_camera.zoom_speed)

        if self.invert_zoom:
            zoom = -zoom

        if zoom == self.last_zoom_input:
            return

        self.camera_conn.zoom(zoom)
        #print(f"Zoom: {zoom}")
        self.last_zoom_input = zoom

    def stop_moving(self):
        self.pan_tilt_input(0, 0)
        self.zoom_input(0)

    @staticmethod
    def adjust_axis(axis: float, response: float) -> float:
        sign = 1 if axis > 0.0 else -1
        return pow(abs(axis), response) * sign

    @staticmethod
    def get_speed(movement: float, max_speed: int) -> int:
        return max(min(round(movement * max_speed), max_speed), -max_speed)