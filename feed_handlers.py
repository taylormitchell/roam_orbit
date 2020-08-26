from schedule_handlers import *
from feedback_handlers import *

class ToReview:
    def __init__(self):
        self.keys = ["feed"]

    def update_metadata(self, block_content):
        block_content.set_kv("feed", self.__class__.__name__)

    def get_schedule_handler(self):
        return ExpVarFactor(init_interval=2, factor_short=2, factor_long=3)

    def get_feedback_handler(self):
        return Vote()
    

class ToThink:
    def __init__(self):
        self.keys = ["feed"]

    def update_metadata(self, block_content):
        block_content.set_kv("feed", self.__class__.__name__)

    def get_schedule_handler(self):
        return ExpReset(init_interval=2, init_factor=3)

    def get_feedback_handler(self):
        return ThoughtProvoking()
    
