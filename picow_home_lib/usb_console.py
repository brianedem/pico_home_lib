import asyncio
import sys

from picow_home_lib import cmd_processor
from picow_home_lib import line_edit

async def console_task():
    # create awaitable sockets - only in MicroPython
    reader = asyncio.StreamReader(sys.stdin)
    writer = asyncio.StreamWriter(sys.stdout)

    # mechanism to provide console echo and command line editing
    le = line_edit.line_edit(reader, writer)
    while True:
        command = await le.get_line()
        command = command.strip()
        if command :
            response = cmd_processor.process(command, le.get_history)
            if response:
                writer.write(response.encode()+b'\n')
                await writer.drain()

