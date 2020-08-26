"""
The metaphorical user story

I'm a planet and anything I want to review later I etch onto a rock and then
send up to the OrbiterStation. I also tell the station the type of orbit I 
want the rock to be in (the schedule) and in what context I want to see the 
rock (the feed).

A Orbiter Manager assigns a schedule_manager and feed_manager to the rock according
to the types indicating by the planet. In then passes it to the feed_manager and schedule_manager
for processing.

The assigned scheduler worker and feed worker start to process the block.

In some cases, no scheduler was indicated. In this case, the feed_manager assigns 
a scheduler. Each feed has a default schedule. That's the only job of the feed.

The first job of the schedule manager is to collect any metadata already etched onto 
the rock. In cases where some metadata is missing, it adds an etching. Using this metadata plus
the planet response, it updates the etching and then sends it off on it's orbit. 

As the rock is hurtling through space, it knows nothing about the orbit. 

All rocks in orbit will, at some point, pass through the OrbiterStation which they
started at. Upon entry, the planet is notified that a new orbiter has come in and is asked to
give one of the set of responses etched on the block. The planet reviews the block 
and sends back one of the respones.   

The response and block are passed to an Orbiter Manager. The manager determines the type
of Scheduler and Feed responsible for processing this block based on some etchings on it.
The manager then wraps the block in a RoamOrbiter package, staples the planet response onto it, 
and passes it off for processing. 
"""
import sys
import re
import json
import datetime as dt
import logging
from date_helpers import strftime_day_suffix, strptime_day_suffix
from feed_handlers import *
from feedback_handlers import *
from schedule_handlers import *
from roam.content import *

logging.basicConfig(level=logging.INFO)

TO_THINK_FACTOR = 2
TO_THINK_FIRST_INTERVAL = 2
TO_THINK_INIT_INTERVAL = 1
TO_THINK_FAC_MULT_DECR = 0.9
TO_THINK_FAC_MULT_INCR = 1.1
TO_REVIEW_FACTOR = 3
TO_REVIEW_INIT_INTERVAL = 1
TO_REVIEW_FIRST_INTERVAL = 2
DEFAULT_FEED = "ToReview"
ROAM_ORBIT_TAG = "Roam Orbiter"

scheduler_handlers = {o.__name__: o for o in [ExpDefault, ExpReset, ExpVarFactor, Periodically]}
feed_handlers = {o.__name__: o for o in [ToReview, ToThink]}
feedback_handlers = {o.__name__: o for o in [Vote, ThoughtProvoking, OldThoughtProvoking]}

roam_orbit_keys = []
for handlers in [feed_handlers, scheduler_handlers, feedback_handlers]:
    for cls in handlers.values():
        for key in cls().keys:
            if key not in roam_orbit_keys:
                roam_orbit_keys.append(key)
roam_orbit_btns = []
for cls in feedback_handlers.values():
    for btn in cls().response_buttons:
        if btn not in roam_orbit_btns:
            roam_orbit_btns.append(btn)


def convert_review_history(block_content):
    items_remove = []
    for i, item in enumerate(block_content.block_items):
        if type(item) in (PageRef, PageTag) and item.title=="SomedayMaybe":
            items_remove.append(item)
        if type(item)==Button and item.name=="Review History":
            review_history = json.loads(item.text)
            block_content.set_kv("interval", int(review_history["Interval"]))
            date = dt.datetime.strptime(review_history["Next Review"], "[[due: %Y-%m-%d]]")
            block_content.set_kv("due", date)
            items_remove.append(item)

    for item in items_remove:
        block_content.block_items.remove(item)

    # Remove trailing whitespace
    while block_content.block_items[-1]==String(" "):
        del block_content.block_items[-1]

    return block_content


def convert_old_roam_orbit(block_content):
     if not block_content.get_kv("type"):
         return block_content
     block_content.remove(Button("cool"))
     block_content.remove(Button("meh"))
     block_content.remove(Button("boring"))
     block_content.delete_kv("type")
     block_content.delete_kv("interval")
     block_content.delete_kv("factor")
     block_content.delete_kv("due")
     block_content.delete_kv("count0")
     block_content.delete_kv("count1")
     block_content.delete_kv("count2")
     # Remove trailing whitespace
     while block_content.block_items[-1]==String(" "):
         del block_content.block_items[-1]


     return block_content


def convert_old_key_values(block_content):
    for i, item in enumerate(block_content.block_items):
        # Skip items which aren't KeyValues used by roam orbit
        if type(item)!=KeyValue:
            continue
        key = item.key.title if type(item.key)==PageRef else item.key 
        if key not in set(roam_orbit_keys):
            continue

        if type(item.key)==PageRef:
            item.key = item.key.title
        if type(item.sep)==PageRef:
            item.sep = item.sep.title
        if type(item.value)==PageRef:
            item.value = item.value.title
        if item.sep==":":
            item.sep = ": "

    return block_content


def convert_old_thought_provoking_names(block_content):
    old_feedback_handler = OldThoughtProvoking()
    new_feedback_handler = ThoughtProvoking()
    # Replace buttons
    for i, btn in enumerate(old_feedback_handler.response_buttons):
        idx = block_content.index(btn) 
        if idx is not None:
            block_content.block_items[idx] = new_feedback_handler.response_buttons[i]
    # Replace counters
    for i, key in enumerate(old_feedback_handler.counter_keys):
        kv = block_content.get_kv(key)
        if kv:
            kv.key = new_feedback_handler.counter_keys[i]
    # Replace feedback name
    kv = block_content.get_kv("feedback")
    if kv:
        kv.value = new_feedback_handler.__class__.__name__

    return block_content


def convert_toreview_scheduler(block_content):
    kv = block_content.get_kv("feed")
    if kv and kv.value=="ToReview":
        block_content.set_kv("schedule", "ExpVarFactor")
        kv = block_content.get_kv("factor")
        block_content.remove(kv)
    return block_content


def collapse_roam_orbit(block_content):
    # Collect roam orbit items
    kvs, btns = [], []
    for key in roam_orbit_keys:
        kv = block_content.get_kv(key)
        if kv:
            kvs.append(kv)
            block_content.remove(kv)
    for btn in roam_orbit_btns:
        btn = block_content.get(btn)
        if btn:
            btns.append(btn)
            block_content.remove(btn)
    roam_orbit_tag = block_content.get(PageTag.from_string(f"#[[{ROAM_ORBIT_TAG}]]"))
    if roam_orbit_tag:
        block_content.remove(roam_orbit_tag)

    # Remove extra whitespace
    items = block_content.block_items
    for i in list(range(len(items[:-1])))[::-1]:
        if items[i]==String(" ") and items[i+1]==String(" "):
            del items[i+1]
    # Remove trailing whitespace
    items = block_content.block_items
    while len(items)>0 and items[-1]==String(" "):
        del items[-1]
    if len(items)>0 and type(items[-1])==String:
        items[-1].string = re.sub("\s*$","", items[-1].string)

    for btn in btns:
        block_content.append(String(" "))
        block_content.append(btn)
    if roam_orbit_tag:
        block_content.append(roam_orbit_tag)
    for kv in kvs:
        block_content.append(kv)

    return block_content


class RoamOrbiterManager:
    def __init__(self, block_content, feed_handler, schedule_hander=None, feedback_handler=None):
        self.block_content = block_content
        self.set_feed_handler(feed_handler)
        self.set_schedule_handler(schedule_hander or feed_handler.get_schedule_handler())
        self.set_feedback_handler(feedback_handler or feed_handler.get_feedback_handler())
        self.block_content.set_default(PageTag.from_string(f"#[[{ROAM_ORBIT_TAG}]]"))
    
    def process_response(self, response_num):
        self.feedback_handler.add_response(self.block_content, response_num)
        self.schedule_handler.schedule(self.block_content, response_num)

    def set_feedback_handler(self, feedback_handler):
        if hasattr(self, "feedback_handler"):
            self.feedback_handler.remove_buttons(self.block_content)
        self.feedback_handler = feedback_handler
        self.feedback_handler.update_metadata(self.block_content)

    def set_schedule_handler(self, schedule_handler):
        self.schedule_handler = schedule_handler
        self.schedule_handler.update_metadata(self.block_content)

    def set_feed_handler(self, feed):
        self.feed = feed
        self.feed.update_metadata(self.block_content)

    @classmethod
    def from_string(cls, string, feed=None, sched=None, feedback=None):
        block_content = BlockContentKV.from_string(string)

        # Convert old formats to the latest one

        block_content = convert_review_history(block_content)
        block_content = convert_old_roam_orbit(block_content)
        block_content = convert_old_key_values(block_content)
        block_content = convert_old_thought_provoking_names(block_content)
        block_content = convert_toreview_scheduler(block_content)
        # If a handler was specified, use that.
        # If not, check if one is specified in the string and use that if it is.
        # Otherwise, set to a default. 

        if not feed:
            if block_content.get_kv("feed"):
                feed = block_content.get_kv("feed").value
            elif block_content.get(PageRef("To-Write")) or \
                    block_content.get(PageRef("To-Think")) or \
                    block_content.get(PageTag("To-Write")) or \
                    block_content.get(PageTag("To-Think")):
                feed = "ToThink"
            else:
                feed = DEFAULT_FEED
        feed_handler = feed_handlers[feed]()

        if sched:
            schedule_handler = schedule_handlers[sched]()
        else:
            schedule_handler = None

        if feedback:
            feedback_handler = feedback_handlers[feedback]()
        else:
            feedback_handler = None

        return cls(block_content, feed_handler, schedule_handler, feedback_handler)

    def to_string(self, collapse=True):
        if collapse:
            self.block_content = collapse_roam_orbit(self.block_content)
        return self.block_content.to_string()


def main(text, action, arg):

    if action=="init":
        if arg=="ToReview":
            orbiter_manager = RoamOrbiterManager.from_string(text, feed="ToReview")
        elif arg=="ToThink":
            orbiter_manager = RoamOrbiterManager.from_string(text, feed="ToThink")
        else:
            orbiter_manager = RoamOrbiterManager.from_string(text)
        return orbiter_manager.to_string()

    orbiter_manager = RoamOrbiterManager.from_string(text)
    if action=="update":
        pass
    elif action=="change_schedule":
        orbiter_manager.set_scheduler_handler(scheduler_handlers[arg]())
    elif action=="change_feed":
        feed_handler = feed_handlers[arg]()
        sch_handler = feed_handler.get_schedule_handler()
        fb_handler = feed_handler.get_feedback_handler()
        orbiter_manager.set_feed_handler(feed_handler)
        orbiter_manager.set_schedule_handler(sch_handler)
        orbiter_manager.set_feedback_handler(fb_handler)
    elif action=="change_feedback_type":
        orbiter_manager.set_feedback_type_handler(feedback_handlers[arg]())
    elif action=="add_response":
        orbiter_manager.process_response(int(arg))
    else:
        raise ValueError(f"'{action}' isn't a supported action")

    return orbiter_manager.to_string()

if __name__=="__main__":
    text = sys.argv[1]
    action = sys.argv[2]
    arg = sys.argv[3] if len(sys.argv)>3 else None 
    print(main(text, action, arg))
    
