import random 

def sm2(interval, factor, first_interval=1):
    if interval == 0:
        return first_interval 
    next_interval = interval * factor
    noise = int(next_interval * (0.125 * (random.randint(0,3) - 1)))
    next_interval = next_interval + noise
    return next_interval