#import re
#import sys

#import aioble
import asyncio
import logging
import platform

from picow_home_lib import cfg_manager
from picow_home_lib import cmd_processor
from picow_home_lib import led
from picow_home_lib import usb_console
#import time
#import wlan
#import timekeeper as tk


import sys

log = logging.getLogger(__name__)

config_file = 'sample.ini'

tasks = {}

def except_handler(loop, context):
    ex = context['exception']
    fut = context['future']
    if fut in tasks:
        log.error(f'task exception: {tasks[fut]} threw: {ex}')
    else:
        log.error(f'task exception: "unknown task" threw: {ex}')

async def base():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(except_handler)

    # read configuration
    cfg_mgr = cfg_manager.config_manager(config_file)
    config = cfg_mgr.config

    try:
        # start the LED blinking
        led.set_mode(led.Mode.BLINK, 0.5)

        # set up USB console
        tasks[asyncio.create_task(usb_console.console_task())] = 'usb_console_task'

        # apply configuration options to logging
        # TODO - network logging

        # set up WIFI

        # set timezone

        # set up bluetooth

        # set up telnet

        ## Classes

        # ntfy

        while True:
            await asyncio.sleep(1)
        print('all tasks completed')

    except asyncio.CancelledError:
        print('base() cancelled')
    except Exception as e:
        print(f'base() got: {e}')
