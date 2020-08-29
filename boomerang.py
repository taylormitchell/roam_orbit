import sys
import re
import datetime as dt
import json
from itertools import zip_longest

SEP = ": "
INIT_INTERVAL = 2

class RoamComponentList(list):
    def __init__(self, components=[]):
        for c in components:
            self.append(c)

    def find(self, condition):
        for c in self:
            if condition(c):
                return c

    def findall(self, condition):
        res = type(self)()
        for c in self:
            if condition(c):
                res.append(c)
        return res

    def get_kv(self, key):
        for o in self:
            if type(o)==KeyValue and o.key==key:
                return o.value

    def set_kv(self, key, value):
        for o in self:
            if type(o)==KeyValue and o.key==key:
                o.value = value
                return
        self.append(KeyValue(key, value))

    def add_tag(self, title):
        for o in self:
            if type(o)==Tag and o.title==title:
                return
        self.append(Tag(title))

    @classmethod
    def from_text(cls, text):
        parse_order = [Button, KeyValue, Tag, Page]
        comp_list = cls([Text(text)])
        for comp_type in parse_order:
            comp_list = comp_type.find_and_replace(comp_list)
        return comp_list

    def to_string(self):
        return "".join([c.to_string() for c in self])


class RoamComponent:
    @classmethod
    def find_and_replace(cls, comp_list):
        new_comp_list = type(comp_list)()
        for comp in comp_list:
            if type(comp)==Text:
                string = comp.to_string()
                cls_comps = [cls.from_string(s) for s in cls.findall(string)]
                text_comps = [Text(s) for s in cls.split(string)]
                comps = [c for tup in zip_longest(text_comps, cls_comps) 
                           for c in tup if c]
                new_comp_list += comps
            else:
                new_comp_list.append(comp)
            
        return new_comp_list

    def __eq__(self, o):
        if type(self)==type(o) and self.to_string()==o.to_string():
            return True
        return False

    def __repr__(self):
        return "<%s('%s')>" % (
            self.__class__.__name__, self.to_string())


class Text(RoamComponent):
    def __init__(self, text):
        self.text = text

    def to_string(self):
        return self.text


class Button(RoamComponent):
    def __init__(self, title, hidden=None):
        self.title = title
        self.hidden = hidden

    @classmethod
    def findall(cls, string):
        return re.findall("{{.(?:(?<!{{).)*}}", string)

    @classmethod
    def split(cls, string):
        return re.split("{{.(?:(?<!{{).)*}}", string)

    @classmethod
    def from_string(cls, string):
        if ":" in string:
            m = re.search(r"{{([^:]*):(.*)}}", string)
            title, hidden = m.groups()
            return cls(title, hidden)
        else:
            return cls(string[2:-2])

    def to_string(self):
        if self.hidden:
            return "{{%s:%s}}" % (self.title, self.hidden)
        return "{{%s}}" % self.title


class Tag(RoamComponent):
    def __init__(self, title_comps):
        if type(title_comps)==str:
            title_comps = RoamComponentList.from_text(title_comps)
        self.title_comps = title_comps

    @property
    def title(self):
        return re.sub("\[\[([\W\w]*)\]\]", "\g<1>", self.to_string()[1:])

    @classmethod
    def findall(cls, string):
        tags = re.findall("#[\w\-_@:]+", string)
        tags += ["#"+c for c in Page.findall(string)]
        if not tags:
            return []
        return re.findall("|".join([re.escape(t) for t in tags]), string)

    @classmethod
    def split(cls, string):
        tags = cls.findall(string)
        if not tags:
            return [string]
        return re.split("|".join([re.escape(t) for t in tags]), string)

    @classmethod
    def from_string(cls, string):
        comps = RoamComponentList.from_text(string[1:])
        return cls(comps)

    def to_string(self):
        return "#"+self.title_comps.to_string()


class Page(RoamComponent):
    def __init__(self, title_comps):
        if type(title_comps)==str:
            title_comps = RoamComponentList([Text(title_comps)])
        self.title_comps = title_comps

    @property
    def title(self):
        return self.to_string()[2:-2]

    @classmethod
    def findall(cls, string):
        # https://stackoverflow.com/questions/524548/regular-expression-to-detect-semi-colon-terminated-c-for-while-loops/524624#524624
        bracket_count = 0
        pages = []
        page = ""
        prev_char = ""
        for j,c in enumerate(string):
            # Track page opening and closing
            if prev_char+c == "[[":
                if not page:
                    page = string[j-1]
                bracket_count += 1
                prev_char = ""
            elif prev_char+c == "]]":
                bracket_count -= 1
                prev_char = ""
            else:
                prev_char = c
            if page:
                page += c
            # End of page
            if bracket_count == 0 and page:
                pages.append(page)
                page = ""

        return pages

    @classmethod
    def split(cls, string):
        pages = cls.findall(string)
        if not pages:
            return [string]
        return re.split("|".join([re.escape(p) for p in pages]), string)

    @classmethod
    def from_string(cls, string):
        return cls(string)

    def to_string(self):
        return self.title_comps.to_string()


class KeyValue(RoamComponent):
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.sep = SEP 

    @classmethod
    def findall(cls, string):
        tags = Tag.findall(string)
        return [t for t in tags if re.match(f"^#(\[\[)?[^:]+{SEP}", t)]

    @classmethod
    def split(cls, string):
        kvs = cls.findall(string)
        if not kvs:
            return [string]
        return re.split("|".join([re.escape(kv) for kv in kvs]), string)

    @classmethod
    def from_string(cls, string):
        tag = Tag.from_string(string)
        m = re.match(f"^([^:]+){SEP}(.*)$", tag.title)
        key, value = m.groups()
        return cls(key, cls.parse_value(value))

    @classmethod
    def parse_value(cls, obj):
        "Convert object to int, float, or date"
        RE_INT = "^[1-9]\d*$|^0$"
        RE_FLOAT = "^([1-9]\d*|0).\d+$"
        RE_DATE = "\d\d\d\d-\d\d-\d\d"
        if re.match(RE_INT, obj):
            return int(obj)
        elif re.match(RE_FLOAT, obj):
            return float(obj)
        elif re.match(RE_DATE, obj):
            return dt.datetime.strptime(obj, "%Y-%m-%d")
        else:
            return obj
    
    def to_string(self):
        if type(self.value)==dt.datetime:
            value = dt.datetime.strftime(self.value, format="%Y-%m-%d")
        elif type(self.value)==int:
            value = str(self.value)
        elif type(self.value)==float:
            value = "%.1f" % self.value
        elif type(self.value)==str:
            value = self.value

        return f"#[[{self.key}{self.sep}{value}]]"


class Boomerang:
    def __init__(self, text, interval=INIT_INTERVAL, due_date=None, counter_values=(0,0,0)):
        self.responses = ["1x", "2x", "3x"]
        self.counter_keys = [r+"_count" for r in self.responses]
        self.interval_key = "interval"
        self.due_key = "due"
        self.total_count_key = "total_count"
        self.name_tag = "Boomerang"

        # Split text into components
        self.components = RoamComponentList.from_text(text)

        # Set boomerang tracking data

        for i, _ in enumerate(self.responses):
            self.set_response_button(i, interval)

        self.components.add_tag(self.name_tag)

        if not self.components.get_kv(self.interval_key):
            self.components.set_kv(self.interval_key, interval)

        if not self.components.get_kv(self.due_key):
            due_date = due_date or dt.datetime.now() + dt.timedelta(interval)
            self.components.set_kv(self.due_key, due_date)

        for key, value in zip(self.counter_keys, counter_values):
            if not self.components.get_kv(key):
                self.components.set_kv(key, value)

        if not self.components.get_kv(self.total_count_key):
            self.components.set_kv(self.total_count_key, sum(counter_values))

    def set_response_button(self, response_num, interval):
        interval = interval*(response_num+1)
        if interval <= 30:
            interval_repr = f"{interval}d"
        elif interval <= 365:
            interval_repr = "%.1fm" % (interval/30.0)
        else:
            interval_repr = "%.1fy" % (interval/365.0)
        response = self.responses[response_num]
        title = title = f"{response} ({interval_repr})"

        pat = f"{response} \(\d+.?\d?[dmy]\)"
        for o in self.components:
            if type(o)==Button and re.match(pat, o.title):
                o.title = title
                return
        self.components.append(Button(title))

    def update(self, response_num):
        # update counter
        counter_key = self.counter_keys[response_num]
        self.components.set_kv(counter_key, self.components.get_kv(counter_key)+1)
        self.components.set_kv(self.total_count_key, self.components.get_kv(self.total_count_key)+1)

        # update due date and interval
        interval = self.components.get_kv(self.interval_key)*(response_num+1)
        self.components.set_kv(self.due_key, dt.datetime.now() + dt.timedelta(interval))
        self.components.set_kv(self.interval_key, interval)

        # update buttons
        for i,_ in enumerate(self.responses):
            self.set_response_button(i, interval)

    def to_string(self):
        return self.components.to_string()


def roam_orbit_to_boomerang(text):

    comps = RoamComponentList.from_text(text)

    metadata = {}

    # Get review history 
    review_history_btn = comps.find(lambda c: type(c)==Button and c.title=="Review History")
    has_review_history = review_history_btn is not None
    if has_review_history:
        review_history = json.loads(review_history_btn.hidden)

    # Get interval
    if comps.get_kv("interval"):
        metadata["interval"] = int(comps.get_kv("interval"))
    elif has_review_history and review_history.get("Interval"):
        metadata["interval"] = int(review_history.get("Interval"))
    else:
        pass

    # Get due date
    if comps.get_kv("due"):
        metadata["due_date"] = comps.get_kv("due")
    elif has_review_history and review_history.get("Next Review"):
        due_kv = review_history.get("Next Review")
        metadata["due_date"] = dt.datetime.strptime(due_kv, "[[due: %Y-%m-%d]]")
    else:
        pass
    
    # Get counters
    counts = []
    feedback = comps.get_kv("feedback")
    if feedback=="Vote":
        counts.append(comps.get_kv("↑_count"))
        counts.append(comps.get_kv("↓_count"))
        counts.append(0)
    elif feedback=="ThoughtProvoking":
        counts.append(comps.get_kv("thoughts_count"))
        counts.append(comps.get_kv("none_count"))
        counts.append(0)
    elif has_review_history:
        counts.append(0)
        counts.append(len(review_history.get("Past Reviews",[])))
        counts.append(0)
    else:
        counts = [0,0,0]
    metadata["counter_values"] = counts

    # Remove stuff
    comps_rem = []
    if review_history_btn:
        comps_rem.append(review_history_btn)
    pat = "feedback|schedule|interval|due|.*_count|factor.*"
    comps_rem += comps.findall(lambda c: type(c)==KeyValue and re.match(pat,c.key))
    comps_rem += comps.findall(lambda c: c.to_string()=="#[[Roam Orbiter]]")
    pat = "↑|↓|thoughts|none"
    comps_rem += comps.findall(lambda c: type(c)==Button and re.match(pat,c.title))
    for c in comps_rem:
        comps.remove(c)

    # Replace stuff
    for i, c in enumerate(comps):
        if type(c)==Tag and c.title=="SomedayMaybe":
            comps[i] = KeyValue("feed", "ToReview")

    # Pop tags
    tags = []
    for i in range(len(comps)-1, 0, -1):
        c = comps[i]
        if type(c) in [Tag, KeyValue]:
            tags.append(comps.pop(i))

    # Remove whitespace at the end
    for i in range(len(comps)-1, 0, -1):
        c = comps[i]
        if type(c)==Text and re.match("^\s*$", c.text):
            comps.pop(i)
        else:
            break
    if type(comps[-1])==Text:
        comps[-1].text = re.sub("\s+$"," ",comps[-1].text)

    # add tags back
    comps += tags

    return Boomerang(comps.to_string(), **metadata)


def main(text, action, response_num=None):
    boomerang = roam_orbit_to_boomerang(text)
    if action=="init":
        pass
    elif action=="update":
        boomerang.update(response_num)
    else:
        raise ValueError(f"'{action}' isn't a supported action")
    return boomerang.to_string()


if __name__=="__main__":

    text = sys.argv[1]
    action = sys.argv[2]
    response_num = int(sys.argv[3]) if len(sys.argv)>3 else None 
    print(main(text, action, response_num))
    sys.exit(0)

    try:
        #text = """Extract the interval, due date, and counters {{↑}} {{↓}}#[[Roam Orbiter]]#[[feed: ToReview]]#[[schedule: ExpVarFactor]]#[[interval: 2]]#[[due: 2020-08-31]]#[[factor_short: 2]]#[[factor_long: 3]]#[[feedback: Vote]]#[[↑_count: 0]]#[[↓_count: 0]]#[[total_count: 0]]"""
        #print(text)
        #boomerang = roam_orbit_to_boomerang(text)
        #print(boomerang.to_string())
        #print("")

        #text = """{{[[DONE]]}} In the [[Remind me later]] feature, change the responses to "upvote/downvote". And record the upvotes and downvotes in the review history.   #SomedayMaybe #[[Programmable Attention]]  {{Review History: {"Interval": 65, "Past Reviews": ["[[reviewed: 2020-04-16]]", "[[reviewed: 2020-04-17]]", "[[reviewed: 2020-04-22]]", "[[reviewed: 2020-05-02]]", "[[reviewed: 2020-05-18]]", "[[reviewed: 2020-06-20]]"], "Next Review": "[[due: 2020-08-24]]"}}}  #[[[[done-date]]: 2020-08-24]] #@09:35"""
        #print(text)
        #boomerang = roam_orbit_to_boomerang(text)
        #print(boomerang.to_string())
        #print("")

        text = """{{[[TODO]]}} [[To-Think]]: Why aren't there equivalents to [[Martial Arts]] gyms and belts for [[Knowledge]] based disciplines? What would that look like? {{thoughts}} {{none}}#[[Roam Orbiter]]#[[feed: ToThink]]#[[schedule: ExpReset]]#[[interval: 13]]#[[due: 2020-08-29]]#[[factor: 2]]#[[feedback: ThoughtProvoking]]#[[total_count: 1]]#[[thoughts_count: 1]]#[[none_count: 0]]"""
        print(text)
        boomerang = roam_orbit_to_boomerang(text)
        print(boomerang.to_string())
        print("")
        boomerang.update(0)
        print(boomerang.to_string())
        print("")
        boomerang.update(1)
        print(boomerang.to_string())
        print("")

    except:
        import sys; import pdb; import traceback
        extype, value, tb = sys.exc_info()
        traceback.print_exc()
        pdb.post_mortem(tb)

            
