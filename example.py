import sys

import asyncio
import logging

from picow_home_lib import base, led, log_mem

# set up logging
logging.basicConfig(level=logging.INFO)     # creates handler for console output
log = logging.getLogger(__name__)           # add handler for memory log buffer
log.setLevel(logging.DEBUG)

# add a handler that will log to a memory buffer
handler = log_mem.MemoryLogHandler() # can supply size argurment
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s:%(name)s:%(message)s')
handler.setFormatter(formatter)
log.addHandler(handler)

log.debug('debug')
log.info('logging setup complete')
log.warning('warning')
log.error('test error level')
log.critical('critical')

async def main():
    system = base.base()

    # we have to wait until async loop is running before starting these
    led.set_mode(led.Mode.BLINK, 0.5)

#   await asyncio.sleep(5)

    print(log_mem.get_logs())

asyncio.run(main())
