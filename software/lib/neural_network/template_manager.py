from lib.config.config import Config
from lib.http.http_client import HTTPClient
from lib.neural_network.objects import Step, Object


class TemplateManager:

    def __init__(self):
        self.client = HTTPClient()
        self.steps = []
        self.objects = []

    def get_templates(self, id):
        res = self.client.get_templates(id)

        for step in res["steps"]:
            self.steps.append(Step(step))
        self.steps.sort(key=lambda x: x.order_num)  # Makes the select faster

        for obj in res["objects"]:
            o = self.transform_coordinates(Object(obj))
            self.objects.append(o)

        #Config().conf["marker"] = res["markerCoordinates"] # NOTICE calibration coordinates save
        #Config.save_config()

    # Return unique order nums
    def get_order_nums(self):
        nums = []
        for step in self.steps:
            if step.order_num not in nums:
                nums.append(step.order_num)
        nums.sort()
        return nums

    def get_steps_by_order_num(self, num):
        steps = []
        for step in self.steps:
            if step.order_num > num:
                break
            elif step.order_num == num:
                steps.append(step)
        return steps

    def get_obj_by_id(self, id):
        for obj in self.objects:
            if str(obj.id) == str(id):
                return obj
        return None

    def remove_step_by_id(self, id):
        for i in range(len(self.steps)):
            if self.steps[i].id == id:
                self.steps.pop(i)
                return True
        return False

    def cleanup(self):
        self.steps = []
        self.objects = []

    # Trasnform template coordinates to different resolution. From smaller to bigger!
    def transform_coordinates(self, object):
        object.x *= Config.get_conf(["camera", "decrease"])
        object.y *= Config.get_conf(["camera", "decrease"])
        object.w *= Config.get_conf(["camera", "decrease"])
        object.h *= Config.get_conf(["camera", "decrease"])

        return object
