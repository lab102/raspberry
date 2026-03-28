class RaspberryGPIOAdapter:
    def setup_output(self, pin: int) -> None:
        # Replace this placeholder with a concrete GPIO library integration
        # such as gpiozero or RPi.GPIO when deploying to hardware.
        print(f"[raspberry-gpio] setup output pin {pin}")

    def write(self, pin: int, value: bool) -> None:
        state = "HIGH" if value else "LOW"
        print(f"[raspberry-gpio] pin {pin} -> {state}")
