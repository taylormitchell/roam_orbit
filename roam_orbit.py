
from ankify_roam.roam.containers import PageRef, PageTag, String, BlockContent, Button
import re
import json
import datetime as dt
import schedulers
from date_helpers import strftime_day_suffix, strptime_day_suffix

TO_THINK_FACTOR = 2
TO_THINK_FIRST_INTERVAL = 2
TO_THINK_INIT_INTERVAL = 1
TO_THINK_FAC_MULT_DECR = 0.9
TO_THINK_FAC_MULT_INCR = 1.1
TO_REVIEW_FACTOR = 3
TO_REVIEW_INIT_INTERVAL = 1
TO_REVIEW_FIRST_INTERVAL = 2

class BlockContentKV:
    def __init__(self, block_items):
        self.block_items = block_items

    @classmethod
    def from_string(cls, text):
        block_items = BlockContent.from_string(text)
        # Replace tags with key-value objects
        for i, item in enumerate(block_items):
            try:
                block_items[i] = KeyValue.from_item(item)
            except:
                continue
        return cls(block_items)

    def set_default_kv(self, key, default_value):
        value = self.get_kv(key)
        if value:
            return value
        else:
            self.add_kv(key, default_value)
            return default_value
        
    def set_default(self, default_item):
        if not self.get(default_item):
            self.add(default_item)
        return default_item

    def get(self, item):
        for b in self.block_items:
            if b==item:
                return b

    def remove(self, item):
        self.block_items.remove(item)

    def index(self, item):
        for i, b in enumerate(self.block_items):
            if b==item:
                return i

    def insert(self, index, item):
        self.block_items.insert(index, item)

    def add(self, item, add_whitespace=True, allow_duplicate=False):
        if not self.get(item) or allow_duplicate:
            if add_whitespace and not self.end_in_whitespace():
                self.block_items.append(String(" "))
            self.block_items.append(item)

    def set_kv(self, key, value):
        kv = self.get_kv(key)
        if kv:
            kv.value = value
        else:
            self.add_kv(key, value)

    def get_kv(self, key):
        for item in self.block_items:
            if type(item)==KeyValue and item.key==key:
                return item

    def add_kv(self, key, value):
        if not self.end_in_whitespace():
            self.block_items.append(String(" "))
        self.block_items.append(KeyValue(key, value))

    def end_in_whitespace(self):
        last_item = self.block_items[-1]
        return type(last_item)==String and last_item.to_string()[-1]==" "

    def to_string(self):
        return "".join([b.to_string() for b in self.block_items])

class KeyValue:
    def __init__(self, key, value, sep=":"):
        self.key = key
        self.value = value
        self.sep = sep

    @classmethod
    def from_item(cls, item, sep=":"):
        RE_INT = "^[1-9]\d*$|^0$"
        RE_FLOAT = "^([1-9]\d*|0).\d+$"
        if not (type(item) in (PageRef, PageTag)):
            raise ValueError("item must be PageRef or PageTag")
        if type(item._title[0])!=PageRef:
            raise ValueError("PageRef title must start with a PageRef") 

        key = item._title[0].title
        # String value
        if len(item._title[1:])==1 and type(item._title[1])==String:
            match = re.search(f"^({sep}\s*)(.+)$", item._title[1].string)
            if match:
                sep = match.group(1)
                value = match.group(2)
                if re.match(RE_INT, value):
                    value = int(value)
                elif re.match(RE_FLOAT, value):
                    value = float(value)
                else:
                    value = value
            else:
                raise ValueError("Syntax problem with the value")
        # PageRef value
        elif (len(item._title[1:])==2) and (type(item._title[1])==String) and (type(item._title[2])==PageRef):
            match = re.search(f"^{sep}\s*$", item._title[1].string)
            if match:
                sep = match.group()
                value = item._title[2]
                # If the page ref is a date, set `value` to a datetime value.
                try: 
                    value = strptime_day_suffix(value.title, format="%B %d, %Y")
                except:
                    pass
            else:
                raise ValueError("Syntax problem with the value")
        else:
            raise ValueError("Value must be a single string or pageref")
        
        return cls(key, value, sep)

    def to_string(self):
        if type(self.value)==PageRef:
            value = self.value.to_string()
        elif type(self.value)==dt.datetime:
            value = strftime_day_suffix(self.value, format="[[%B %d, %Y]]")
        elif type(self.value)==int:
            value = str(self.value)
        elif type(self.value)==float:
            value = "%.1f" % self.value
        elif type(self.value)==str:
            value = self.value
        else:
            raise ValueError
        key = PageRef(self.key).to_string()
        sep = self.sep
        return f"#[[{key}{sep}{value}]]"

    def __repr__(self):
        return f"<KeyValue(key={self.key}, value={self.value})>"

class RoamOrbiter:
    def __init__(self, block_content, feed, scheduler):
        self.block_content = block_content
        self.feed = feed
        self.scheduler = scheduler or self.feed.get_scheduler()
        self.feed.init(self.block_content)
        self.scheduler.init(self.block_content)
    
    def swap_feed(self, new_feed):
    	feed_kv = self.feed.feed_kv
    	feed_kv.value = self.new_feed.name
    	new_feed.feed_kv = feed_kv
    	self.feed = new_feed

    def swap_scheduler(self, new_scheduler):
    	name_kv = self.scheduler.name_kv
    	name_kv.value = new_scheduler.name
    	new_scheduler.name_kv = name_kv
    	new_scheduler.factor_kv = self.scheduler.factor_kv
    	new_scheduler.interval_kv = self.scheduler.interval_kv
    	new_scheduler.due_kv = self.scheduler.due_kv
    
    	idx = self.scheduler.remove_buttons()
    	new_scheduler.insert_buttons(idx, self.block_content)

    	new_scheduler.add_counters(self.block_content)
    	self.scheduler = new_scheduler

class Scheduler:
    def __init__(self, name, interval, factor, responses=[]):
        self.name = name
        self.interval = interval 
        self.factor = factor
        self.responses = responses
        self.counter_keys = [f"{self.name}_{r}" for r in self.responses]
        self.response_buttons = [Button(r) for r in self.responses]

    def init(self, block_content):
        """
        TODO: this method assumes that none of the metadata that it's
        adding already exists in the block content
        """
        for button in self.response_buttons:
            block_content.add(button)

        block_content.set_kv("interval", self.interval)
        self.interval_kv = block_content.get_kv("interval")

        block_content.set_kv("factor", self.factor)
        self.factor_kv = block_content.get_kv("factor")

        due = dt.datetime.now() + dt.timedelta(days=self.interval)
        block_content.set_kv("due", due)
        self.due_kv = block_content.get_kv("due")

        for key in self.counter_keys:
            block_content.set_kv(key, 0)
            self.counter_kvs = block_content.get_kv(key)

    def update(self, block_content, response_num):
        counter_key = self.counter_keys[response_num]
        block_content.set(counter_key, self.get(counter_key)+1)

        block_content.set("interval", self.scheduler(
            int(self.get("interval")), 
            int(self.get("factor")), 
            int(self.get("first_interval"))))

        block_content.set("due", dt.datetime.now() + dt.timedelta(days=self.get("interval")))

    def remove_buttons(self, block_content):
        idx = block_content.index(self.response_buttons[0])
        for button in self.response_buttons:
            block_content.remove(button)
        return idx

    def insert_buttons(self, idx, block_content):
        for i, button in enumerate(self.response_buttons):
            block_content.insert(idx+(2*i), button)
            if i != len(self.response_buttons)-1:
                block_content.insert(idx+(2*i+1), String(" "))

class Feed:
    def __init__(self, name, scheduler):
        self.name = name
        self.scheduler = scheduler
        self.feed_key = "feed"

    def init(self, block_content):
        self.block_kv.set_default_kv(self.feed_key, self.name)
        self.feed_kv = self.block_kv.get_kv(self.feed_key)
    
class ToReview:
    name = "to-review"
    responses = ("cool","meh","boring")

    def __init__(self, block_kv, due=None, interval=TO_REVIEW_INIT_INTERVAL, factor=TO_REVIEW_FACTOR, 
                 first_interval=TO_REVIEW_FIRST_INTERVAL, scheduler=None):
        self.block_kv = block_kv
        for r in self.responses:
            self.block_kv.set_default(Button(r))
        self.block_kv.set_default_kv("type", self.name)
        self.block_kv.set_default_kv("interval", interval)
        self.block_kv.set_default_kv("factor", factor)
        due = dt.datetime.now() + dt.timedelta(days=TO_REVIEW_INIT_INTERVAL)
        self.block_kv.set_default_kv("due", due)
        for i,r in enumerate(self.responses):
            self.block_kv.set_default_kv(f"count{i}", 0)
        self.first_interval = first_interval 
        self.scheduler = scheduler or schedulers.sm2

    def get(self, attrname):
        if hasattr(self, attrname):
            return getattr(self, attrname)
        elif self.block_kv.get_kv(attrname):
            return self.block_kv.get_kv(attrname).value
        else:
            return None

    def set(self, attrname, value):
        if hasattr(self, attrname):
            setattr(self, attrname, value)
        elif self.block_kv.get_kv(attrname):
            self.block_kv.set_kv(attrname, value)
        else:
            raise AttributeError

    def update(self, response_num):

        count_key = f"count{response_num}"
        self.set(count_key, self.get(count_key)+1)

        self.set("interval", self.scheduler(
            int(self.get("interval")), 
            int(self.get("factor")), 
            int(self.get("first_interval"))))

        self.set("due", dt.datetime.now() + dt.timedelta(days=self.get("interval")))

    def to_string(self):
        return self.block_kv.to_string()

class ToThink:
    name = "to-think"
    responses = ("thought-provoking","not")

    def __init__(self, block_kv, due=None, 
            interval=TO_THINK_INIT_INTERVAL, 
            factor=TO_THINK_FACTOR, 
            first_interval=TO_THINK_FIRST_INTERVAL, 
            factor_multiplier_incr=TO_THINK_FAC_MULT_INCR,
            factor_multiplier_decr=TO_THINK_FAC_MULT_DECR,
            scheduler=None):
        self.block_kv = block_kv
        for r in self.responses:
            self.block_kv.set_default(Button(r))
        self.block_kv.set_default_kv("type", self.name)
        self.block_kv.set_default_kv("interval", interval)
        self.block_kv.set_default_kv("factor", factor)
        due = dt.datetime.now() + dt.timedelta(days=TO_REVIEW_INIT_INTERVAL)
        self.block_kv.set_default_kv("due", due)
        for i,r in enumerate(self.responses):
            self.block_kv.set_default_kv(f"count{i}", 0)
        self.first_interval = first_interval 
        self.scheduler = scheduler or schedulers.sm2
        self.factor_multiplier_incr = factor_multiplier_incr
        self.factor_multiplier_decr = factor_multiplier_decr

    def get(self, attrname):
        if hasattr(self, attrname):
            return getattr(self, attrname)
        elif self.block_kv.get_kv(attrname):
            return self.block_kv.get_kv(attrname).value
        else:
            return None

    def set(self, attrname, value):
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

        self.set("interval", self.scheduler(
            int(self.get("interval")), 
            int(self.get("factor")), 
            int(self.get("first_interval"))))

        self.set("due", dt.datetime.now() + dt.timedelta(days=self.get("interval")))

    def to_string(self):
        return self.block_kv.to_string()

ORBITERS = {o.name: o for o in [ToThink, ToReview]}

def init(text, type):
    block_kv = BlockContentKV.from_string(text)
    Orbiter = ORBITERS.get(type, ToReview)
    return Orbiter(block_kv).to_string()

def update(text, response):
    block_kv = BlockContentKV.from_string(text)
    block_kv = handle_review_history(block_kv)

    orbiter_type = block_kv.set_default_kv("type", "to-review")
    Orbiter = ORBITERS.get(orbiter_type)
    orbiter = Orbiter(block_kv)

    orbiter.update(response)

    return orbiter.to_string()

def handle_review_history(block_kv):
    items_remove = []
    for i, item in enumerate(block_kv.block_items):
        if type(item) in (PageRef, PageTag) and item.title=="SomedayMaybe":
            items_remove.append(item)
        if type(item)==Button and item.name=="Review History":
            review_history = json.loads(item.text)
            block_kv.add_kv("interval", review_history["Interval"])
            date = dt.datetime.strptime(review_history["Next Review"], "[[due: %Y-%m-%d]]")
            date = strftime_day_suffix(date)
            block_kv.add_kv("due", f"[[{date}]]")
            items_remove.append(item)
    for item in items_remove:
        block_kv.block_items.remove(item)
    return block_kv





