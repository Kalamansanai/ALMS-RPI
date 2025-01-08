import os
import time
import json
import requests
from lib.logger.logger import Log
from lib.other.diagnostics import *
from lib.config.config import Config
from getmac import get_mac_address as gma
from lib.camera.qr_reader import QR_reader


class HTTPClient:

    def POST(self, endpoint, json_data):
        path = "http://{}:{}/{}".format(
            Config.get_conf(["backend", "ip"]),
            Config.get_conf(["backend", "port"]),
            endpoint)
        response = requests.post(path, json=json_data, verify=False)
        Log.debug(f"HTTP/POST {path} response: {response.status_code} {response.reason} Took: {response.elapsed}")
        return response

    def GET(self, endpoint):
        path = "http://{}:{}/{}".format(
            Config.get_conf(["backend", "ip"]),
            Config.get_conf(["backend", "port"]),
            endpoint)
        response = requests.get(path, verify=False)
        Log.debug(f"HTTP/GET {path} response: {response.status_code} {response.reason} Took: {response.elapsed}")
        return response

    def send_event(self, step_id, task_id, result, reason=""):
        data = {}
        data["stepId"] = step_id
        data["taskId"] = task_id
        data["Success"] = result
        if not result:
            data["failureReason"] = reason

        r = self.POST("api/v1/events", data)
        Log.info("Event sent")

    def identification(self):
        id, _ = QR_reader().read()
        #id = 3

        while True:
            try:
                if self.POST(f"api/v1/detectors/{id}/identify", {"macAddress": gma()}).status_code < 300:
                    break
                else:
                    raise Exception("https error code")
            except Exception as ex:
                Log.error("Could not send identification data to server")
                time.sleep(5)
        Log.info("Identification sent")

    def heartbeat(self):
        while True:
            try:
                data = {}
                data["temperature"] = temperature()
                data["storagePercentage"] = storage()
                data["uptime"] = uptime()
                data["cpu"] = cpu()
                data["ram"] = ram()
                r = self.POST(f"api/v1/detectors/{gma()}/heartbeat", data)
                Log.info("Heartbeat sent")
                time.sleep(Config.get_conf(["heartbeat"]))  # Cooldown
            except Exception as ex:
                Log.error("Could not send heartbeat to server")
                time.sleep(5)

    def get_templates(self, id):
        while True:
            try:
                return json.loads(self.GET(f"api/v1/tasks/{id}/objects_and_steps").content.decode("utf-8"))
            except Exception as ex:
                Log.error("Could not get steps and from server")
                time.sleep(5)
