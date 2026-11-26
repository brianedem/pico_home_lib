class line_edit:
    def __init__(self, reader, writer, return_key='\n', eof_key=''):
        self.reader = reader
        self.writer = writer
        self.return_key = return_key
        self.eof_key = eof_key

        self.cmd_history = ['']
        self.history_start = 1
        self.prompt = '> '          # TODO needs to include config.modified flag

    def set_prompt(self, prompt=''):
        if prompt:
            self.prompt = f'{prompt} '
        else:
            prompt = ''
        
    def get_history(self):
        if len(self.cmd_history) == 1:
            return []
        else:
            return enumerate(reversed(self.cmd_history[1:]), self.history_start)

    async def get_line(self):
        command = ''
        command_index = 0
        history_index = 0
        if self.prompt:
            self.writer.write(self.prompt.encode()) # TODO verify that encode() is needed - decode not needed on read
            await self.writer.drain()
        while True:
            key = await self.process_key()
            if key=='':
                return ''
            if key==self.eof_key and command=='':
                return ''

            if key == self.return_key:              # line termination
                self.writer.write(b'\r\n')
                await self.writer.drain()
                command = command.strip()
                if len(command) and len(self.cmd_history)==1 or command != self.cmd_history[1]:
                        self.cmd_history.insert(1, command)
                        if len(self.cmd_history) > 30:
                            self.cmd_history.pop()
                            self.history_start += 1
                return command

            if key == '\033[A':                     # cursor up
                if len(self.cmd_history) > history_index+1:
                    history_index += 1
                    command = self.cmd_history[history_index]
                    command_index = len(command)
                    self.writer.write(b'\r\033[K')      # delete line
                    self.writer.write(self.prompt.encode())
                    self.writer.write(command.encode())
                else:
                    self.writer.write(b'\007')

            elif key == '\033[B':                   # cursor down
                if history_index == 0:
                    self.writer.write(b'\007')
                else:
                    history_index -= 1
                    command = self.cmd_history[history_index]
                    command_index = len(command)
                    self.writer.write(b'\r\033[K')      # delete line
                    self.writer.write(self.prompt.encode())
                    self.writer.write(command.encode())

            elif key == '\033[C':                   # cursor right
                if command_index < len(command):
                    command_index += 1
                    self.writer.write(key.encode())

            elif key == '\033[D':                   # cursor left
                if command_index > 0:
                    command_index -= 1
                    self.writer.write(key.encode())

            elif key == '\010' or key == '\177':    # backspace (destructive)
                if command_index > 0:
                    command_index -= 1
                    command = command[:command_index] + command[command_index+1:]
                    self.writer.write(b'\010\033[P')    # move left, delete one charactor

            elif key == '\033[3~':                  # delete under cursor
                if command_index < len(command):
                    command = command[:command_index] + command[command_index+1:]
                    self.writer.write(b'\033[P')        # delete one charactor

            else:                                   # insert/add some text
                for k in key:
                    if not ord(' ') <= ord(k) <= ord('~'): # MicroPython does not support str.isprintable()
                        continue
                    if command_index != len(command):
                        command = command[:command_index]+k+command[command_index:]
                        self.writer.write(b'\033[@')    # insert one charactor
                        self.writer.write(k.encode())
                        command_index += 1
                    else:
                        command += k
                        command_index += 1
                        self.writer.write(k.encode())

            await self.writer.drain()

    async def process_key(self):
        sequence = ''
        while True:
            key = await self.reader.read(1)
            if not key:
                return ''
            sequence += key
            if len(sequence) == 1:
                if key == '\033':         # looking for leading ESC
                    continue
                else:
                    break
            if len(sequence) == 2:
                if key == '[':          # ESC followed by [
                    continue
                else:
                    break
            if len(sequence) > 2:       # start checking for sequence end charactor
                if ord('@') <= ord(key) <= ord('~'):   # type: ignore
                    break
                else:
                    continue
        return sequence
