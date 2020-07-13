import datetime as dt
import re
import schedulers

DAYS_TO_SECONDS = 24*60*60

@dataclass
class ToReview:
    responses = ("cool","meg","boring")
    scheduler = schedulers.sm2

    def __init__(self, text, due=None, interval=0, factor=4, response_counts=None, first_interval=2):
        self.text = text
        self.due = due or dt.datetime.now().timestamp()
        self.interval = interval
        self.factor = factor
        self.first_interval = first_interval
        self.response_counts = response_counts or {r:0 for r in self.responses}

    def update(self, response):
        try:
            idx = self.responses.index(response)
        except:
            raise ValueError("Invalid response")
        self.response_counts[response] += 1
        self.interval = self.__class__.scheduler(self.interval, self.factor, self.first_interval)
        self.due = self.due + self.interval*DAYS_TO_SECONDS

    def __repr__(self):
        d = self.__dict__.copy()
        d["due"] = dt.datetime.fromtimestamp(d["due"])
        return f"<ToReview {d}'>"


class ToThink:
    responses = ("thought-provoking","not")

    def __init__(self, text, due=None, interval=0, factor=4, response_counts=None, first_interval=2, 
            scheduler=None, factor_multiplier_incr=1.2, factor_multiplier_decr=0.8):
        self.text = text
        self.due = due or dt.datetime.now().timestamp()
        self.interval = interval
        self.factor = factor
        self.first_interval = first_interval
        self.response_counts = response_counts or {r:0 for r in self.responses}
        self.scheduler = scheduler or schedulers.sm2
        self.factor_multiplier_incr = factor_multiplier_incr
        self.factor_multiplier_decr = factor_multiplier_decr

    def update(self, response_num):
        try:
            response = self.responses[response_num]
        except:
            raise ValueError("Invalid response")
        if response_num==0:
            self.factor *= self.factor_multiplier_decr
        else:
            self.factor *= self.factor_multiplier_incr
        self.response_counts[response] += 1
        self.interval = self.scheduler(self.interval, self.factor, self.first_interval)
        self.due = self.due + self.interval*DAYS_TO_SECONDS

    def __repr__(self):
        d = self.__dict__.copy()
        d["due"] = dt.datetime.fromtimestamp(d["due"])
        return f"<ToReview {d}'>"



if __name__=="__main__":
    orbiter = ToThink("why is the sky blue?")
    print(orbiter)
    orbiter.update(0)
    print(orbiter)