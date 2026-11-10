class Pin():
    OUT = 'OUT'
    ON = 'ON'
    OFF = 'OFF'
    def __init__(self, port, mode):
        self.led_state = False
        print("Configuring", port, "to", mode)

    def set_led_state(self, state):
        if self.led_state is not state:
            print(f'Setting LED {state}')
            self.led_state = state
    def on(self):
        self.set_led_state(Pin.ON)
    def off(self):
        self.set_led_state(Pin.OFF)
    def toggle(self):
        if self.led_state is Pin.ON:
            self.set_led_state(Pin.OFF)
        else:
            self.set_led_state(Pin.ON)
