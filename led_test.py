import asyncio

from picow_home_lib import led

print(led._mode, led._rate)


async def main():

    await asyncio.sleep(1)

    led.set_mode(led.Mode.BLINK, 0.5)

    await asyncio.sleep(3)

    led.set_mode(led.Mode.OFF)

    await asyncio.sleep(2)

    led.set_mode(led.Mode.BLINK, 1.0)

    await asyncio.sleep(5)

    try:
        led.set_mode(led.Mode.BLINK)
    except AssertionError:
        print('missing set_mode() parameter threw exception as expected')

asyncio.run(main())
