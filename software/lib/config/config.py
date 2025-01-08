import os
import json
from lib.logger.logger import Log
import time

import sys


class Config:

    conf = None
    file = "lib/config/rpi.config"
    modified = os.path.getmtime(file)

    @staticmethod
    def get_conf(names):
        while True:
            try:
                if Config.conf is None or os.path.getmtime(Config.file) > Config.modified:
                    Config.load_config()
                    Config.modified = os.path.getmtime(Config.file)
                value = Config.conf
                for name in names:
                    value = value[name]
                return value
            except Exception as ex:
                print("Waiting for config file...")
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno, "\n")


    @staticmethod
    def load_config():
        file = open(Config.file)
        Config.conf = json.load(file)
        file.close()
        Log.info("Config loaded")

    @staticmethod
    def save_config():
        with open(Config.file, "w") as outfile:
            json.dump(Config.conf, outfile)
            Config.version = int(os.path.getmtime(Config.file))
            Log.info("Config saved")