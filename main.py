import asyncio
import json
import socket
import threading
import queue
from functools import wraps
from typing import List, Dict, Any

from quart import Quart, render_template, websocket, request, redirect

from control_app import ControlApp
from websocket_client import WebsocketClient

web_app = Quart(__name__)
connected_websockets = set()

def collect_websocket(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        global connected_websockets
        client = WebsocketClient(control_app)
        connected_websockets.add(client)
        try:
            return await func(client, *args, **kwargs)
        finally:
            connected_websockets.remove(client)
    return wrapper

def state_callback(state: Dict[str, Any]):
    for client in connected_websockets:
        client.send_data(state)

control_app = ControlApp(callback_func=state_callback)
port = 4343

def run_app():
    control_app.load_config_file()
    control_app.run()

@web_app.websocket('/ws')
@collect_websocket
async def ws(client: WebsocketClient) -> None:
    sender = asyncio.create_task(client.send_loop())
    receiver = asyncio.create_task(client.receive_loop())
    await asyncio.gather(sender, receiver)

@web_app.route('/')
async def dashboard():
    return await render_template("index.html", state=control_app.get_state())

@web_app.route('/add-camera', methods=['POST'])
async def addCamera():
    form_data = await request.form
    control_app.add_camera(form_data['cameraName'], form_data['cameraIP'])
    return redirect('/')

@web_app.route('/remove-camera', methods=['POST'])
async def deleteCamera():
    camera_ip = request.args.get("cameraIP")

    if camera_ip:
        control_app.remove_camera(camera_ip)

    return redirect('/')

def print_local_ip():
    # https://pytutorial.com/python-get-all-ip-addresses-on-local-network/
    try:
        # Create a socket connection
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"Local IP: {ip}:{port}")
    except Exception as e:
        print(f"Could not determine local IP: {str(e)}")

if __name__ == '__main__':
    print_local_ip()

    camera_thread = threading.Thread(target=run_app, daemon=True)
    camera_thread.start()

    web_app.run(port=port, host="0.0.0.0")