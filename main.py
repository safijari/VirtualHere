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


class Plugin:
    _listener_task = None
    _enabled = False

    async def enable(self):
        decky_plugin.logger.info("enable called")

    async def is_enabled(self):
        return Plugin._enabled

    async def listener(self):
        decky_plugin.logger.info("listener started")
        while True:
            try:
                print("do the thing")
            except Exception:
                decky_plugin.logger.exception("listener")

    async def _main(self):
        try:
            loop = asyncio.get_event_loop()
            Plugin._listener_task = loop.create_task(Plugin.listener(self))
            decky_plugin.logger.info("Initialized")
        except Exception:
            decky_plugin.logger.exception("main")
