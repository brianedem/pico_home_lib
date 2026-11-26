#import re
#import sys

import asyncio
import logging
#import platform

from picow_home_lib import cfg_manager, cmd_processor, led, usb_console, wlan
#import time
#import timekeeper as tk

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

async def system():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(except_handler)

    # read the configuration file
    cfg_manager.config_manager(config_file)

    try:
        # start the LED blinking
        led.set_mode(led.Mode.BLINK, 1.0)

        # set up USB console
        tasks[asyncio.create_task(usb_console.console_task())] = 'usb_console'

        # apply configuration options to logging
        # TODO - network logging

        # start up the WIFI management
        tasks[asyncio.create_task(wlan.wifi_manager())] = 'wifi_manager'

        # set timezone

        # set up bluetooth

        # set up telnet

        ## Classes

        # ntfy

        while True:
            await asyncio.sleep(1)
        print('all tasks completed')

    except asyncio.CancelledError:
        print('system() cancelled')
    except Exception as e:
        print(f'system() got: {e}')
