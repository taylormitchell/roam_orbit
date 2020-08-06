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



if __name__=="__main__":
    #unittest.main()
    text = """{{[[TODO]]}} How does an air conditioner work? #SomedayMaybe {{Review History: {"Interval": 0, "Past Reviews": [], "Next Review": "[[due: 2020-07-05]]"}}}"""
    text = main(text, "init", "ToReview")
    print(text)