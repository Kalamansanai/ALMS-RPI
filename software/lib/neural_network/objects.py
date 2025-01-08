

class Step:

    def __init__(self, json):
        self.id = json["id"]
        self.object_id = json["objectId"]
        self.order_num = json["orderNum"]
        self.expected_initial_state = json["expectedInitialState"]
        self.expected_subsequent_state = json["expectedSubsequentState"]


class Object:

    def __init__(self, json):
        self.id = json["id"]
        self.name = json["name"]
        self.x = json["coordinates"]["x"]
        self.y = json["coordinates"]["y"]
        self.w = json["coordinates"]["width"]
        self.h = json["coordinates"]["height"]
