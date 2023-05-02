#!/usr/bin/env python
import asyncio
from asyncio.subprocess import Process


async def ping_host(host):
    ip = host[0]
    ping_command = ["ping", "-c", "1", ip]
    process: Process = await asyncio.create_subprocess_exec(
        *ping_command, stdout=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    ping_result = process.returncode
    if ping_result == 0:
        print(f"    {host[0]}\t - {host[1]}")
    else:
        print(f"Ping result code: {ping_result}")
        print(f"IP address {host[0]} not reachable - check if {host[1]} is online")


async def main():
    hosts_list = [
        [
            "10.165.3.1",
            "R&S Signal Generator SMB100A",
            "za-itf-signal-generator.ad.skatelescope.org",
        ],
        [
            "10.165.3.2",
            "Tektronix Oscilloscope MSO64",
            "za-itf-oscilloscope.ad.skatelescope.org",
        ],
        ["10.165.3.3", "Tektronix AWG", "za-itf-awg.ad.skatelescope.org"],
        [
            "10.165.3.4",
            "Anritsu Spectrum Analyser",
            "za-itf-spectrum-analyser.ad.skatelescope.org",
        ],
        ["10.165.3.5", "GwInstek PSU", "za-itf-psu.ad.skatelescope.org"],
        [
            "10.165.3.6",
            "RCDAT-8000-30 Programmable Attenuator",
            "za-itf-attenuator.ad.skatelescope.org",
        ],
        ["10.165.3.7", "za-itf-sw (Ubuntu)", "za-itf-sw.ad.skatelescope.org"],
        ["10.165.3.8", "za-itf-dev1 (Ubuntu)", "za-itf-dev1.ad.skatelescope.org"],
        ["10.165.3.9", "za-itf-dev2 (Windows)", "za-itf-dev2.ad.skatelescope.org"],
        [
            "10.165.3.10",
            "Keysight Time Interval Counter",
            "za-itf-tic.ad.skatelescope.org",
        ],
        ["10.165.3.11", "Raspberry Pi (ITF)", "za-itf-pi.ad.skatelescope.org"],
        ["10.165.3.12", "GPS", "za-itf-gps.ad.skatelescope.org"],
        ["10.165.3.13", "NTP", "za-itf-ntp.ad.skatelescope.org"],
    ]
    tasks = [asyncio.create_task(ping_host(host)) for host in hosts_list]

    print("Pinging the folowing hosts:")

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
