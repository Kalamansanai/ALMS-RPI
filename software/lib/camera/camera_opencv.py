import cv2
import time
import math
import imutils
import numpy as np
import lib.other.led as led
import numpy.linalg as lin
from lib.logger.logger import Log
from lib.config.config import Config
from lib.camera.base_camera import BaseCamera
from cv2 import aruco

class Camera(BaseCamera):
    video_source = Config.get_conf(["camera", "source"])
    logo = cv2.imread('./assets/hand.png')

    def __init__(self):
        super(Camera, self).__init__()

    @staticmethod
    def frames():
        camera = cv2.VideoCapture(Camera.video_source)
        camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # manual mode
        camera.set(cv2.CAP_PROP_EXPOSURE, Config.get_conf(["camera", "exposure"]))
        #camera.set(cv2.CV_CAP_PROP_SATURATION, 1)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.get_conf(["camera", "width"]))
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.get_conf(["camera", "height"]))
        #camera._set_awb_gains((4,4))

        if not camera.isOpened():
            Log.error("Could not start camera.")
        else:
            Log.info(f"Camera started in {int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))} mode")

        while True:
            ret, img = camera.read()

            if type(Config.get_conf(["camera", "source"])) is str:  # Webcam is int, video file path is str
                if not ret:
                    Log.debug("Video frame did not captured or video restarted.")
                    camera.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
                    continue
            else:
                if not ret:
                    Log.error("Failed to capture frame.")

            yield img

    @staticmethod
    def decrease(frm):  # Stream/snapshot resolution different than the camera capture resolution
        return cv2.resize(
            frm,
            (int(round(frm.shape[1] / 2)),
             int(round(frm.shape[0] / 2))),
            interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def calibrate(frm):
        if len(Config.get_conf(["marker"])) >= 0:
            h, w, _ = frm.shape
            
            marker_dict = aruco.getPredefinedDictionary(0)
            parameters = cv2.aruco.DetectorParameters()
            detector = cv2.aruco.ArucoDetector(marker_dict, parameters)
            sharpened_image = frm
            sharpened_image = cv2.GaussianBlur(frm, (5, 5), 0)
            cv2.addWeighted(frm, 1.5, sharpened_image, -0.5, 0, sharpened_image)
            grayFrame = cv2.cvtColor(sharpened_image, cv2.COLOR_BGR2GRAY)
            corners, markerIds, reject = detector.detectMarkers(grayFrame)
            
            topLeftMarkerCenterX = 0
            topLeftMarkerCenterY = 0
            bottomRightMarkerCenterX = 0
            bottomRightMarkerCenterY = 0
            bottomLeftMarkerCenterX = 0
            bottomLeftMarkerCenterY = 0
            if corners:
              for ids, marker in zip(markerIds, corners):
                marker = marker.reshape((4,2))
                
                (topLeft, topRight, bottomRight, bottomLeft) = marker
                topRight = [int(topRight[0]), int(topRight[1])]
                bottomRight = [int(bottomRight[0]), int(bottomRight[1])]
                bottomLeft = [int(bottomLeft[0]), int(bottomLeft[1])]
                topLeft = [int(topLeft[0]), int(topLeft[1])]
                
                centerpointX = (topRight[0] + bottomLeft[0])/2
                centerpointY = (topRight[1] + bottomLeft[1])/2
                
                if(ids == Config.get_conf(["markerIDs"])["topLeft"]):
                    topLeftMarkerCenterX = centerpointX
                    topLeftMarkerCenterY = centerpointY
                    cv2.line(frm, topLeft, topRight, (0, 255, 0), 2)
                    cv2.line(frm, topRight, bottomRight, (0, 255, 0), 2)
                    cv2.line(frm, bottomRight, bottomLeft, (0, 255, 0), 2)
                    cv2.line(frm, bottomLeft, topLeft, (0, 255, 0), 2)
                if(ids == Config.get_conf(["markerIDs"])["bottomRight"]):
                    bottomRightMarkerCenterX = centerpointX
                    bottomRightMarkerCenterY = centerpointY
                    cv2.line(frm, topLeft, topRight, (0, 255, 0), 2)
                    cv2.line(frm, topRight, bottomRight, (0, 255, 0), 2)
                    cv2.line(frm, bottomRight, bottomLeft, (0, 255, 0), 2)
                    cv2.line(frm, bottomLeft, topLeft, (0, 255, 0), 2)
                if(ids == Config.get_conf(["markerIDs"])["bottomLeft"]):
                    bottomLeftMarkerCenterX = centerpointX
                    bottomLeftMarkerCenterY = centerpointY
                    cv2.line(frm, topLeft, topRight, (0, 255, 0), 2)
                    cv2.line(frm, topRight, bottomRight, (0, 255, 0), 2)
                    cv2.line(frm, bottomRight, bottomLeft, (0, 255, 0), 2)
                    cv2.line(frm, bottomLeft, topLeft, (0, 255, 0), 2)

            topLeftMarkerCenter = [int(topLeftMarkerCenterX), int(topLeftMarkerCenterY)]
            bottomRightMarkerCenter = [int(bottomRightMarkerCenterX), int(bottomRightMarkerCenterY)]
            bottomLeftMarkerCenter = [int(bottomLeftMarkerCenterX), int(bottomLeftMarkerCenterY)]
            
            transformtopLeft = [int(Config.get_conf(["marker"])[0]["X"]), int(Config.get_conf(["marker"])[0]["Y"])]
            transformbottomRight = [Config.get_conf(["marker"])[1]["X"], Config.get_conf(["marker"])[1]["Y"]]
            transformbottomLeft = [Config.get_conf(["marker"])[2]["X"], Config.get_conf(["marker"])[2]["Y"]]
            
            pts2 = np.float32([topLeftMarkerCenter, bottomRightMarkerCenter, bottomLeftMarkerCenter])
            pts1 = np.float32([transformtopLeft, transformbottomRight, transformbottomLeft])
            
            M = cv2.getAffineTransform(pts2, pts1)
            frm = cv2.warpAffine(frm, M, (w, h))
            return True, frm
                
        return False, frm


    @staticmethod
    def mask(frm):
        #return  frm , False # WARNING Skip masking
        try:
            hsv = cv2.cvtColor(frm, cv2.COLOR_BGR2HSV) # Convert to hsv
            mask = cv2.inRange(hsv,
                (Config.get_conf(["hand_mask", "min_blue"]), Config.get_conf(["hand_mask", "min_green"]), Config.get_conf(["hand_mask", "min_red"])),
                (Config.get_conf(["hand_mask", "max_blue"]), Config.get_conf(["hand_mask", "max_green"]), Config.get_conf(["hand_mask", "max_red"]))) # Apply color mask by min-max values
            mask = cv2.erode(mask, None, iterations=Config.get_conf(["hand_mask", "closing"])) # Close gaps
            mask = cv2.dilate(mask, None, iterations=Config.get_conf(["hand_mask", "opening"]))

            # Try to separate hands from other objects
            contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)#[-2:]
            if len(contours) > 0:
                cont = max(contours, key = cv2.contourArea)
                x,y,w,h=cv2.boundingRect(cont)

                if (w*h / (frm.shape[0]*frm.shape[1]))*100 > Config.get_conf(["hand_mask", "treshold"]): # object bigger than treshold

                    # Add watermark to image
                    led.r_on()
                    h_logo, w_logo, _ = Camera.logo.shape
                    h_img, w_img, _ = frm.shape
                    center_y = int(h_img/2)
                    center_x = int(w_img/2)
                    top_y = center_y - int(h_logo/2)
                    left_x = center_x - int(w_logo/2)
                    bottom_y = top_y + h_logo
                    right_x = left_x + w_logo
                    destination = frm[top_y:bottom_y, left_x:right_x]
                    result = cv2.addWeighted(destination, 1, Camera.logo, 1, 0)
                    frm[top_y:bottom_y, left_x:right_x] = result
                    

                    return frm, True
                else:
                    led.r_off()
                    return frm, False
            else:
                led.r_off()
                return frm, False
        except Exception as ex:
            Log.error(f"Masking error! \n{ex}")
