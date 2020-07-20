import re
from datetime import datetime

FORMAT = '%B %d, %Y'

def remove_day_suffix(dt): 
    return re.sub(r"\b(\d{1,2})(st|nd|rd|th)\b", "\g<1>", dt)

def strptime_day_suffix(date_string, format=FORMAT):
    # Parse datetime from date string with day suffix 
    date_string = remove_day_suffix(date_string)
    return datetime.strptime(date_string, format)

def get_day_suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def strftime_day_suffix(dt, format=FORMAT):
    # Datetime to date string with day suffix 
    return dt.strftime(format.replace('%d', str(dt.day) + get_day_suffix(dt.day)))

def add_day_suffix(dt, format=FORMAT):
    # Date string to date string with day suffix added 
    dt = datetime.strptime(dt, format)
    return dt.strftime(format.replace('%d', str(dt.day) + get_day_suffix(dt.day)))
