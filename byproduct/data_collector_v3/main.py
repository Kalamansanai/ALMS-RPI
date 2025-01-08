# import required modules
from flask import Flask, Response
import cv2
import time
import os
import numpy as np
import cv2

app = Flask(__name__)

vid = cv2.VideoCapture(0)
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

folder = round(time.time() * 1000)
os.mkdir(f"./{folder}")



def gen():
    while(True):
        ret, frame = vid.read()
        if not ret:
            print("Can not take frame")
        else:
            try:
                file = round(time.time() * 1000)
                cv2.imwrite(f"{folder}/{file}.jpg", frame)
                print(file, "saved.")
                time.sleep(0.3)

                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            except Exception as ex:
                print("Nincs számlap", ex)



@app.route('/')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
