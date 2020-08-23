from roam.content import *

class FeedbackHandler:
    def __init__(self, responses):
        self.responses = responses
        self.counter_keys = [f"{r}_count" for r in self.responses] + ["total_count"]
        self.response_buttons = [Button(r) for r in self.responses]
        self.keys = ["feedback"] + self.counter_keys 

    def update_metadata(self, block_content, btn_loc="before kvs"):
        self.add_handler_name(block_content)
        self.add_counters(block_content)
        self.insert_buttons(block_content, btn_loc)

    def add_response(self, block_content, response_num):
        counter_key = self.counter_keys[response_num]
        res_counter = block_content.get_kv(counter_key)
        res_counter.value += 1
        tot_counter = block_content.get_kv("total_count")
        tot_counter.value += 1

    def add_handler_name(self, block_content):
        block_content.set_kv("feedback", self.__class__.__name__)

    def response_num_to_name(self, response_num):
        return self.responses[response_num]

    def remove_buttons(self, block_content):
        idx = block_content.index(self.response_buttons[0])
        for button in self.response_buttons:
            block_content.remove(button)
        return idx

    def insert_buttons(self, block_content, loc="before kvs", allow_duplicate=False):
        if loc=="before kvs":
            for i,item in enumerate(block_content.block_items):
                if type(item)==KeyValue:
                    break
            loc = i
        if loc is None or loc==-1: 
            for i, button in enumerate(self.response_buttons):
                if not allow_duplicate and block_content.get(button):
                    continue
                block_content.add_kv(button)
        else:
            for i, button in enumerate(self.response_buttons):
                if not allow_duplicate and block_content.get(button):
                    continue
                block_content.insert(loc+(2*i), button)
                block_content.insert(loc+(2*i+1), String(" "))

    def add_counters(self, block_content):
        for key in self.counter_keys:
            block_content.set_default_kv(key, 0)


class Vote(FeedbackHandler):
    def __init__(self):
        responses = ["↑","↓"]
        super().__init__(responses)


class ThoughtProvoking(FeedbackHandler):
    def __init__(self):
        responses = ["thoughts", "none"]
        super().__init__(responses)


class OldThoughtProvoking(FeedbackHandler):
    def __init__(self):
        responses = ["thought-provoking", "not"]
        super().__init__(responses)