""" Light Client """
import logging
from os import getenv, getcwd
from datetime import datetime
from time import localtime, strftime
import time
import tango
import sys
import signal
import os

logger = logging.getLogger("event-subscriber")
callback_counter = 0
callback_3_counter = 0
print_event_rate = getenv("EVENT_PRINT_RATE")
high_pub_rate_event_data = []
low_pub_rate_event_data = []

time_now = localtime()
date = strftime("%Y%m%d", time_now)
time_now = strftime("%H%M%S", time_now)
logs_dir = f"{os.getcwd()}/event_logs"
high_pub_rate_file_path = f"{logs_dir}/high-pub-{date}-{time_now}.log"
low_pub_rate_file_path = f"{logs_dir}/low-pub-{date}-{time_now}.log"
os.makedirs(logs_dir, exist_ok=True)

def timeval_to_datetime(time_val):
    sec = time_val.tv_sec
    nsec = time_val.tv_nsec
    usec = time_val.tv_usec
    time_datetime = datetime.fromtimestamp(sec+usec/1e6+nsec/1e9)
    return time_datetime

def print_metrics(event, print_event_rate):
    callback_time = datetime.now()
    logger.info(f"{event}")
    print(f"{event}")
    pub_time = timeval_to_datetime(event.attr_value.time)
    reception_time = timeval_to_datetime(event.reception_date)
    print(f"Latency: {reception_time - pub_time}")    
    print(f"Callback - Reception: {callback_time - reception_time}")
    
def high_pub_rate_callback(event):
    """callback"""
    global event_data
    global callback_counter
    global print_event_rate

    event_string = f"{event.reception_date.totime()}    {event.attr_name.split('/')[-1]}    {event.attr_value.value}"
    high_pub_rate_event_data.append(event_string)

    callback_counter = callback_counter + 1

    if (not print_event_rate) or (print_event_rate and (callback_1_counter == print_event_rate)):
        callback_1_counter = 0
        print_metrics(event, print_event_rate)

    if event.err:
        sys.exit()

def low_pub_rate_callback(event):
    global low_pub_rate_event_data

    event_string = f"{event.reception_date.totime()}    {event.attr_name.split('/')[-1]}    {event.attr_value.value}"

    low_pub_rate_event_data.append(event_string)

    print_metrics(event, None)

    if event.err:
        sys.exit()

def do_nothing_callback(event):
    pass


def signal_handler(signal, frame):
    with open(high_pub_rate_file_path, 'a') as file:
        file.write('\n'.join(high_pub_rate_event_data) + '\n')

    with open(low_pub_rate_file_path, 'a') as file:
        file.write('\n'.join(low_pub_rate_event_data) + '\n')

    print('Logs written to file')

    sys.exit(0)

# Set the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    attr_name = getenv("ATTR_NAME")

    try:
        attr_proxy = tango.AttributeProxy(attr_name)
        attr_2_proxy = tango.AttributeProxy("tango://tango-databaseds.integration-dish-lmc-ska001.svc.miditf.internal.skao.int:10000/mid-dish/ds-manager/ska001/achievedPointing")
        id = attr_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, high_pub_rate_callback)
        id_2 = attr_2_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, low_pub_rate_callback)
        for i in range(20000):
            id = attr_proxy.subscribe_event(tango.EventType.CHANGE_EVENT, do_nothing_callback)
    except Exception as e:
        logging.error(f"exception: {e}")
    while True:  # keep container running
        time.sleep(1)