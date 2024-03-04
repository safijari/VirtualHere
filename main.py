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

class KeyStateMonitor:
    def __init__(self, device_path, process_path):
        self.device_path = device_path
        self.key_states = {114: 0, 115: 0}
        self.toggle_state = 0
        self.both_keys_pressed = False
        self.process_path = process_path
        self.process = None
        self.fd = open(self.device_path, 'rb')

    def run_shell_command(self, command):
        subprocess.run(command, shell=True)

    def start_process(self):
        if self.process is None or self.process.poll() is not None:
            self.process = subprocess.Popen([self.process_path])

    def stop_process(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()

    def unbind_and_bind(self):
        self.run_shell_command('echo "3-3" | sudo tee /sys/bus/usb/drivers/usb/unbind')
        self.run_shell_command('echo "3-3" | sudo tee /sys/bus/usb/drivers/usb/bind')

    async def read_input_device(self):
        device_file = self.fd

        event_data = device_file.read(24)

        event = struct.unpack('llHHI', event_data)

        timestamp, microseconds, event_type, event_code, event_value = event

        if event_type == 1:
            self.key_states[event_code] = event_value

            # print(f"Key {event_code} - State: {event_value}")

            if self.key_states[114] != 0 and self.key_states[115] != 0:
                self.both_keys_pressed = True

            elif self.both_keys_pressed and self.key_states[114] == 0 and self.key_states[115] == 0:
                self.toggle_state = 1 - self.toggle_state
                self.unbind_and_bind()

                if self.toggle_state == 1:
                    self.start_process()
                    logger.info("Toggle state is 1. Process started/restarted.")
                else:
                    self.stop_process()
                    logger.info("Toggle state is 0. Process stopped.")

                self.both_keys_pressed = False


class Plugin:
    _listener_task = None
    _enabled = False
    _sent = False
    _key_state_monitor = KeyStateMonitor('/dev/input/by-path/platform-i8042-serio-0-event-kbd', '/home/deck/vhusbdx86_64')

    async def enable(self):
        decky_plugin.logger.info("enable called")
        Plugin._key_state_monitor.start_process()
        Plugin._key_state_monitor.toggle_state = 1
        Plugin._enabled = True

    async def disable(self):
        decky_plugin.logger.info("enable called")
        Plugin._key_state_monitor.stop_process()
        Plugin._key_state_monitor.toggle_state = 0
        Plugin._enabled = False

    async def is_enabled(self):
        return Plugin._enabled

    async def listener(self):
        decky_plugin.logger.info(f"listener started {Plugin._sent} {Plugin._key_state_monitor.both_keys_pressed}")
        await Plugin._key_state_monitor.read_input_device()
        if Plugin._key_state_monitor.both_keys_pressed and not Plugin._sent:
            decky_plugin.logger.info(f"Sending now")
            Plugin._sent = True
            return True
        if Plugin._sent and not Plugin._key_state_monitor.both_keys_pressed:
            decky_plugin.logger.info(f"resetting sent")
            Plugin._sent = False
        decky_plugin.logger.info(f"default path")
        return False

    async def _main(self):
        try:
            # loop = asyncio.get_event_loop()
            # Plugin._listener_task = loop.create_task(Plugin.listener(self))
            decky_plugin.logger.info("Initialized")
        except Exception:
            decky_plugin.logger.exception("main")
