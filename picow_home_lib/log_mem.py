import logging

_memory_buffer = []

class MemoryLogHandler(logging.Handler):
    def __init__(self, size=100):
        super().__init__()
        self.buffer_size = size
        # TODO - add console commands for managing log buffer

    def emit(self, record):
        msg = self.format(record)
        _memory_buffer.append(msg)
        if len(_memory_buffer) > self.buffer_size:
            _memory_buffer.pop(0)

def get_logs():
    return _memory_buffer
