class MockGPIOAdapter:
    def setup_output(self, pin: int) -> None:
        print(f"[mock-gpio] setup output pin {pin}")

    def write(self, pin: int, value: bool) -> None:
        state = "HIGH" if value else "LOW"
        print(f"[mock-gpio] pin {pin} -> {state}")
