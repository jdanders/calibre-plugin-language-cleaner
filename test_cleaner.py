import unittest
import re
from functools import partial
from cleaner import (
    keep_case, first_case, drop_first_match,
    dirty_a_list, clean_a_list, lord_list, vain_lord_list, re_list
)

class TestCleanerRegex(unittest.TestCase):

    def run_sub(self, pattern, sub, pcase, text):
        if pcase:
            return pattern.sub(partial(pcase, sub), text)
        else:
            return pattern.sub(sub, text)

    def check_list(self, regex_list, test_cases):
        """
        test_cases: list of (input_text, expected_output)
        """
        from cleaner import RuleEngine
        engine = RuleEngine(regex_list)
        for input_text, expected_output in test_cases:
            actual_output = engine.process_text(input_text)
            if actual_output != expected_output:
                self.fail(f"Got '{actual_output}' but expected '{expected_output}'")

    def test_keep_case(self):
        # Test keep_case function directly
        pattern = re.compile(r'word', re.I)
        self.assertEqual(keep_case('sub', pattern.match('word')), 'sub')
        self.assertEqual(keep_case('sub', pattern.match('WORD')), 'SUB')
        self.assertEqual(keep_case('sub', pattern.match('Word')), 'Sub')
        self.assertEqual(keep_case('substitution', pattern.match('Word')), 'Substitution')
        self.assertEqual(keep_case('sub', pattern.match('WOrd')), 'SUB')

    def test_dirty_a_list(self):
        cases = [
            ("Move ass!", "Move fast!"),
            ("HAUL ASS", "MOVE FAST"),
            ("haul ass", "move fast"),
            ("GET ASS", "MOVE FAST"),
            ("drag ass", "move fast"),
            ("little ass", "little donkey"),
            ("little asses", "little donkeys"),
            ("your ass", "your rear"),
            ("own ass", "own rear"),
            ("my ass", "my rear"),
            ("our ass", "our rear"),
            ("her ass", "her rear"),
            ("his ass", "his rear"),
            ("this ass", "this rear"),
            ("that ass", "that rear"),
            ("the ass", "the rear"),
            ("their ass", "their rear"),
            ("those ass", "those rear"),
            ("these ass", "these rear"),
            ("its ass", "its rear"),
            ("for ass", "for rear"),
            ("your asses", "your rears"),
            ("own asses", "own rears"),
            ("my asses", "my rears"),
            ("our asses", "our rears"),
            ("her asses", "her rears"),
            ("his asses", "his rears"),
            ("this asses", "this rears"),
            ("that asses", "that rears"),
            ("the asses", "the rears"),
            ("their asses", "their rears"),
            ("those asses", "those rears"),
            ("these asses", "these rears"),
            ("its asses", "its rears"),
            ("for asses", "for rears"),
            ("an ass", "a jerk"),
            ("Asses", "Rears"),
            ("ass", "rear"),
        ]
        self.check_list(dirty_a_list, cases)

    def test_clean_a_list(self):
        cases = [
            ("move ass", "move fast"),
            ("haul ass", "move fast"),
            ("get ass", "move fast"),
            ("drag ass", "move fast"),
            ("MOVE ASS", "MOVE FAST"),
            ("asses", "donkeys"),
            ("an Ass", "a Donkey"),
            ("an ass", "a donkey"),
            ("ass", "donkey"),
            ("in ass", "in ass"),
        ]
        self.check_list(clean_a_list, cases)


    def test_lord_list(self):
        cases = [
            ("Thank God", "Thank goodness"),
            ("Thank Jesus", "Thank goodness"),
            ("Thank Jesus Christ", "Thank goodness"),
            ("Thank Christ", "Thank goodness"),
            ("thank you, God", "thank goodness"),
            ("thank you, Jesus", "thank goodness"),
            ("thank you, Jesus Christ", "thank goodness"),
            ("thank you, Christ", "thank goodness"),
            ("My God!", "My goodness!"),
            ("My Jesus!", "My goodness!"),
            ("My Jesus Christ!", "My goodness!"),
            ("My Christ!", "My goodness!"),
            ("Oh, God", "Oh goodness"),
            ("Oh, Jesus", "Oh goodness"),
            ("Oh, Jesus Christ", "Oh goodness"),
            ("Oh, Christ", "Oh goodness"),
            ("Good God", "Goodness"),
            ("Good Jesus", "Goodness"),
            ("Good Jesus Christ", "Goodness"),
            ("Good Christ", "Goodness"),
            ("name of God", "world"),
            ("name of Jesus", "world"),
            ("name of Jesus Christ", "world"),
            ("name of Christ", "world"),
            ("where in God's name", "where in the world"),
            ("what in God's name", "what in the world"),
            ("how in God's name", "how in the world"),
            ("why in God's name", "why in the world"),
            ("when in God's name", "when in the world"),
            ("where in Jesus's name", "where in the world"),
            ("where in Jesus Christ's name", "where in the world"),
            ("where in Christ's name", "where in the world"),
            ("in God's name", "for goodness sake"),
            ("in Jesus's name", "for goodness sake"),
            ("in Jesus Christ's name", "for goodness sake"),
            ("in Christ's name", "for goodness sake"),
            ("in God", "in the lord"),
            ("in Jesus", "in the lord"),
            ("in Jesus Christ", "in the lord"),
            ("in Christ", "in the lord"),
            ("to God", "to heaven"),
            ("to Jesus", "to heaven"),
            ("to Jesus Christ", "to heaven"),
            ("to Christ", "to heaven"),
            ("to God Himself", "to heaven"),
            ("by God", "by the heavens"),
            ("by Jesus", "by the heavens"),
            ("by Jesus Christ", "by the heavens"),
            ("by Christ", "by the heavens"),
            ("God knows", "heaven knows"),
            ("Jesus knows", "heaven knows"),
            ("Jesus Christ knows", "heaven knows"),
            ("Christ knows", "heaven knows"),
            (". God knows", ". Heaven knows"),
            ("for God's sake", "for goodness sake"),
            ("for Jesus's sake", "for goodness sake"),
            ("for Jesus Christ's sake", "for goodness sake"),
            ("for Christ's sake", "for goodness sake"),
            ("Godforsaken", "forsaken"),
            ("Jesusforsaken", "forsaken"),
            ("Jesus Christforsaken", "forsaken"),
            ("Christforsaken", "forsaken"),
            ("godawful", "forsaken"),
            ("jesusawful", "forsaken"),
            ("jesus christawful", "forsaken"),
            ("christawful", "forsaken"),
        ]
        self.check_list(lord_list, cases)

    def test_vain_lord_list(self):
        cases = [
            ("thanked God", "thanked heaven"),
            ("thanked Jesus", "thanked heaven"),
            ("thanked Christ", "thanked heaven"),
            ("thanked Jesus Christ", "thanked heaven"),
            (".  Jesus!", ".  Goodness!"),
            (".  God!", ".  Goodness!"),
            (".  Christ!", ".  Goodness!"),
            (".  Jesus Christ", ".  Goodness"),
            (".  Jesus-Christ", ".  Goodness"),
            (".  Jesus Almighty", ".  Goodness"),
            (".  Christ", ".  Goodness"),
        ]
        self.check_list(vain_lord_list, cases)

    def test_re_list_tits_slut_topless(self):
        self.check_list(re_list, [
            ("tits", "belly"),
            ("TITS", "BELLY"),
            ("tit for tat", "tit for tat"),
            ("slut", "hussy"),
            ("sluts", "hussies"),
            ("topless bar", "bar"),
        ])

    def test_re_list_whorehouse_crap(self):
        self.check_list(re_list, [
            ("whorehouse", "brothel"),
            ("take a crap", "use the toilet"),
            ("take a crapper", "use the toilet"),
            ("crapper", "toilet"),
            ("crap", "garbage"),
            ("crapped", "wet"),
        ])

    def test_re_list_cock_cunt_damn(self):
        self.check_list(re_list, [
            ("cock-up", "mess up"),
            ("cocksucker", "sucker"),
            ("cocker", "idiot"),
            ("cocker spaniel", "cocker spaniel"),
            ("cunt", "groin"),
            ("Goddammit", "Dang it"),
            ("dammit", "dang it"),
        ])

    def test_re_list_ass_varieties(self):
        self.check_list(re_list, [
            ("smart ass", "smart aleck"),
            ("smart-ass", "smart aleck"),
            ("kissing ass", "kissing up"),
            ("kiss my ass", "fly a kite"),
            ("kick ass", "kick booty"),
            ("cover your ass", "cover your rear"),
            ("kick his ass", "kick his rear"),
            ("jackass", "jerk"),
            ("bray like a jackass", "bray like a donkey"),
            ("asshole", "jerk"),
            ("horse's ass", "jerk"),
        ])

    def test_re_list_damn_varieties(self):
        # Clancy's favorites
        clancy_words = ["sure", "near", "sight", "good", "much", "hard", "easy", "big", "little", "glad", "clever", "mess", "smart", "fine", "fool", "right", "thing", "shame", "nice", "mean", "bad", "lucky", "late", "important"]
        # Note: 'damn near' is already handled by a previous rule, so it will be replaced by 'nearly'
        # Other clancy words match 'damned [word]'
        clancy_cases = [(f"damned {word}", f"{word}") for word in clancy_words]
        # 'damn [word]' matches the catch-all 'damn' -> 'dang'
        clancy_cases += [(f"damn {word}", f"dang {word}") for word in clancy_words if word != "near"]
        clancy_cases += [("damn near", "nearly")]

        # Lookbehind variations
        lookbehind_words = ["your", "our", "her", "his", "this", "that", "the", "their", "hose", "these", "for", "so", "some", "one", "one more", "too"]
        lookbehind_cases = [(f"{word} damn", f"{word}") for word in lookbehind_words]
        lookbehind_cases += [(f"{word} damned", f"{word}") for word in lookbehind_words]

        cases = [
            ("be damned", "be darned"),
            ("be goddamned", "be darned"),
            ("be gods damned", "be darned"),
            ("give a damn", "care"),
            ("gives a damn", "cares"),
            ("give a god damn", "care"),
            ("damn near", "nearly"),
            ("god damn near", "nearly"),
            ("worth a damn", "worth a cent"),
            ("worth a god damn", "worth a cent"),
            ("of the damned", "of the cursed"),
            ("of the god damned", "of the cursed"),
            ("a damn", "a blasted"),
            ("a god damn", "a blasted"),
            ("damn sure", "dang sure"),
            ("damned well", "darn well"),
            ("damn well", "darn well"),
            ("god damned well", "darn well"),
            ("damnedest", "very best"),
            ("god damnedest", "very best"),
            ("damning", "condemning"),
            ("god damning", "condemning"),
            ("damnable", "condemning"),
            ("god damnable", "condemning"),
            ("damnably", "cursedly"),
            ("god damnably", "cursedly"),
            ("damnatory", "condemning"),
            ("god damnatory", "condemning"),
            ("damnation", "condemnation"),
            ("god damnation", "condemnation"),
            (", damn it all", ""),
            (", god damn it all", ""),
            ("damn it all, x", "x"),
            ("a damn nuisance", "a blasted nuisance"),
            ("damn you to hell", "curse you"),
            ("god damn you to hell", "curse you"),
            ("damn him", "curse him"),
            ("damn his", "curse his"),
            ("damn her", "curse her"),
            ("damn you", "curse you"),
            ("damn next", "curse next"),
            ("damn the", "curse the"),
            ("damn", "dang"),
            ("god damn", "dang"),
        ] + clancy_cases + lookbehind_cases
        self.check_list(re_list, cases)

    def test_re_list_bitch_shit(self):
        cases = [
            ("son of a bitch", "jerk"),
            ("son of bitch", "jerk"),
            ("sons-of-bitches", "jerks"),
            ("bitchin'", "complaining"),
            ("bitched", "complained"),
            ("bitches about", "complains about"),
            ("not bitch", "not complain"),
            ("it's a bitch", "it's tough"),
            ("bitch", "jerk"),
            ("bitches", "jerks"),
            ("bullshit", "rubbish"),
            ("horseshit", "rubbish"),
            ("dogshit", "rubbish"),
            ("jackshit", "rubbish"),
            ("bull-shit", "rubbish"),
            ("holy shit", "incredible"),
            ("holy-shit", "incredible"),
            ("oh, shit", "oh, shoot"),
            ("oh shit", "oh shoot"),
            ("--shit", "--shoot"),
            ("no shit", "no kidding"),
            ("know shit", "know squat"),
            ("shitload", "load"),
            ("shit-load", "load"),
            ("shitcan", "trash"),
            ("shit-can", "trash"),
            ("shitpot", "toilet"),
            ("shit-pot", "toilet"),
            ("shithead", "idiot"),
            ("shit-head", "idiot"),
            ("shithole", "pile of trash"),
            ("shit-hole", "pile of trash"),
            ("shittin'", "kiddin'"),
            ("shitter", "toilet"),
            ("shitty", "nasty"),
            (" shit-filled", ""),
            ("give a shit", "give a hoot"),
            ("got shit", "got nothing"),
            ("some shit", "some trash"),
            ("Shit!", "Shoot!"),
            ("shit", "rubbish"),
        ]
        self.check_list(re_list, cases)

    def test_re_list_f_bomb(self):
        cases = [
            ("fuck", "idiot"), # Rule: fuck -> zxsa -> idiot
            ("motherfuck", "idiot"), # Rule: motherfuck -> zxsa -> idiot
            ("muthafuck", "idiot"),
            ("fook", "idiot"),
            ("motherfook", "idiot"),
            ("Zxsa yourself", "Kill yourself"),
            ("Zxsa-yourself", "Kill yourself"),
            ("cluster zxsa", "massive failure"),
            ("cluster-zxsa", "massive failure"),
            ("zxsa your", "harass your"),
            ("zxsa you", "forget you"),
            ("the zxsa", "the heck"),
            ("you zxsa up", "you mess up"),
            ("you zxsa with", "you mess with"),
            ("zxsas around", "messes around"),
            ("zxsas with", "messes with"),
            ("zxsas on", "messes on"),
            ("zxsas up", "messes up"),
            ("zxsas over", "messes over"),
            ("zxsas under", "messes under"),
            ("zxsas through", "messes through"),
            ("zxsain around", "messin around"),
            ("zxsain' around", "messin' around"),
            ("zxsas around", "messes around"),
            ("zxsain a", "unbelievable"),
            (" zxsain well x", " x"),
            ("zxsain well x", " x"),
            ("zxsain", "frigging"),
            ("zxsaer", "idiot"),
            ("zxsa it", "phoo"),
            ("zxsa-it", "phoo"),
            ("zxsaed", "messed"),
            ("zxsa the", "forget the"),
            ("zxsa our", "harass our"),
            ("zxsa her", "harass her"),
            ("zxsa his", "harass his"),
            ("zxsa us", "harass us"),
            ("zxsa this", "harass this"),
            ("zxsa that", "harass that"),
            ("zxsa their", "forget their"),
            ("zxsa those", "harass those"),
            ("zxsa these", "forget these"),
            ("zxsa them", "forget them"),
            ("zxsa 'em", "harass 'em"),
            ("zxsa for", "harass for"),
            ("zxsa a", "harass a"),
            ("zxsaed our", "harassed our"),
            ("to zxsa", "to mess"),
            ("zxsa up", "mess up"),
            ("zxsa", "idiot"),
        ]
        self.check_list(re_list, cases)

    def test_re_list_dick_bastard_hell(self):
        hell_questions = ["how", "for", "where", "what", "whatever", "who", "why", "when"]
        hell_q_cases = [(f"{q} the hell", f"{q} the heck") for q in hell_questions]

        cases = [
            ("Dick around", "Mess around"),
            ("Dick with", "Mess with"),
            ("Dick on", "Mess on"),
            ("Dick up", "Mess up"),
            ("Dick over", "Mess over"),
            ("Dick under", "Mess under"),
            ("Dick through", "Mess through"),
            ("dickin' around", "messin' around"),
            ("dickhead", "jerk"),
            ("dickweed", "jerk"),
            ("know dick", "know squat"),
            ("dick", "toe"),
            ("bastard", "mongrel"),
            ("hellhound", "demonhound"),
            ("hell-hound", "demonhound"),
            ("hell-bent", "demon-bent"),
            ("hell's bells", "by golly"),
            ("to hell with", "forget"),
            ("the hell with", "forget"),
            ("hell with", "heck with"),
            ("beats the hell out of", "beats"),
            ("to hell", "to perdition"),
            ("some hell", "some trouble"),
            ("give him hell", "give him trouble"),
            ("gave him hell", "gave him trouble"),
            ("raising hell", "raising trouble"),
            ("raises hell", "raises trouble"),
            ("chance in hell x", "chance x"),
            ("burn in hell x", "burn x"),
            ("living hell", "living prison"),
            ("for the hell", "for the heck"),
            ("what the hell!", "what the heck!"),
            ("the hell x", "x"),
            ("sure as hell ", "sure "),
            ("way in hell x", "way x"),
            ("what in hell x", "what x"),
            ("but hell", "but heck"),
            ("to be hell", "to be terrible"),
            ("is hell", "is perdition"),
            ("it's hell", "it's perdition"),
            ("Aw, hell", "Aw, heck"),
            ("catch hell", "get in trouble"),
            ("caught hell", "got in trouble"),
            ("as hell ", "as could be"),
            ("of hell", "of torture"),
            ("all hell", "all perdition"),
            ("hell was", "heck was"),
            ("hell to pay", "heck to pay"),
            ("bloody hell", "bloody heck"),
            ("dang hell", "dang heck"),
            ("look like hell", "look like mad"),
            ("looked like hell", "looked really bad"),
            ("hurt like hell", "hurt like mad"),
            ("felt like hell", "felt like garbage"),
            ("LIKE HELL", "NOT A CHANCE"),
            ("like hell", "like mad"),
            ("the hell I", "the heck I"),
            ("hell of ", "heck of "),
            ("hell out", "heck out"),
            ("hell off ", "heck off "),
            ("hell do ", "heck do "),
            ("hell are ", "heck are "),
            ("hellish", "unpleasant"),
            ("this hell", "this pit"),
            ("real hell", "real pit"),
            ("this hellhole", "this pit"),
            ("this hellpit", "this pit"),
            ("hell's", "perditions's"),
            (".  hell,", ".  heck,"),
            (">hell<", ">perdition<"),
        ] + hell_q_cases
        self.check_list(re_list, cases)

    def test_language_check(self):
        from cleaner import language_check, vain_lord_list, dirty_a_list, clean_a_list

        # Test default
        rules = language_check("Normal text")
        self.assertNotIn(vain_lord_list[0], rules)
        self.assertIn(clean_a_list[0], rules)

        # Test vain lord
        rules = language_check("fuck")
        self.assertIn(vain_lord_list[0], rules)

        # Test dirty ass
        rules = language_check("asshole")
        self.assertIn(dirty_a_list[0], rules)

    def test_first_case_upper(self):
        cases = [
            ("THANK GOD", "THANK GOODNESS"),
        ]
        self.check_list(lord_list, cases)

    def test_clean_text_integrated(self):
        from cleaner import clean_text
        text = "This is a damn nuisance."
        expected = "This is a blasted nuisance."
        self.assertEqual(clean_text(text), expected)

    def test_exceptions(self):
        # Trigger first_case exception
        from cleaner import first_case
        class MockMatch:
            def group(self, n): return ""
        first_case("sub", MockMatch())

        # Trigger drop_first_match exception
        from cleaner import drop_first_match
        class MockMatch2:
            def group(self, n):
                if n == 1: return "A"
                if n == 2: return None
            def groups(self): return ("A", None)
        drop_first_match("sub", MockMatch2())

if __name__ == '__main__':
    unittest.main()
