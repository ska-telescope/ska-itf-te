import tango

dp = tango.DeviceProxy("spfrx/rxpu/controller")

print(dp.get_attribute_list())