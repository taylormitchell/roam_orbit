import unittest
import datetime as dt
from roam_orbit import *
from date_helpers import strftime_roam

class TestRoamOrbiterManager(unittest.TestCase):
    def setUp(self):
        self.maxDiff=None

    def test_init_review(self):
        text = "Some thing I want to review later"
        output = RoamOrbiterManager.from_string(text, feed="ToReview").to_string()
        expected_output = \
            "Some thing I want to review later {{↑}} {{↓}} #[[[[feed]]:ToReview]] "\
            "#[[[[schedule]]:ExpDefault]] #[[[[interval]]:2]] #[[[[due]]:[[%s]]]] #[[[[factor]]:3]] "\
            "#[[[[feedback]]:Vote]] #[[[[↑_count]]:0]] #[[[[↓_count]]:0]]" % strftime_roam(dt.datetime.now() + dt.timedelta(2))
        self.assertEqual(output, expected_output) 

    def test_init_think(self):
        text = "Some thing I want to think later"
        orbiter = RoamOrbiterManager.from_string(text, feed="ToThink")
        self.assertEqual(
            orbiter.to_string(),
            "Some thing I want to think later {{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] "\
            "#[[[[schedule]]:ExpReset]] #[[[[interval]]:2]] #[[[[due]]:[[%s]]]] #[[[[factor]]:3]] "\
            "#[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:0]] #[[[[not_count]]:0]]"\
            % strftime_roam(dt.datetime.now() + dt.timedelta(2))
        )

    def test_review_vote(self):
        text = \
            "Some thing I want to review later {{↑}} {{↓}} #[[[[feed]]:ToReview]] "\
            "#[[[[schedule]]:ExpDefault]] #[[[[interval]]:2]] #[[[[due]]:[[August 8th, 2020]]]] #[[[[factor]]:3]] "\
            "#[[[[feedback]]:Vote]] #[[[[↑_count]]:0]] #[[[[↓_count]]:0]]"
        orbiter = RoamOrbiterManager.from_string(text)
        orbiter.process_response(0)
        self.assertEqual(orbiter.to_string()[-37:], "#[[[[↑_count]]:1]] #[[[[↓_count]]:0]]")
        orbiter.process_response(1)
        self.assertEqual(orbiter.to_string()[-37:], "#[[[[↑_count]]:1]] #[[[[↓_count]]:1]]")
        
    def test_think_reset(self):
        text = \
            "Some thing I want to think later {{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] "\
            "#[[[[schedule]]:ExpReset]] #[[[[interval]]:10]] #[[[[due]]:[[August 8th, 2020]]]] #[[[[factor]]:3]] "\
            "#[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:0]] #[[[[not_count]]:0]]"
        orbiter = RoamOrbiterManager.from_string(text)
        orbiter.process_response(0)
        self.assertEqual(
            orbiter.to_string(),
            "Some thing I want to think later {{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] "\
            "#[[[[schedule]]:ExpReset]] #[[[[interval]]:2]] #[[[[due]]:[[%s]]]] #[[[[factor]]:3]] "\
            "#[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:1]] #[[[[not_count]]:0]]"\
            % strftime_roam(dt.datetime.now() + dt.timedelta(2))
        )

class TestConverters(unittest.TestCase):
    def test_review_history(self):
        text = """{{[[TODO]]}} Look into how hard is it to get a pilot's license. Could be fun. Is there a quick way to try it first to see if I like it? #SomedayMaybe {{Review History: {"Interval": 4, "Past Reviews": ["[[reviewed: 2020-06-21]]", "[[reviewed: 2020-06-26]]"], "Next Review": "[[due: 2020-06-30]]"}}}"""
        orbiter = RoamOrbiterManager.from_string(text)
        orbiter.process_response(0)


class TestKeyValue(unittest.TestCase):
    def test(self):
        item = PageTag.from_string("#[[key:value]]")
        kv = KeyValue.from_item(item)
        self.assertEqual(item.to_string(), kv.to_string())

        item = PageTag.from_string("#[[key:20]]")
        kv = KeyValue.from_item(item)
        self.assertEqual(item.to_string(), kv.to_string())
        self.assertEqual(type(kv.value), int)

        item = PageTag.from_string("#[[key: 2020-10-03]]")
        kv = KeyValue.from_item(item)
        self.assertEqual(item.to_string(), kv.to_string())
        self.assertEqual(type(kv.value), dt.datetime)

        item = PageTag.from_string("#[[[[key]]:value]]")
        kv = KeyValue.from_item(item)
        self.assertEqual(item.to_string(), kv.to_string())

        item = PageTag.from_string("#[[[[key]]:[[value]]]]")
        kv = KeyValue.from_item(item)
        self.assertEqual(item.to_string(), kv.to_string())

        item = PageTag.from_string("#[[[[key]][[:]][[value]]]]")
        kv = KeyValue.from_item(item)
        self.assertEqual(item.to_string(), kv.to_string())


if __name__=="__main__":
    #unittest.main()

    #string = "{{[[TODO]]}} Maybe remove the spaces between key-value items because when I hide them, you end up with a bunch of ugly white space in block references to them eg: #[[Roam Orbit]] {{↑}} {{↓}} #[[[[feed]]:ToReview]] #[[[[schedule]]:ExpDefault]] #[[[[interval]]:2]] #[[[[due]]:[[August 5th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:Vote]] #[[[[↑_count]]:0]] #[[[[↓_count]]:0]]"
    #block_content = BlockContentKV.from_string(string)
    #print(block_content.to_string())
    #convert_old_key_values(block_content)
    #print(block_content.to_string())

    #print("")

    #string = "What are all the different ways in which two atoms (molecules?) can be bonded to each other? {{↑}} {{↓}} #[[[[feed]]:ToReview]] #[[[[schedule]]:ExpDefault]] #[[[[interval]]:2]] #[[[[due]]:[[August 5th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:Vote]] #[[[[↑_count]]:0]] #[[[[↓_count]]:0]]"
    #block_content = BlockContentKV.from_string(string)
    #print(block_content.to_string())
    #convert_old_key_values(block_content)
    #print(block_content.to_string())

    #print("")

    #string = """Inversion of [[Top five regrets of the dying]]: "Don't ignore your dreams; don't work too much; say what you think; cultivate friendships; be happy." #Quote #[[[[source]][[:]][[http://www.paulgraham.com/todo.html]]]] {{↑}} {{↓}} #[[[[feed]]:ToReview]] #[[[[schedule]]:ExpDefault]] #[[[[interval]]:2]] #[[[[due]]:[[August 10th, 2020]]]] #[[[[factor]]:2]] #[[[[feedback]]:Vote]] #[[[[↑_count]]:0]] #[[[[↓_count]]:0]]"""
    #manager = RoamOrbiterManager.from_string(string)
    #print(manager.to_string())
    #manager.process_response(0)
    #print(manager.to_string())

    #print("")

    #string = """[[Finding the Answer is easy, it's finding the Question that's hard]] {{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] #[[[[schedule]]:ExpReset]] #[[[[interval]]:2]] #[[[[due]]:[[August 6th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:0]] #[[[[not_count]]:0]]"""
    #manager = RoamOrbiterManager.from_string(string)
    #print(manager.to_string())
    #manager.process_response(0)
    #print(manager.to_string())

    print("")

    #string = """{{[[TODO]]}} Maybe remove the spaces between key-value items because when I hide them, you end up with a bunch of ugly white space in block references to them eg: #[[Roam Orbit]] {{↑}} {{↓}} #[[[[feed]]:ToReview]] #[[[[schedule]]:ExpDefault]] #[[[[interval]]:2]] #[[[[due]]:[[August 5th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:Vote]] #[[[[↑_count]]:0]] #[[[[↓_count]]:0]]"""
    #print(string)
    #manager = RoamOrbiterManager.from_string(string)
    #print(manager.to_string())
    #manager.process_response(0)
    #print(manager.to_string())

    #print(" ")


    #string="""zero sum and non-zero sum games played at work/projects {{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] #[[[[schedule]]:ExpReset]] #[[[[interval]]:2]] #[[[[due]]:[[August 7th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:0]] #[[[[not_count]]:0]]"""
    #print(string)
    #manager = RoamOrbiterManager.from_string(string)
    #print(manager.to_string())
    #manager.process_response(1)
    #print(manager.to_string())
    #manager.process_response(0)
    #print(manager.to_string())

    #print(" ")


    #string = """{{[[TODO]]}} [[Fun Criterion]] {{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] #[[[[schedule]]:ExpReset]] #[[[[interval]]:2]] #[[[[due]]:[[August 5th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:0]] #[[[[not_count]]:0]]"""
    #print(string)
    #manager = RoamOrbiterManager.from_string(string)
    #print(manager.to_string())

    #print("")

    #string = """{{thought-provoking}} {{not}} #[[[[feed]]:ToThink]] #[[[[schedule]]:ExpReset]] #[[[[interval]]:2]] #[[[[due]]:[[August 6th, 2020]]]] #[[[[factor]]:3]] #[[[[feedback]]:ThoughtProvoking]] #[[[[thought-provoking_count]]:0]] #[[[[not_count]]:0]]"""
    #print(string)
    #manager = RoamOrbiterManager.from_string(string)
    #print(manager.to_string())

    #print("")

    string = """{{[[DONE]]}} [[Roam Orbit]]: When I add thoughts to a ToThink item, reschedule the item at the same interval as last interval. The idea is: that last interval was the right amount of space from the idea you needed until your thoughts developed or you came across new ideas to mix with it etc. So guess that the same interval is what you'll need again. If next time you don't have anything to add, then increase the interval. {{↑}} {{↓}} #[[[[feed]]:ToReview]] #[[[[schedule]]:ExpDefault]] #[[[[interval]]:4]] #[[[[due]]:[[August 12th, 2020]]]] #[[[[factor]]:2]] #[[[[feedback]]:Vote]] #[[[[↑_count]]:1]] #[[[[↓_count]]:0]] #[[[[done-date]]: 2020-08-08]] #@21:34 """
    print(string)
    manager = RoamOrbiterManager.from_string(string)
    print(manager.to_string())
    print("")