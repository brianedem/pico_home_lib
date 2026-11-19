#import re
#import sys

#import aioble
import asyncio
import logging

from picow_home_lib import cfg_manager
from picow_home_lib import cmd_processor
import console
from picow_home_lib import led
#import time
#import wlan
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

async def base():
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(except_handler)

    try:
        # start the LED blinking
        led.set_mode(led.Mode.BLINK, 0.5)

        # set up console
        tasks[asyncio.create_task(console.console_task())] = 'console_task'

        # read configuration
        cfg_mgr = cfg_manager.config_manager(config_file)
        config = cfg_mgr.config

        # apply configuration options to logging
        # TODO - network logging

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
