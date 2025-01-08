from flask import Flask, Response, render_template, request
from flask_cors import CORS
import time
import numpy as np
import cv2
# 154, 85, 163, 4close

app = Flask(__name__)
CORS(app)

video = cv2.VideoCapture(0)
video.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # manual mode


video.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
video.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

mi_b = 0
mi_g = 0
mi_r = 0

ma_b = 255
ma_g = 255
ma_r = 255

x_min = 0
y_min = 0
x_max = 0
y_max = 0

closing = 0
opening = 0

trashold = 0

def white_balance(img):
    result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    avg_a = np.average(result[:, :, 1])
    avg_b = np.average(result[:, :, 2])
    result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
    result = cv2.cvtColor(result, cv2.COLOR_LAB2BGR)
    return result

@app.route('/')
def index():
    return render_template('index.html')

def gen(video):
    global mi_b
    global mi_g
    global mi_r

    global ma_b
    global ma_g
    global ma_r

    global x_min
    global y_min
    global x_max
    global y_max

    global closing
    global opening

    global trashold

    font = cv2.FONT_HERSHEY_SIMPLEX
    org = (0, 25)
    fontScale = 1
    color = (3, 186, 252)
    thickness = 2
    prev_frame_time = 0
    new_frame_time = 0
    while True:
        #time.sleep(0.5)
        success, image = video.read()

        if not success:
            video.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
        else:
            #image = cv2.GaussianBlur(image, (11,11), 0) # Homályosítás segíthet. próbáld ki

            # img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV) # Kontrasztolás
            # img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
            # image = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)



            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            masked = cv2.inRange(hsv_image, (mi_b, mi_g, mi_r), (ma_b, ma_g, ma_r)) # color mask
            invert_masked = cv2.bitwise_not(masked) # Invert mask

            # Close gaps
            masked = cv2.erode(masked, None, iterations=closing)
            masked = cv2.dilate(masked, None, iterations=opening)

            contours, _ = cv2.findContours(masked.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2:]

            if len(contours) > 0:
                cont = max(contours, key = cv2.contourArea)

                x,y,w,h=cv2.boundingRect(cont)

                rect = cv2.minAreaRect(cont)
                box = cv2.boxPoints(rect)
                box = np.int64(box)
                M = cv2.moments(cont)
                if M["m10"] > 0 and M["m00"] > 0 and M["m01"]  > 0 and M["m00"] > 0:
                    center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                    cv2.circle(image, center, 5, (255, 0, 255), -1)

                if (w*h / (image.shape[0]*image.shape[1]))*100 > trashold:
                    cv2.rectangle(image,(x,y), (x+w,y+h), (0,255,0), 2)
                else:
                    cv2.rectangle(image,(x,y), (x+w,y+h), (255,0,0), 2)
                #cv2.putText(image, str(i+1), (x,y+h), font, 1, (0,255,255), 2, cv2.LINE_AA)

            masked = cv2.cvtColor(masked,cv2.COLOR_GRAY2RGB) # add the 3th channel
            image = cv2.hconcat([image, masked])




            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            image = cv2.putText(image, "FPS: "+str(round(fps, 3)), org, font, fontScale, color, thickness, cv2.LINE_AA)
            prev_frame_time = new_frame_time

            ret, jpeg = cv2.imencode('.jpg', image)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    global video
    return Response(gen(video), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/crop/', methods=['GET', 'POST'])
def crop():
    global x_min
    global y_min
    global x_max
    global y_max

    data=request.form

    name = data["name"]
    x = data["x"]
    y = data["y"]

    print("-->", name, x, y)

    if name == "left":
        x_min = int(x)
        y_min = int(y)
    elif name == "right":
        x_max = int(x)
        y_max = int(y)

    return "OK"

@app.route('/command/', methods=['GET', 'POST'])
def command():
    global mi_b
    global mi_g
    global mi_r

    global ma_b
    global ma_g
    global ma_r

    global closing
    global opening

    global video

    global trashold

    data=request.form
    print("-->", data)

    name = data["name"]
    value = data["value"]

    if name == "mib":
        mi_b = int(value)
    elif name == "mig":
        mi_g = int(value)
    elif name == "mir":
        mi_r = int(value)
    elif name == "mab":
        ma_b = int(value)
    elif name == "mag":
        ma_g = int(value)
    elif name == "mar":
        ma_r = int(value)
    elif name == "cls":
        closing = int(value)
    elif name == "opn":
        opening = int(value)
    elif name == "cam":
        print("EXP", value)
        video.set(cv2.CAP_PROP_EXPOSURE, int(value))
    elif name == "trash":
        trashold = int(value)

    return 'OK'

if __name__ == '__main__':
    app.run(host='192.168.0.111', port=3000, threaded=True)
