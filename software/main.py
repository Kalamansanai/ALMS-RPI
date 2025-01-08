import os
#os.chdir("/home/pi/plm-rpi/software/")
import json
import cv2
import sys
import math
import time
import shutil
import requests
import platform
import numpy as np
import lib.other.led as led
from threading import Thread
# from waitress import serve # For production server
from lib.logger.logger import Log
from lib.config.config import Config
from lib.camera.qr_reader import QR_reader
from lib.http.http_client import HTTPClient
from lib.camera.camera_opencv import Camera
from lib.neural_network.detector import Detector
from flask import Flask, request, send_file, make_response, Response

app = Flask(__name__)
det = Detector()
client = HTTPClient()


@app.route('/collect', methods=['GET'])  # Zip the collected images, delete the raw images, return zip
def collect():
    if request.method == 'GET' and request.remote_addr == Config.get_conf(["backend", "ip"]):
        if det.running:  # "make_archive" function locks the folder -> config and other files not reachable -> stop needed
            return {"msg": "You can only download the data when the detector stopped!"}, 400
        else:
            Log.info("Sendig collected data to backend...")
            shutil.make_archive("./assets/data", 'zip', "./assets/collected_data")
            for path, subdirs, files in os.walk("./assets/collected_data"):
                for name in files:
                    os.remove(os.path.join(path, name))
            return send_file('./assets/data.zip', as_attachment=True)
    return {"msg": "Wrong request, or you have no access"}, 400


@app.route('/log', methods=['GET'])  # Send the log file
def log():
    if request.method == 'GET' and request.remote_addr == Config.get_conf(["backend", "ip"]):
        Log.info("Sendig log file to backend...")
        return send_file('./assets/logs/rpi.log', as_attachment=True)
    return {"msg": "Wrong request, or you have no access"}, 400


def decode_command(cmd, param):
    if cmd == "restart":
        # TODO REBOOT DEVICE
        pass
    elif cmd == "start":
        det.start(param)
    elif cmd == "stop":
        det.stop()
    elif cmd == "pause":
        det.pause()
    elif cmd == "resume":
        det.resume()


@app.route('/command', methods=['POST'])
def command():
    if request.method == 'POST' and request.remote_addr == Config.get_conf(["backend", "ip"]):
        decode_command(json.loads(request.data.decode("utf-8"))["msg"], json.loads(request.data.decode("utf-8"))["task_id"])
        return {"msg": "Command recieved"}, 200
    return {"msg": "Wrong request, or you have no access"}, 400


@app.route('/snapshot', methods=['GET'])  # Return basic or calibrated snapshot
def snapshot():
    if request.method == 'GET' and request.remote_addr == Config.get_conf(["backend", "ip"]):
        frame = Camera().get_frame()
        frame, uncertain = Camera().mask(frame)
        if not uncertain:
            success, frame = Camera().calibrate(frame)
        #corners, _, _ = cv2.aruco.detectMarkers(frame, cv2.aruco.Dictionary_get(cv2.aruco.DICT_4X4_50), parameters=cv2.aruco.DetectorParameters_create())
        #if len(corners) > 0: # marker present
         # corner = corners[0].reshape((4,2))
          #(topLeft, topRight, bottomRight, bottomLeft) = corner
          #topRight = [int(topRight[0]), int(topRight[1])]
          #bottomRight = [int(bottomRight[0]), int(bottomRight[1])]
          #bottomLeft = [int(bottomLeft[0]), int(bottomLeft[1])]
          #topLeft = [int(topLeft[0]), int(topLeft[1])]
        frame = Camera().decrease(frame)
        binary = cv2.imencode('.jpg', frame)[1].tobytes()
        response = make_response(binary)
        response.headers.set('Content-Type', 'image/jpeg')
        response.headers.set('Content-Disposition', 'attachment', filename='snapshot.jpg')
        response.headers['Marker-Coordinates'] = [0, 0, 0, 0]
        return response
    return {"msg": "Wrong request, or you have no access"}, 400


def gen(camera):
    frame_rate = 15
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        frame = camera.get_frame()

        if time_elapsed > 1./frame_rate:
            prev = time.time()
            frame, uncertain = camera.mask(frame)
            if not uncertain:
               success, frame = camera.calibrate(frame)
            frame = camera.decrease(frame)
            frame = cv2.imencode('.jpg', frame)[1].tobytes()
            yield (b'--frame\r\n'
                b'Content-Type:image/jpeg\r\n'
                b'Content-Length: ' + f"{len(frame)}".encode() + b'\r\n'
                b'\r\n' + frame + b'\r\n')


@app.route('/stream')  # Provide live stream
def video_feed():
    if request.method == 'GET' and request.remote_addr == Config.get_conf(["backend", "ip"]):
        return Response(gen(Camera()), mimetype='multipart/x-mixed-replace; boundary=frame')
    return {"msg": "Wrong request, or you have no access"}, 400


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    requests.packages.urllib3.util.connection.HAS_IPV6 = False

    Log.info(f"Starting up code_v"+Config.get_conf(["code_version"])+" with model_v"+Config.get_conf(["model_version"]))
    Log.debug(f"System information: {platform.uname().system}, {platform.uname().release}")
    Log.debug(f"Python version: {sys.version}")

    # Startup stuff
    led.setup()
    Thread(target=client.heartbeat).start()
    client.identification()
    #det.start(1) # Test

    # serve(app, host="0.0.0.0", port=8080) # For production server
    app.run(debug=False, host="0.0.0.0", port=3000)
