import os
import decky_plugin
from pathlib import Path
import json
import os
import subprocess
import sys
import shutil
import time
import asyncio
import struct
import subprocess
import signal
import time
import asyncio
import traceback
from threading import Thread

import sys
sys.path.append(os.path.dirname(__file__))

from py_backend import keyboard


logger = decky_plugin.logger


def run_shell_command(command):
    subprocess.run(command, shell=True)


def unbind_and_rebind_sc():
    run_shell_command('echo "3-3" | sudo tee /sys/bus/usb/drivers/usb/unbind')
    run_shell_command('echo "3-3" | sudo tee /sys/bus/usb/drivers/usb/bind')


class KeyStateMonitor:
    def __init__(self, device_path):
        self.device_path = device_path
        self.key_states = {114: 0, 115: 0}
        self.toggle_state = 0
        self.both_keys_pressed = False
        self.fd = open(self.device_path, "rb")

    def read_input_device(self):
        device_file = self.fd

        event_data = device_file.read(24)

        event = struct.unpack("llHHI", event_data)

        timestamp, microseconds, event_type, event_code, event_value = event

        if event_type == 1:
            self.key_states[event_code] = event_value

            if self.key_states[114] != 0 and self.key_states[115] != 0:
                self.both_keys_pressed = True

            elif (
                self.both_keys_pressed
                and self.key_states[114] == 0
                and self.key_states[115] == 0
            ):
                self.toggle_state = 1 - self.toggle_state

                self.both_keys_pressed = False


class ProcessManager:
    def __init__(self, path):
        self.process_path = path
        self.process = None

    def start_process(self):
        if self.process is None or self.process.poll() is not None:
            self.process = subprocess.Popen([self.process_path])

    def stop_process(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
            self.process = None


def poller(_key_state_monitor):
    logger.info("poller initialized")
    while True:
        try:
            _key_state_monitor.read_input_device()
            # logger.info(f"reading done {Plugin._key_state_monitor.both_keys_pressed}")
        except Exception:
            logger.error(traceback.format_exc())


class Plugin:
    _poll_task = None
    _enabled = False
    _sent = False
    _key_state_monitor = KeyStateMonitor(
        "/dev/input/by-path/platform-i8042-serio-0-event-kbd"
    )
    _process_manager = None
    _thread = None
    _last_coffee = time.time()

    async def enable_proc(self):
        # logger.info("enable called")
        Plugin._process_manager.start_process()
        Plugin._enabled = True

    async def disable_proc(self):
        # logger.info("disable called")
        unbind_and_rebind_sc()
        Plugin._process_manager.stop_process()
        Plugin._enabled = False

    async def is_enabled(self):
        return Plugin._enabled

    async def polled_fn(self):
        # logger.info("Calling polled fn")
        try:
            if time.time() - Plugin._last_coffee > 10 and Plugin._enabled:
                keyboard.press_and_release("scrlk")
                keyboard.press_and_release("scrlk")
                Plugin._last_coffee = time.time()
                # logger.info("pressing scroll lock to keep things awake")
            # logger.info(f"{Plugin._sent} {Plugin._key_state_monitor.both_keys_pressed}")
            if Plugin._key_state_monitor.both_keys_pressed and not Plugin._sent:
                # logger.info(f"true sent")
                Plugin._sent = True
                return True
            if Plugin._sent and not Plugin._key_state_monitor.both_keys_pressed:
                # logger.info("false unsent")
                Plugin._sent = False
            return False
        except Exception:
            logger.info("failed " + traceback.format_exc())

    async def _main(self):
        try:
            Plugin._thread = Thread(target=lambda: poller(Plugin._key_state_monitor))
            Plugin._thread.daemon = True
            Plugin._thread.start()
            Plugin._process_manager = ProcessManager(decky_plugin.DECKY_PLUGIN_DIR + "/server")
            decky_plugin.logger.info("Initialized")
        except Exception:
            decky_plugin.logger.exception("main")
