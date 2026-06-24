class CameraSettings:
    def __init__(self, name: str, ip: str):
        self.name = name
        self.ip = ip
        self.pan_tilt_speed = 5
        self.zoom_speed = 4