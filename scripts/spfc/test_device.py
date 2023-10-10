import tango

dp = tango.DeviceProxy("SPFRx/rxpu/controller")

print(dp.get_attribute_list())