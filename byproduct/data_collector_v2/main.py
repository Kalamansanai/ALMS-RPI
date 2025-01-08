# import required modules
from flask import Flask, Response
import cv2
import time
import os
from ultralytics import YOLO
import numpy as np
import cv2

app = Flask(__name__)
plates_model = YOLO("plates.pt")

vid = cv2.VideoCapture(0)
vid.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
vid.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

folder = round(time.time() * 1000)
os.mkdir(f"./{folder}")

# Automatic brightness and contrast optimization with optional histogram clipping
def automatic_brightness_and_contrast(image, clip_hist_percent=1):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Calculate grayscale histogram
    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    hist_size = len(hist)

    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index -1] + float(hist[index]))

    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum/100.0)
    clip_hist_percent /= 2.0

    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1

    # Locate right cut
    maximum_gray = hist_size -1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1

    # Calculate alpha and beta values
    alpha = 255 / (maximum_gray - minimum_gray)
    beta = -minimum_gray * alpha

    auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return (auto_result, alpha, beta)


def gen():
    while(True):
        ret, frame = vid.read()
        if not ret:
            print("Can not take frame")
        else:
            try:
                result = plates_model.predict(source=[frame])[0]
                box = result.boxes[0]
                x1, y1, x2, y2 = np.round(box.xyxy[0].numpy()).astype(int)
                frame = frame[y1:y2, x1:x2]

                frame, alpha, beta = automatic_brightness_and_contrast(frame)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Gray


                alpha = 1.0 # Contrast control (1.0-3.0)
                beta = 100 # Brightness control (0-100)
                frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


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



@app.route('/stream')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
