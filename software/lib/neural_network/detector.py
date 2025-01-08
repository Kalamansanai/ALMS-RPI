import os
import cv2
import time
import random
from threading import Thread
from itertools import groupby
from collections import Counter
from lib.logger.logger import Log
from lib.config.config import Config
from lib.camera.camera_opencv import Camera
from lib.http.http_client import HTTPClient
from lib.neural_network.classifier import ClassifierLite
from lib.neural_network.template_manager import TemplateManager


class Detector:

    def __init__(self):
        self.running = False
        self.paused = False
        self.classifer = ClassifierLite()
        self.client = HTTPClient()
        self.manager = TemplateManager()
        self.det_history = {}
        self.prev_frame_time = 0
        self.new_frame_time = 0
        self.prev_det_time = 0
        self.new_det_time = 0
        self.dps = 0

    def detect(self, id):
        self.manager.get_templates(id)

        self.clear_history()

        # Iterate on all order numbers. Order number not unique!. Same order number has to be watched at the same time
        for num in self.manager.get_order_nums():  # Get all unique urder number
            while self.running and len(self.manager.get_steps_by_order_num(num)) > 0:
                if not self.paused:
                    frame = Camera().get_frame()
                    success, frame = Camera().calibrate(frame)
                    if success:
	                    # Get all steps. (Ordered)
	                    for step in self.manager.get_steps_by_order_num(num):
	                        obj = self.manager.get_obj_by_id(step.object_id)

	                        image = self.crop_template(frame, obj)

	                        # Only run detection when there is no hand on the frame
	                        _, uncertain_mask = Camera().mask(frame)
	                        if not uncertain_mask:
	                            result, confidence, took = self.classifer.predict(image)
	                            self.step_dps()
	                        else:
	                            result = "Uncertain"
	                            confidence = 100
	                            took = 0

	                        if not self.false_frame(obj, result):
	                            Log.info(f"Detected step {step.id}, order number {step.order_num} on object {obj.id} with {result} class, {round(confidence, 3)}% confidence, under {took} ms.")
	                            self.send_respone(step, id, result, obj)
	                            self.collect_data(image, result, confidence)
	                        else:
	                            Log.info("False frame detection active. "+str(Config.get_conf(["cnn", "false_frames"]))+" frames has to be the same")

                Log.info(f"DPS: {self.dps}")

        Log.info("Detection job finished")
        self.running = False
        self.paused = False
        self.manager.cleanup()

    def clear_history(self):
        self.det_history = {}
        for d in self.manager.objects:
            self.det_history[d.id] = [None] * Config.get_conf(["cnn", "false_frames"])

    # Store frames, check if all is the same
    def false_frame(self, obj, result):
        self.det_history[obj.id].append(result)
        self.det_history[obj.id].pop(0)
        g = groupby(self.det_history[obj.id])
        return next(g, False) and not next(g, True)

    # Send the correct response to server.
    def send_respone(self, step, task_id, result, obj): # TODO Init state stuff
        if step.expected_subsequent_state == result:
            self.client.send_event(step.id, task_id, True)
            self.manager.remove_step_by_id(step.id)

    def start(self, id):
        if not self.running:
            Log.info("Detector starting...")
            self.running = True
            self.paused = False
            Thread(target=self.detect, args=(id, )).start()
        else:
            Log.warning("Start? Detector already running! If not, try resume")

    def stop(self):
        if self.running:
            Log.info("Detector stopping...")
            self.running = False
        else:
            Log.warning("Stop? Detector not running!")

    def pause(self):
        if not self.paused and self.running:
            Log.info("Detector paused")
            self.paused = True
        else:
            Log.warning("Pause? Detector already paused or stopped!")

    def resume(self):
        if self.paused and self.running:
            Log.info("Detector resume")
            self.paused = False
        else:
            Log.warning("Resume? Detector not paused or not even running")

    # TODO legyen egy max megabyte érték amit ha elérnek a mentett képek, töröljön random képeket mentés leőtt
    # Save the image or free up some space and than save
    def collect_data(self, img, result, confidence):
        if Config.get_conf(["cnn", "max_size"]) > 0:
            if confidence < Config.get_conf(["cnn", "threshold_max"]) and confidence > Config.get_conf(["cnn", "threshold_min"]):
                size, counts = self.get_folder_size("./assets/collected_data")
                if size > Config.get_conf(["cnn", "max_size"]):
                    Log.warning("Collected data size limit reached.")
                    if counts[result] > 1:
                        counts[result] = random.randint(0, counts[result]-1)

                cv2.imwrite(f"./assets/collected_data/{result}/{counts[result]+1}.jpg", img)
                Log.info(f"Data saved about prediction")

    def get_folder_size(self, path):
        size = 0
        counts = {}
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    size += entry.stat().st_size
                    if counts.__contains__(entry.path.split("/")[-2]):
                        counts[entry.path.split("/")[-2]] += 1
                    else:
                        counts[entry.path.split("/")[-2]] = 0
                elif entry.is_dir():
                    s, c = self.get_folder_size(entry.path)
                    size += s
                    if c.__contains__(entry.path.split("/")[-1]):
                        c[entry.path.split("/")[-1]] += 1
                    else:
                        c[entry.path.split("/")[-1]] = 0
                    counts.update(c)
        return size, counts

    def crop_template(self, image, step):
        return image[step.y:step.y+step.h, step.x:step.x+step.w]

    # Detections per second
    def step_dps(self):
        self.new_det_time = time.time()
        self.dps = round(1/(self.new_det_time-self.prev_det_time), 2)
        self.prev_det_time = self.new_det_time
