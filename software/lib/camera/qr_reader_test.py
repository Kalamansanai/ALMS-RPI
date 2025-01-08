#import os
#os.chdir("/home/pi/plm-rpi/software")
import cv2
import time
#from lib.logger.logger import Log
#import lib.other.led as led
from camera_opencv import Camera


class QR_reader:
    def read(self):
        #l_state = True
        try:
            while True:
                data, vertices_array, binary_qrcode = cv2.QRCodeDetector(
                ).detectAndDecode(Camera().get_frame())
                if vertices_array is not None and len(data) >= 1:
                    print(f"QR data: {data}")
                    #led.g_on()
                    return data, vertices_array[0]
                else:
                    #if l_state:
                        #led.g_on()
                    #else:
                        #led.g_off()
                    #l_state = not l_state
                    print("There is no QR code")
                    time.sleep(1)
        except Exception as ex:
            print("GEBASZ:")
            print(str(ex))
