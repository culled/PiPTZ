# PiPTZ
A custom Visca PTZ interface that allows you to control PTZ cameras using a gamepad via the Visca protocol. A Raspberry Pi runs the main PiPTZ server and is configurable via a web interface.

## Setting Up
1. Clone the repository - `git clone https://github.com/culled/PiPTZ.git`
2. Navigate to the repo - `cd PiPTZ`
3. Setup a Python virtual environment - `python3 -m venv .venv`
4. Activate the virtual environment - `source .venv/bin/activate`
5. Install dependencies - `pip install -r requirements.txt`
6. Plug in a joystick to a USB port of the Pi (I've so far only tested with a Logitech F310 gamepad)
7. Run the program - `python3 main.py`

A `start.sh` script is included which can be used to auto-start PiPTZ if it's located in the `/root` directory and you have the script execute upon boot. You can also modify this file to point to the directory that you cloned the repo so it starts properly from there.

## Basic Controls
- Moving the right joystick pans and tilts the active camera
- Left trigger zooms the camera out
- Right trigger zooms the camera in
- Left and right bumpers switch to the previous or next camera
- D-pad left and right decrease and increase the pan/tilt speed of the active camera
- D-pad down and up decrease and increase the zoom speed of the active camera
  
## Configuring Cameras
You can access a web interface to modify the settings of PiPTZ by navigating to `<IP of your Pi>:4343` in a web browser. The program will print out the local IP address upon starting, so you can use that to identify you Pi's IP.

Settings exposed in the web interface:
- Pan/Tilt Response: Higher values make the panning and tilting less sensitive for small joystick movements
- Invert Panning: Reverses the panning direction
- Invert Tilting: Reverses the tilting direction
- Zoom Response: Higher values make the panning and tilting less sensitive for small joystick movements
- Invert Zooming: Reverses the zooming direction

### Add Camera
Set a name for the camera and input its IP address, then click "Add Camera." The camera will appear below in the list of cameras

### Cameras
Shows all the registered cameras that can be controlled. The active camera is denoted next to its name with "(Active)." You can click any camera to view details about it and change its settings.

#### Camera-specific Settings:
- Pan/Tilt Speed: The speed of the panning and tilting
- Zoom Speed: The speed of the zooming

Pressing "Delete" will remove the camera from the list of registered cameras
