from ankify_roam.roam.containers import BlockContent 

class Scheduler:
    def __init__(self):
        self.key_due = "due"
        self.key_interval = "interval"
        self.key_factor = "factor"
        self.key_type = "type"
        self.pat_counter = "count\d+"

    def update(self, roam_text, response):
        orbit_info = self.get_orbit_info(text)
        orbit_info.update(response)
        return self.update_roam_text(orbit_info)

    def get_orbit_info(self, text):
        block_content = BlockContent.from_string(text)
        for i, block_item in enumerate(block_content):
            if type(block_item)==PageTag and KeyValueTag.is_kv(block_item):
                # figure out the property it contains
                # save index
                # get value

        if type=="to-think":
            return ToThink()
        elif type=="to-review":
            return ToReview()

    def update_roam_text(self, orbiter):
        return text

class KeyValueTag:
    def __init__(self, key, value):
        self.key = key
        self.value = value 

    @classmethod
    def from_string(cls, string):
        pat = "#\[\[\[\[(\w+)\]\]:(\w+)\]\]"
        matches = re.findall(pat)
        key, value = matches.groups()
        return cls(key, value)

    def to_string(self):
        return f"#[[[[{self.key}]]:{self.value}]]"


def init(text):
    pass

def update(text, response):
    pass

if __name__=="__main__":
    response = 0
    text = "{{[[TODO]]}} so something {{cool!}} {{meh}} {{boring}} #[[[[type]]:to-review]] #[[[[scheduler]]:SM2]] #[[[[interval]]:4]] #[[[[factor]]:4]] #[[due: [[July 11th, 2020]]]] #[[[[count1]]:1]] #[[[[count2]]:2]] #[[[[count3]]:0]]"
    scheduler = Scheduler()
    text_rescheduled = scheduler.update(text, response)
    return text_rescheduled

