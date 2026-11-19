import sys

import asyncio
import logging

from picow_home_lib import base, led, log_mem

sys.path.append('picow_home_lib')
tests = ''

# set up a default logger to the USB console
logging.basicConfig(level=logging.INFO)

# set up a logger to a memory buffer
handler = log_mem.MemoryLogHandler()
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s:%(name)s:%(message)s')
handler.setFormatter(formatter)
log = logging.getLogger(__name__)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

if 'LOGGING' in tests:
    log.debug('debug')
    log.info('logging setup complete')
    log.warning('warning')
    log.error('test error level')
    log.critical('critical')

if 'LED' not in tests:
    led.disable()

asyncio.run(base.base(), debug=True)
