import time
from tango.server import Device, device_property, attribute, command, pipe


class Clock(Device):

    model = device_property(dtype=str)

    @attribute
    def time(self):
        return time.time()

    @command(dtype_in=str, dtype_out=str)
    def strftime(self, format):
        return time.strftime(format)

    @pipe
    def info(self):
        return ("Information", dict(manufacturer="Tango", model=self.model, version_number=123))


if __name__ == "__main__":
    Clock.run_server()
