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

scheduler_handlers = {o.__name__: o for o in [ExpDefault, ExpReset, Periodically]}
feed_handlers = {o.__name__: o for o in [ToReview, ToThink]}
feedback_handlers = {o.__name__: o for o in [Vote, ThoughtProvoking]}

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


class RoamOrbiterManager:
    def __init__(self, block_content, feed_handler, schedule_hander=None, feedback_handler=None):
        self.block_content = block_content
        self.set_feed_handler(feed_handler)
        self.set_schedule_handler(schedule_hander or feed_handler.get_schedule_handler())
        self.set_feedback_handler(feedback_handler or feed_handler.get_feedback_handler())
    
    def process_response(self, response_num):
        self.feedback_handler.add_response(self.block_content, response_num)
        response = self.feedback_handler.response_num_to_name(response_num)
        self.schedule_handler.schedule(self.block_content, response)

    def set_feedback_handler(self, feedback_handler):
        self.feedback_handler = feedback_handler
        self.feedback_handler.update(self.block_content)

    def set_schedule_handler(self, schedule_handler):
        self.schedule_handler = schedule_handler
        self.schedule_handler.update(self.block_content)

    def set_feed_handler(self, feed):
        self.feed = feed
        self.feed.update(self.block_content)

    @classmethod
    def from_string(cls, string, feed=None, sched=None, feedback=None):
        block_content = BlockContentKV.from_string(string)

        # Convert old formats to the latest one

        block_content = convert_review_history(block_content)
        block_content = convert_old_roam_orbit(block_content)

        # If a handler was specified, use that.
        # If not, check if one is specified in the string and use that if it is.
        # Otherwise, set to a default. 

        if not feed:
            if block_content.get_kv("feed"):
                feed = block_content.get_kv("feed").value
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

    def to_string(self):
        return self.block_content.to_string()


def main(text, action, arg):

    if action=="init":
        if arg=="ToReview":
            orbiter_manager = RoamOrbiterManager.from_string(text, feed="ToReview")
        elif arg=="ToThink":
            orbiter_manager = RoamOrbiterManager.from_string(text, feed="ToThink")
        else:
            orbiter_manager = RoamOrbiterManager.from_string(text)
    elif action=="change_schedule":
        orbiter_manager = RoamOrbiterManager.from_string(text)
        orbiter_manager.set_scheduler(schedulers[arg])
    elif action=="change_feed":
        orbiter_manager = RoamOrbiterManager.from_string(text)
        orbiter_manager.set_feed(feeds[arg])
    elif action=="change_feedback_type":
        orbiter_manager = RoamOrbiterManager.from_string(text)
        orbiter_manager.set_feedback_type(feeds[arg])
    elif action=="add_response":
        orbiter_manager = RoamOrbiterManager.from_string(text)
        orbiter_manager.process_response(int(arg))
    else:
        raise ValueError(f"'{action}' isn't a supported action")

    return orbiter_manager.to_string()

if __name__=="__main__":
    text = sys.argv[1]
    action = sys.argv[2]
    arg = sys.argv[3] 
    print(main(text, action, arg))
