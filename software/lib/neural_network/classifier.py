import cv2
import time
import numpy as np
import multiprocessing
import tensorflow.lite as tflite
from lib.config.config import Config
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


class ClassifierLite:

    def __init__(self):
        self.interpreter = None
        self.interpreter = tflite.Interpreter(model_path="./assets/model.tflite", num_threads=multiprocessing.cpu_count())
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.image_size = self.input_details[0]['shape'][2]
        self.classes = Config.get_conf(["cnn", "classes"])
        self.timer = 0

    def predict(self, img):
        input_index = self.interpreter.get_input_details()[0]["index"]
        self.interpreter.set_tensor(input_index, self.preproccess(img))
        self.interpreter.invoke()
        output_details = self.interpreter.get_output_details()

        output_data = self.interpreter.get_tensor(output_details[0]['index'])
        pred = np.squeeze(output_data)

        return self.classes[np.argmax(pred)], max(pred)*100, round(time.time() * 1000) - self.timer


        # COLOR MASK: object feher
        # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV) # Convert to hsv
        # mask = cv2.inRange(hsv,
        #     (Config.get_conf(["hand_mask", "min_blue"]), Config.get_conf(["hand_mask", "min_green"]), Config.get_conf(["hand_mask", "min_red"])),
        #     (Config.get_conf(["hand_mask", "max_blue"]), Config.get_conf(["hand_mask", "max_green"]), Config.get_conf(["hand_mask", "max_red"]))) # Apply color mask by min-max values
        # mask = cv2.erode(mask, None, iterations=Config.get_conf(["hand_mask", "closing"])) # Close gaps
        # mask = cv2.dilate(mask, None, iterations=Config.get_conf(["hand_mask", "opening"]))

        # if np.count_nonzero(mask == 255) / (len(mask)*len(mask[0])) *100 > 5: # 5%-nál több maszk pixel van
        #     return self.classes[1], 100, 0
        # else:
        #     return self.classes[0], 100, 0

    # GRAYSCALE
    def preproccess(self, img):
        self.timer = round(time.time() * 1000)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # GRAYSCALE
       # img = cv2.equalizeHist(img) # AUTO BRIGHTNESS-CONTRAST
        img = (img/255.0).astype("float32")
        img = cv2.resize(img, (self.image_size, self.image_size))
        img = np.expand_dims(img, axis=2)  # One channel

        return np.array(np.expand_dims(img, 0))
