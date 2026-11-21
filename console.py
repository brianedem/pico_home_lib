# For testing on Linux/OSX
import asyncio
import sys
import termios
import tty

from picow_home_lib import cmd_processor
from picow_home_lib import line_edit

async def console_task():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setcbreak(fd)
        loop = asyncio.get_running_loop()

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        transport, protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout)

        writer = asyncio.StreamWriter(transport, protocol, None, loop)

        le = line_edit.line_edit(reader, writer, eof_key='\x04')
        while True:
            command = await le.get_line()
            if command == '':   # indication of EOF
                break
            command = command.strip()
            if command:
                response = cmd_processor.process(command, le.get_history)
                if response:
                    writer.write(response.encode()+b'\n')
                    await writer.drain()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    raise asyncio.CancelledError

if __name__ == '__main__':
    asyncio.run(console_task())
