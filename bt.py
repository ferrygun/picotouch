import asyncio
from bleak import BleakScanner, BleakClient

dev_name = "mpy-uart"
_UART_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
_UART_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
_UART_RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

toggle_status=False

async def notification_handler(sender: int, data: bytearray):
    print(f"Received message from {sender}: {data.decode()}")

    global toggle_status

    toggle_status= not toggle_status
    if(toggle_status):
        script = "start_video.scpt"
    else:
        script = "stop_video.scpt"
                                    

    run_applescript(script)



async def discover_device():
    scanner = BleakScanner()
    await scanner.start()
    await asyncio.sleep(3)  # Allow time for scanning
    devices = scanner.discovered_devices

    for dev in devices:
        print(dev.name)
        if dev.name == dev_name:
            print(f"Found {dev_name} at {dev.address}")
            return dev.address

    print(f"{dev_name} not found.")
    return None

async def run(loop):
    while True:
        device_address = await discover_device()
        if not device_address:
            print(f"Retrying in 3 seconds...")
            await asyncio.sleep(3)
            continue

        try:
            async with BleakClient(device_address, loop=loop) as client:
                # Enable notifications on TX characteristic
                await client.start_notify(_UART_TX_UUID, notification_handler)

                print(f"Listening for incoming messages on {_UART_TX_UUID}. Press Ctrl+C to stop.")

                


                while True:
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"Connection failed: {str(e)}")
            print(f"Retrying in 3 seconds...")
            await asyncio.sleep(3)

import subprocess

def run_applescript(script_path):
    try:
        subprocess.run(["osascript", script_path], check=True)
        print('run script')
    except subprocess.CalledProcessError as e:
        print(f"Error executing AppleScript: {e}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
