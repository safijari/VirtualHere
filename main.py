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

    async def read_input_device(self):
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
                self.unbind_and_bind()

                if self.toggle_state == 1:
                    self.start_process()
                else:
                    self.stop_process()

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


class Plugin:
    _listener_task = None
    _enabled = True
    _sent = False
    _key_state_monitor = KeyStateMonitor(
        "/dev/input/by-path/platform-i8042-serio-0-event-kbd"
    )
    _process_manager = None

    async def enable_proc(self):
        logger.info("enable called")
        # Plugin._key_state_monitor.start_process()
        Plugin._enabled = True

    async def disable_proc(self):
        logger.info("disable called")
        # Plugin._key_state_monitor.stop_process()
        # unbind_and_rebind_sc()
        Plugin._enabled = False

    async def is_enabled(self):
        return Plugin._enabled

    async def listener(self):
        await Plugin._key_state_monitor.read_input_device()
        if Plugin._key_state_monitor.both_keys_pressed and not Plugin._sent:
            Plugin._sent = True
            return True
        if Plugin._sent and not Plugin._key_state_monitor.both_keys_pressed:
            Plugin._sent = False
        return False

    async def _main(self):
        try:
            decky_plugin.logger.info("Initialized")
            Plugin._process_manager = ProcessManager("/home/deck/vhusbdx86_64")
        except Exception:
            decky_plugin.logger.exception("main")
