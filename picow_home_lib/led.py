import asyncio
from enum import Enum, auto

import machine

class Mode(Enum):
    ON = auto()
    OFF = auto()
    BLINK = auto()

_led = machine.Pin('LED', machine.Pin.OUT)
_led.on()
_mode = Mode.ON
_rate = None
_blink_task = None

async def led_blink(rate):
    while True:
        await asyncio.sleep(rate)
        _led.toggle()

def set_mode(mode, rate=None):
    global _mode, _rate, _blink_task
#   print(f'setting led to {mode} at {rate}')
    assert not(mode is Mode.BLINK and rate is None)

    if _blink_task and rate!=_rate:
        _blink_task.cancel()
        _blink_task = None

    _mode = mode
    _rate = rate
        
    if mode is Mode.ON:
        _led.on()
    elif mode is Mode.OFF:
        _led.off()
    else:
        _blink_task = asyncio.create_task(led_blink(rate))
