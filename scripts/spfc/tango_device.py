from tango.server import (
    Device,
    device_property,
    run
)

class SpfcLocation(Device):
# Mandatory properties work only when a TANGO_HOST with a TangoDB is available
# for this device.
    My_mandatory_device_property = device_property(
        dtype = 'double',
        mandatory = True
    )

def main(args = None, **kwargs):
    return run((SpfcLocation,), **kwargs)

if __name__ == '__main__':
    main()