import random
import datetime as dt

class ScheduleHandler:
    def __init__(self, name, init_interval=1):
        self.name = name
        self.init_interval = init_interval 

    def update(self, block_content, btn_loc="before kvs"):
        block_content.set_kv("schedule", self.__class__.__name__)
        block_content.set_default_kv("interval", self.init_interval)
        due = dt.datetime.now() + dt.timedelta(days=self.init_interval)
        block_content.set_default_kv("due", due)

        return block_content

    def schedule(self, block_content):
        raise NotImplementedError


class ExpDefault(ScheduleHandler):
    def __init__(self, init_interval=1, init_factor=2):
        super().__init__("ExpSpacer", init_interval)
        self.init_factor = init_factor

    def update(self, block_content):
        super().update(block_content)
        block_content.set_default_kv("factor", self.init_factor)

    def schedule(self, block_content, response):
        interval = block_content.get_kv("interval")
        factor = block_content.get_kv("factor")
        due = block_content.get_kv("due")

        interval.value = self.get_next_interval(interval.value, factor.value)
        due.value = dt.datetime.now() + dt.timedelta(days=interval.value)

        return block_content

    def get_next_interval(self, interval, factor):
        if interval == 0:
            return 1 
        next_interval = interval * factor
        noise = next_interval * (0.125 * (2*random.random() - 1))
        next_interval = round(next_interval + noise)
        return next_interval


class ExpReset(ScheduleHandler):
    def __init__(self, init_interval=1, init_factor=2):
        super().__init__("ExpSpacer", init_interval)
        self.init_factor = init_factor

    def update(self, block_content):
        super().update(block_content)
        block_content.set_default_kv("factor", self.init_factor)

    def schedule(self, block_content, response):
        interval = block_content.get_kv("interval")
        factor = block_content.get_kv("factor")
        due = block_content.get_kv("due")

        if response in ["↑","thought-provoking"]:
            interval.value = self.init_interval
        else:
            interval.value = self.get_next_interval(interval.value, factor.value)
        due.value = dt.datetime.now() + dt.timedelta(days=interval.value)

        return block_content

    def get_next_interval(self, interval, factor):
        if interval == 0:
            return 1 
        next_interval = interval * factor
        noise = next_interval * (0.125 * (2*random.random() - 1))
        next_interval = round(next_interval + noise)
        return next_interval


class Periodically(ScheduleHandler):
    def __init__(self, days=7):
        super().__init__("Periodically", init_interval=days)

    def schedule(self, block_content):
        due = block_content.get_kv("due")
        interval = block_content.get_kv("interval")
        due.value = due.value + dt.timedelta(days=interval.value)
