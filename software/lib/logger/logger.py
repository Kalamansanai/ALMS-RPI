import inspect
from datetime import datetime


class Log:

    def get_time():
        return datetime.now().strftime("%Y/%d/%m %H:%M:%S")

    def write(msg):
        file = open("./assets/logs/rpi.log", "a")
        file.write(F"{msg}\n")
        file.close()

    def debug(msg):
        msg = f"{Log.get_time()} [{inspect.stack()[1].filename}] DEBUG: {msg}"
        print(msg)
        Log.write(msg)

    def info(msg):
        msg = f"{Log.get_time()} [{inspect.stack()[1].filename}] INFO: {msg}"
        print(msg)
        Log.write(msg)

    def warning(msg):
        msg = f"{Log.get_time()} [{inspect.stack()[1].filename}] WARNING: {msg}"
        print(msg)
        Log.write(msg)

    def error(msg):
        msg = f"{Log.get_time()} [{inspect.stack()[1].filename}] ERROR: {msg}"
        print(msg)
        Log.write(msg)

    def critical(msg):
        msg = f"{Log.get_time()} [{inspect.stack()[1].filename}] CRITICAL: {msg}"
        print(msg)
        Log.write(msg)
