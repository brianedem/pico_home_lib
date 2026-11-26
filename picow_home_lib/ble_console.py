import asyncio

import aioble
import bluetooth

from picow_home_lib import cmd_processor

# Standard Nordic UART Service (NUS) UUIDs
_UART_SERVICE_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_CHAR_UUID = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E") # Central writes here
_UART_TX_CHAR_UUID = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E") # Peripheral notifies here

# Register GATT server
uart_service = aioble.Service(_UART_SERVICE_UUID)
rx_char = aioble.Characteristic(uart_service, _UART_RX_CHAR_UUID, write=True, write_no_response=True)
tx_char = aioble.Characteristic(uart_service, _UART_TX_CHAR_UUID, read=True, notify=True)
aioble.register_services(uart_service)

class _history:
    def __init__(self):
        self.history = []
        self.start = 1
    def add_command(self, command):
        self.history.append(command)
        if len(self.history) > 30:
            self.history.pop()
            self.start += 1
    def get_history(self):
        return enumerate(self.history, start=self.start)

async def rx_task(connection):
    """Handles incoming serial messages from the connected phone/PC."""
    cmd_history = _history()
    while connection.is_connected():
        try:
            # Wait for the central device to write to the RX characteristic
            await rx_char.written()

            command = rx_char.read().decode("utf-8").strip()
            if command:
                cmd_history.add_command(command)
                response = cmd_processor.process(command, cmd_history.get_history)
                if response:
                    tx_char.notify(connection, response.encode('utf-8'))

        except asyncio.CancelledError:
            break
        except Exception as e:
            print("RX Error:", e)
    
async def ble_console(name):
    """Advertises the BLE console and manages connections."""
    while True:
        print("Advertising BLE UART Console...")
        async with await aioble.advertise(
            250_000, # 250ms interval
            name=name,
            services=[_UART_SERVICE_UUID],
        ) as connection:
            print("Connected to:", connection.device)

            t_rx = asyncio.create_task(rx_task(connection))
            await connection.disconnected()
            t_rx.cancel()

            print("Disconnected.")

if __name__ == '__main__':
    asyncio.run(ble_console('ble_console'))
