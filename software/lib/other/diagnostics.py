import os
import time
import psutil
from lib.config.config import Config


# Uptime in seconds
def uptime():    
    return str(int(time.time() - psutil.boot_time()))


def storage():
    try:
        return round(get_folder_size("./assets/collected_data") / (Config.get_conf(["cnn", "max_size"])) * 100)
    except:
        return 0


def temperature():
    try:
        return int(psutil.sensors_temperatures()['cpu_thermal'][0].current)
    except:
        return None


def cpu():
    return psutil.cpu_percent(interval=5)


def ram():
    return psutil.virtual_memory().percent


def get_folder_size(path):
    size = 0
    with os.scandir(path) as it:
        for entry in it:
            if entry.is_file():
                size += entry.stat().st_size
            elif entry.is_dir():
                size += get_folder_size(entry.path)
    return size
