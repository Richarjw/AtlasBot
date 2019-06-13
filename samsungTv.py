import samsungctl
import time

config = {
    "name": "Samsung",
    "description": "TV",
    "id": "",
    "host": "192.168.1.220",
    "method": "legacy",
    "port": 55000,
    "timeout": 0,
}


with samsungctl.Remote(config) as remote:
    for i in range(10):
        remote.control("KEY_MENU")
        time.sleep(0.5)