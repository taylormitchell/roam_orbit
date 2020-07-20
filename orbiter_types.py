import datetime as dt
import re
import schedulers
from date_helpers import strftime_day_suffix

class ToReview:
    name = "to-review"
    responses = ("cool","meg","boring")

    def __init__(self, text, due=None, interval=0, factor=4, first_interval=2, scheduler=None):
        self.block_kv = block_kv
        self.block_kv.set_default("type", self.name)
        self.block_kv.set_default("interval", interval)
        self.block_kv.set_default("factor", factor)
        self.block_kv.set_default("due", f"[[{strftime_day_suffix(dt.datetime.now())}]]")
        for i,r in enumerate(self.responses):
            self.block_kv.set_default(f"count{i}", 0)
        self.first_interval = first_interval 
        self.scheduler = scheduler or schedulers.sm2

    def get(attrname):
        if hasattr(self, attrname):
            return getattr(self, attrname)
        elif self.block_kv.get_kv(attrname):
            return self.block_kv.get_kv(attrname)
        else:
            raise AttributeError

    def set(attrname, value):
        if hasattr(self, attrname):
            setattr(self, attrname, value)
        elif self.block_kv.get_kv(attrname):
            self.block_kv.set_kv(attrname, value)
        else:
            raise AttributeError

    def update(self, response_num):

        count_key = f"count{response_num}"
        self.set(count_key, self.get(count_key)+1)

        self.set("interval", self.scheduler(self.get("interval"), self.get("factor"), self.get("first_interval")))

        due = strftime_day_suffix(dt.datetime.now() + dt.timedelta(days=self.get("interval")))
        self.block_kv.set_default("due", f"[[{due}]]")

class ToThink:
    name = "to-think"
    responses = ("thought-provoking","not")

    def __init__(self, text, due=None, interval=0, factor=4, first_interval=2, 
            scheduler=None, factor_multiplier_incr=1.2, factor_multiplier_decr=0.8):
        self.block_kv = block_kv
        self.block_kv.set_default("type", self.name)
        self.block_kv.set_default("interval", interval)
        self.block_kv.set_default("factor", factor)
        self.block_kv.set_default("due", f"[[{strftime_day_suffix(dt.datetime.now())}]]")
        for i,r in enumerate(self.responses):
            self.block_kv.set_default(f"count{i}", 0)
        self.first_interval = first_interval 
        self.scheduler = scheduler or schedulers.sm2
        self.factor_multiplier_incr = factor_multiplier_incr
        self.factor_multiplier_decr = factor_multiplier_decr

    def get(attrname):
        if hasattr(self, attrname):
            return getattr(self, attrname)
        elif self.block_kv.get_kv(attrname):
            return self.block_kv.get_kv(attrname)
        else:
            raise AttributeError

    def set(attrname, value):
        if hasattr(self, attrname):
            setattr(self, attrname, value)
        elif self.block_kv.get_kv(attrname):
            self.block_kv.set_kv(attrname, value)
        else:
            raise AttributeError

    def update(self, response_num):
        if response_num==0:
            self.set("factor", self.get("factor")*self.get("factor_multiplier_decr"))
        elif response_num==1:
            self.set("factor", self.get("factor")*self.get("factor_multiplier_incr"))
        else:
            raise ValueError("Invalid response")

        count_key = f"count{response_num}"
        self.set(count_key, self.get(count_key)+1)

        self.set("interval", self.scheduler(self.get("interval"), self.get("factor"), self.get("first_interval")))

        due = strftime_day_suffix(dt.datetime.now() + dt.timedelta(days=self.get("interval")))
        self.block_kv.set_default("due", f"[[{due}]]")

if __name__=="__main__":
    orbiter = ToThink("why is the sky blue?")
    print(orbiter)
    orbiter.update(0)
    print(orbiter)