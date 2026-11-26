import unittest
import re
import difflib
import os
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
                self.fail(f"Input '{input_text}': Got '{actual_output}' but expected '{expected_output}'")

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
            ("Move arse!", "Move fast!"),
            ("HAUL ASS", "MOVE FAST"),
            ("haul arse", "move fast"),
            ("GET ASS", "MOVE FAST"),
            ("drag ass", "move fast"),
            ("little ass", "little donkey"),
            ("little-ass", "little donkey"),  # \W? matches -
            ("little arse", "little donkey"),
            ("little asses", "little donkeys"),
            ("your ass", "your rear"),
            ("your arse", "your rear"),
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
            ("an arse", "a jerk"),
            ("Asses", "Rears"),
            ("ass", "rear"),
            ("arse", "rear"),
        ]
        self.check_list(dirty_a_list, cases)

    def test_clean_a_list(self):
        cases = [
            ("move ass", "move fast"),
            ("move arse", "move fast"),
            ("haul ass", "move fast"),
            ("get ass", "move fast"),
            ("drag ass", "move fast"),
            ("MOVE ASS", "MOVE FAST"),
            ("asses", "donkeys"),
            ("an Ass", "a Donkey"),
            ("an ass", "a donkey"),
            ("an arse", "a fool"),
            ("ass", "donkey"),
            ("arse", "rear"),
            ("in ass", "in ass"),
            ("<b>ass</b>", "<b>ass</b>"),
        ]
        from cleaner import language_check
        rules = language_check(
            'sample', replace_crude=False, replace_british=True,
            replace_ass=True, ass_override='clean',
        )
        self.check_list(rules, cases)


    def test_lord_list(self):
        cases = [
            ("Thank God", "Thank goodness"),
            ("thank you God", "thank goodness"),
            ("Thank Jesus", "Thank goodness"),
            ("Thank Jesus Christ", "Thank goodness"),
            ("Thank God of Israel", "Thank God of Israel"),
            ("Thank Christ", "Thank goodness"),
            ("thank you, God", "thank goodness"),
            ("thank you, Jesus", "thank goodness"),
            ("thank you, Jesus Christ", "thank goodness"),
            ("thank you, Christ", "thank goodness"),
            ("My God!", "My goodness!"),
            ("My Jesus!", "My goodness!"),
            ("My Jesus Christ!", "My goodness!"),
            ("My Christ!", "My goodness!"),
            ("my God's", "my goodness's"),  # s is captured by s? in My God rule
            ("Oh, God", "Oh goodness"),
            ("oh God", "oh goodness"),
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
            ("Jesus!", "Goodness!"),
            ("Christ", "Goodness"),
        ]
        self.check_list(vain_lord_list, cases)

    def test_re_list_tits_slut_topless(self):
        self.check_list(re_list, [
            ("tits", "belly"),
            ("TITS", "BELLY"),
            ("tit for tat", "tit for tat"),
            ("tit-tat-toe", "tit-tat-toe"),
            ("titular", "titular"),
            ("slut", "trollop"),
            ("sluts", "trollops"),
            ("sheeny", "man"),
            ("nigger", "person"),
            ("topless bar", "bar"),
            ("topless-bar", "bar"),
            ("blasted zxsain windpipe", "blasted windpipe"),
        ])

    def test_slurs_generalize_without_changing_identity_terms(self):
        from cleaner import RuleEngine, slur_list
        engine = RuleEngine(slur_list)
        cases = [
            ('bad niggers', 'bad people'),
            ('a nigger', 'a person'),
            ("a nigger's hat", "a person's hat"),
            ('thick niggerlips', 'thick lips'),
            ('thick nigger lips', 'thick lips'),
            ('nigger straw', 'straw'),
            ('what did she marry a coon like that for?',
             'what did she marry a person like that for?'),
            ('coloured coons in white suits', 'people in white suits'),
            ('cutest colour coon', 'cutest person'),
            ('dirty Jew', 'dirty person'),
            ('the little jewy', 'the little fellow'),
            ('those jewies does', 'those people do'),
            ('the jewman', 'the man'),
            ('sheeny', 'man'),
            ('sheenies', 'men'),
            ('Jew and Jews are Jewish people.', 'Jew and Jews are Jewish people.'),
            ('A raccoon crossed the road.', 'A raccoon crossed the road.'),
            ('a coon hat', 'a coon hat'),
        ]
        for original, expected in cases:
            self.assertEqual(engine.process_line(original), expected)
        self.assertEqual(
            engine.process_text('marry a coon like\nthat for?'),
            'marry a person like\nthat for?',
        )

    def test_re_list_whorehouse_crap(self):
        self.check_list(re_list, [
            ("whorehouse", "brothel"),
            ("take a crap", "use the toilet"),
            ("take-a-crap", "use the toilet"),
            ("take a crapper", "use the toilet"),
            ("crapper", "toilet"),
            ("crap", "garbage"),
            ("crapped", "wet"),
        ])

    def test_re_list_cock_cunt_damn(self):
        self.check_list(re_list, [
            ("cock-up", "mess up"),
            ("cockup", "mess up"),
            ("cocksucker", "jerk"),
            ("cocker", "idiot"),
            ("you cocker!", "you idiot!"),
            ("cocker's", "idiot's"),
            ("cocker spaniel", "cocker spaniel"),
            ("cocker spaniels", "cocker spaniels"),
            ("cocker-spaniel", "cocker-spaniel"),
            ("cocker-spaniels", "cocker-spaniels"),
            ("cunt", "jerk"),
            ("CUNT", "JERK"),
            ("cunts", "jerks"),
            ("cunty", "obnoxious"),
            ("you cunt", "you jerk"),
            ("you absolute cunt", "you absolute jerk"),
            ("He is a miserable cunt", "He is a miserable jerk"),
            ("What a miserable cunt he is.", "What a miserable jerk he is."),
            ("you cunts", "you jerks"),
            ("you absolute cunts", "you absolute jerks"),
            ("Goddammit", "Dang it"),
            ("Goddamnit, I grumbled", "Dang it, I grumbled"),
            ("dammit", "dang it"),
        ])

    def test_re_list_contextual_profanity_phrases(self):
        self.check_list(re_list, [
            ("Some cunt done buggered up the system.", "Some jerk done messed up the system."),
            # Keep crotch replacements for clearly anatomical references.
            ("He got kicked in the cunt.", "He got kicked in the crotch."),
            ("He got a kick to the cunt.", "He got a kick to the crotch."),
            ("He injured her cunt.", "He injured her crotch."),
            ("The train was locked tighter than an octoid's cunt.", "The train was locked tighter than an octoid's crotch."),
            ("the grey sunken cunt of the world", "the grey sunken crotch of the world"),
            ("the grey cunt of the world", "the grey crotch of the world"),
            ("Oh, fuck.", "Oh, shoot."),
            ("Holy fuck.", "Unbelievable."),
            ("Fuck, man.", "Shoot, man."),
            ("We'd be fucked.", "We'd be in trouble."),
            ("We just got fucked.", "We just got screwed."),
            ("I hate this mental typing shit.", "I hate this mental typing nonsense."),
            ("Don't give me shit.", "Don't give me a hard time."),
            ("That was scary as shit.", "That was very scary."),
            ("Scary as shit.", "Very scary."),
            ("There was a shitload of monsters.", "There was a lot of monsters."),
            ("Don't give me a shitty pour.", "Don't give me a bad pour."),
        ])

    def test_re_list_ass_varieties(self):
        self.check_list(re_list, [
            ("smart ass", "smart aleck"),
            ("smart-ass", "smart aleck"),
            ("smart arse", "smart aleck"),
            ("kissing ass", "kissing up"),
            ("kissing arse", "kissing up"),
            ("kissin' ass", "kissing up"),
            ("kiss my ass", "fly a kite"),
            ("kiss my arse", "fly a kite"),
            ("kiss your arse", "fly a kite"),
            ("kiss my royal Irish arse", "fly a kite"),
            ("arse", "rear"),
            ("kick ass", "kick booty"),
            ("kick arse", "kick booty"),
            ("cover your ass", "cover your rear"),
            ("cover his arse", "cover his rear"),
            ("kick his ass", "kick his rear"),
            ("jackass", "jerk"),
            ("bray like a jackass", "bray like a donkey"),
            ("asshole", "jerk"),
            ("an-asshole", "a jerk"),
            ("horse's ass", "jerk"),
            ("horse's arse", "jerk"),
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
        lookbehind_words = ["your", "our", "her", "his", "this", "that", "the", "their", "those", "these", "for", "so", "some", "one", "one more", "too"]
        lookbehind_cases = [(f"{word} damn", f"{word}") for word in lookbehind_words]
        lookbehind_cases += [(f"{word} damned", f"{word}") for word in lookbehind_words]

        cases = [
            ("be damned", "be darned"),
            ("be goddamned", "be darned"),
            ("be gods-damned", "be darned"),
            ("be gods damned", "be darned"),
            ("give a damn", "care"),
            ("give him a damn", "care"),
            ("gives a damn", "cares"),
            ("give a god damn", "care"),
            ("damn near", "nearly"),
            ("god damn near", "nearly"),
            ("gods damn near", "nearly"),
            ("worth a damn", "worth a cent"),
            ("worth a god damn", "worth a cent"),
            ("the damned", "the"),
            ("of the damned", "of the cursed"),
            ("of the god damned", "of the cursed"),
            ("a damn nuisance", "a blasted nuisance"),
            ("a damn", "a cent"),
            ("a god damn", "a cent"),
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
            ("gods damn", "dang"),
        ] + clancy_cases + lookbehind_cases
        self.check_list(re_list, cases)

    def test_re_list_bitch_shit(self):
        cases = [
            ("son of a bitch", "jerk"),
            ("sun of a bitch", "jerk"),
            ("son ov a bitch", "jerk"),
            ("son of bitch", "jerk"),
            ("sons-of-bitches", "jerks"),
            ("bitchin'", "complaining"),
            ("bitched", "complained"),
            ("bitches about", "complains about"),
            ("not bitch", "not complain"),
            ("it's a bitch", "it's tough"),
            ("bitch", "jerk"),
            ("bitches", "jerks"),
            ("bitchbody", "jerkbody"),
            ("bullshit", "rubbish"),
            ("bull.shit", "rubbish"),
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
            ("That guy will be shitting ice cubes for the next three seasons.", "That guy will be pooping ice cubes for the next three seasons."),
            ("shitter", "toilet"),
            ("shitty", "nasty"),
            (" shit-filled", ""),
            ("give a shit", "give a hoot"),
            ("got shit", "got nothing"),
            ("some shit", "some trash"),
            ("Shit!", "Shoot!"),
            ("shite", "rubbish"),
            ("give a shite", "give a hoot"),
            ("shit", "rubbish"),
        ]
        self.check_list(re_list, cases)

    def test_re_list_f_bomb(self):
        cases = [
            ("The system tended to fuck you over.", "The system tended to cheat you."),
            ("This is a bigger fuck you to the showrunners.", "This is a bigger insult to the showrunners."),
            ("How is this a fuck you to the boss people?", "How is this an insult to the boss people?"),
            ("They could all go fuck themselves.", "They could all go get lost."),
            ("They should fuck themselves.", "They should get lost."),
            ("For fuck's sake.", "For goodness’ sake."),
            ("Oh, for fuck’s sake, Mordecai.", "Oh, for goodness’ sake, Mordecai."),
            ("Oh fuck this.", "Oh, forget this."),
            ("Oh, fuck this.", "Oh, forget this."),
            ("Yeah, fuck this.", "Yeah, forget this."),
            ("Yeah, fuck that.", "Yeah, forget that."),
            ("Fuck off, Mordecai.", "Go away, Mordecai."),
            ("fuck", "idiot"), # Rule: fuck -> zxsa -> idiot
            ("motherfuck", "idiot"), # Rule: motherfuck -> zxsa -> idiot
            ("mother-fuck", "idiot"),
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
            (" zxsain well ", " "),
            (" zxsain well,", ","),
            ("zxsain", "frigging"),
            ("zxsaer", "idiot"),
            ("zxsa it", "phoo"),
            ("zxsa-it", "phoo"),
            ("zxsa it all", "phoo"),
            ("zxsaed", "messed"),
            ("zxsa the", "forget the"),
            ("zxsa our", "harass our"),
            ("zxsa her", "harass her"),
            ("zxsa his", "harass his"),
            ("zxsa old", "curse old"),
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
            ("bastard son", "mongrel son"),
            ("you bastard", "you mongrel"),
            ("those bastards", "those mongrels"),
            ("hellhound", "demonhound"),
            ("hell-hound", "demonhound"),
            ("helldiver", "helldiver"),
            ("hell-bent", "demon-bent"),
            ("hell's bells", "by golly"),
            ("to hell with", "forget"),
            ("the hell with", "forget"),
            ("hell with", "heck with"),
            ("beats the hell out of", "beats"),
            ("where the blue hell am I?", "where the heck am I?"),
            ("not in hell", "not in perdition"),
            ("snowball in hell", "snowball in perdition"),
            ("Hell open to christians", "Perdition open to christians"),
            ("O hell!", "Oh heck!"),
            ("Oh hell yeah!", "Oh, absolutely!"),
            ("Oh, hell yeah!", "Oh, absolutely!"),
            ("Hell yeah!", "Absolutely!"),
            ("hell yea", "absolutely"),
            ("Oh hell yes!", "Oh, absolutely!"),
            ("Hell no!", "Absolutely not!"),
            ("Oh hell no!", "Oh, absolutely not!"),
            ("Oh hell!", "Oh no!"),
            ("God thrust Satan down to hell.", "God thrust Satan down to perdition."),
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
            ("bloody hell", "heck"),
            ("like bloody hell", "like heck"),
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
            ("hell's", "perdition's"),
            (".  hell,", ".  heck,"),
            (">hell<", ">perdition<"),
            (", \"hell,", ", \"heck,"),
        ] + hell_q_cases
        self.check_list(re_list, cases)

    def test_language_check(self):
        from cleaner import language_check, vain_lord_list

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

    def test_unambiguous_profanity_auto_detect(self):
        """Unambiguous profanities (cunt, cocksucker, etc.) trigger profane register."""
        from cleaner import language_check, vain_lord_list, dirty_a_list, clean_a_list

        # 'cunt' must trigger exclamatory/vain register for religious expressions
        rules = language_check("What a miserable cunt he is.")
        self.assertIn(vain_lord_list[0], rules)

        # 'cocksucker' must trigger exclamatory/vain register
        rules = language_check("You cocksucker!")
        self.assertIn(vain_lord_list[0], rules)

        # Religious exclamations with comma or period (not just '!') must trigger vain register
        rules = language_check("For Christ's sake, hurry up.")
        self.assertIn(vain_lord_list[0], rules)

        rules = language_check("Holy Jesus, that was close.")
        self.assertIn(vain_lord_list[0], rules)

    def test_fbomb_compound_replacements(self):
        from cleaner import clean_text
        self.assertEqual(clean_text('fuckwit'), 'idiot')
        self.assertEqual(clean_text('fuckwits'), 'idiots')
        self.assertEqual(clean_text('fuckface'), 'jerk')
        self.assertEqual(clean_text('fuckhead'), 'idiot')
        self.assertEqual(clean_text('fuckboy'), 'jerk')
        self.assertEqual(clean_text('unfuckingbelievable'), 'unbelievable')

    def test_clean_text_with_stats(self):
        from cleaner import clean_text_with_stats
        cleaned, stats = clean_text_with_stats('fuck\nplain')
        self.assertEqual(cleaned, 'idiot\nplain')
        self.assertEqual(stats, {
            'lines_total': 2,
            'lines_changed': 1,
            'rule_substitutions': 2,
        })

    def test_reviewed_inflections_and_compounds(self):
        from cleaner import clean_text
        cases = [
            ('bitches', 'jerks'),
            ('bitchy', 'mean'),
            ('bitchiness', 'meanness'),
            ('he shits', 'he defecates'),
            ('dipshits', 'idiots'),
            ('go apeshit', 'go wild'),
            ('batshit crazy', 'completely crazy'),
            ('shitfaced', 'drunk'),
            ('badass', 'tough'),
            ('half-assed', 'half-baked'),
            ('asswipes', 'jerks'),
            ('whore', 'prostitute'),
            ('whores', 'prostitutes'),
            ('whoredom', 'prostitution'),
            ('scrotumtightening sea', 'gut-tightening sea'),
        ]
        for original, expected in cases:
            self.assertEqual(clean_text(original), expected)

    def test_unambiguous_profanity_respects_crude_preference(self):
        """Terms skip contextual detection but still follow the crude toggle."""
        from cleaner import language_check, RuleEngine, unambiguous_profanity_list, crude_non_ass_list

        # Unambiguous and context-sensitive crude rules both follow replace_crude.
        rules_no_crude = language_check("sample", replace_crude=False)
        for r in unambiguous_profanity_list:
            self.assertNotIn(r, rules_no_crude)
        for r in crude_non_ass_list:
            self.assertNotIn(r, rules_no_crude)

        engine_no_crude = RuleEngine(rules_no_crude)
        self.assertEqual(engine_no_crude.process_line("He called her a cunt."), "He called her a cunt.")
        self.assertEqual(engine_no_crude.process_line("You cocksucker, you."), "You cocksucker, you.")
        self.assertEqual(engine_no_crude.process_line("He is an asshole."), "He is an asshole.")
        self.assertEqual(engine_no_crude.process_line("What a slut."), "What a slut.")
        self.assertEqual(engine_no_crude.process_line("I need to take a crap."), "I need to take a crap.")

        # With crude cleanup on, contextual override values don't suppress them.
        rules = language_check("sample", replace_crude=True, ass_override='clean', vain_override='never')
        for r in unambiguous_profanity_list:
            self.assertIn(r, rules)

    def test_crude_subgroups_are_independently_selectable(self):
        from cleaner import (language_check, strong_profanity_list, fbomb_list,
                             sexual_anatomical_list, crude_insult_list,
                             mild_crude_list, british_list, RuleEngine)
        rules = language_check(
            'sample', replace_crude=False,
            replace_strong=True, replace_sexual=False,
            replace_insults=False, replace_mild_crude=False,
            replace_british=False,
        )
        self.assertTrue(all(rule in rules for rule in strong_profanity_list))
        self.assertTrue(all(rule in rules for rule in fbomb_list))
        for group in (sexual_anatomical_list, crude_insult_list,
                      mild_crude_list, british_list):
            for rule in group:
                self.assertNotIn(rule, rules)

    def test_british_rules_are_context_guarded(self):
        from cleaner import RuleEngine, british_list
        engine = RuleEngine(british_list)
        self.assertEqual(engine.process_line('You absolute twat!'), 'You fool!')
        self.assertEqual(engine.process_line('What a bunch of twats!'), 'What a bunch of fools!')
        self.assertEqual(engine.process_line('You wanker!'), 'You idiot!')
        self.assertEqual(engine.process_line('What a load of bollocks.'), 'What a load of nonsense.')
        self.assertEqual(engine.process_line('Bugger off!'), 'Go away!')
        self.assertEqual(engine.process_line('Where the bugger is it?'), 'Where the heck is it?')
        self.assertEqual(engine.process_line("The poor bugger's tool."), "The poor fellow's tool.")
        self.assertEqual(engine.process_line('The poor buggers waited.'), 'The poor fellows waited.')
        self.assertEqual(engine.process_line('I am buggered.'), 'I am exhausted.')
        self.assertEqual(engine.process_line('That is a bloody awful idea.'), 'That is a very awful idea.')
        self.assertEqual(engine.process_line('He is a bloody fool.'), 'He is a fool.')
        self.assertEqual(engine.process_line('Most bloody awful story.'), 'Most awful story.')
        self.assertEqual(engine.process_line('He was bloody lucky.'), 'He was very lucky.')
        self.assertEqual(engine.process_line('These bloody English!'), 'These English!')
        self.assertEqual(engine.process_line('A bloody swindle.'), 'A swindle.')
        self.assertEqual(engine.process_line('Choking with bloody foolery.'), 'Choking with foolery.')
        self.assertEqual(engine.process_line('Hanging over the bloody paper.'), 'Hanging over the paper.')
        self.assertEqual(engine.process_line('Those bloody (wait for it) cuckoos.'), 'Those (wait for it) cuckoos.')
        self.assertEqual(engine.process_line('The bloody nag took fright.'), 'The nag took fright.')
        self.assertEqual(engine.process_line('Bloody wars, says I.'), 'Wars, says I.')
        # Avoid changing literal blood references and the ordinary verb "prick".
        self.assertEqual(engine.process_line('She had a bloody nose.'), 'She had a bloody nose.')
        self.assertEqual(engine.process_line('Rawhead and bloody bones.'), 'Rawhead and bloody bones.')
        self.assertEqual(engine.process_line('Bloody bridge is over there.'), 'Bloody bridge is over there.')
        self.assertEqual(engine.process_line('He was bloodying the sea.'), 'He was bloodying the sea.')
        self.assertEqual(engine.process_line('Prick the paper with a pin.'), 'Prick the paper with a pin.')
        self.assertEqual(engine.process_line('He got kicked in the bollocks.'), 'He got kicked in the bollocks.')
        from cleaner import mild_crude_list
        mild = RuleEngine(mild_crude_list)
        self.assertEqual(mild.process_line('Take a piss.'), 'Use the toilet.')
        self.assertEqual(mild.process_line("I'm pissed off."), "I'm angry.")
        self.assertEqual(mild.process_line("She's mighty pissed about it, too."), "She's mighty angry about it, too.")
        self.assertEqual(mild.process_line("I'm pissed at him."), "I'm angry at him.")
        self.assertEqual(mild.process_line("Pissed me off further."), "Angered me further.")
        self.assertEqual(mild.process_line("filled with pissed-off narwhals"), "filled with angry narwhals")
        self.assertEqual(mild.process_line("a pissed off crowd"), "an angry crowd")
        self.assertEqual(mild.process_line("She was pissed."), "She was angry.")
        self.assertEqual(mild.process_line("He got pissed drunk."), "He got drunk.")
        self.assertEqual(mild.process_line("He was pissed as a newt."), "He was drunk.")
        self.assertEqual(mild.process_line("He was pissed out of his mind."), "He was drunk out of his mind.")
        self.assertEqual(mild.process_line('Piss off!'), 'Go away!')
        self.assertEqual(mild.process_line('He pissed off his friend.'), 'He annoyed his friend.')
        self.assertEqual(mild.process_line('horsepiss'), 'horse urine')
        self.assertEqual(mild.process_line('He pissed on the door.'), 'He urinated on the door.')
        self.assertEqual(mild.process_line('The dog pissed against a rock.'), 'The dog urinated against a rock.')
        self.assertEqual(mild.process_line('He pissed quick short at the wall.'), 'He urinated quickly at the wall.')
        self.assertEqual(mild.process_line('Piss on the wall!'), 'Urinate on the wall!')
        self.assertEqual(mild.process_line('Men\'s beery piss.'), "Men's beery urine.")
        self.assertEqual(mild.process_line('Pisspots'), 'Chamber pots')
        self.assertEqual(mild.process_line('Pisser Burke arrived.'), 'Pisser Burke arrived.')
        self.assertEqual(engine.process_line('Fecking matches.'), 'Darn matches.')
        self.assertEqual(engine.process_line('Scutter!'), 'Rubbish!')
        self.assertEqual(engine.process_line('That is ballocks.'), "That's nonsense.")
        self.assertEqual(engine.process_line("Who's the old ballocks?"), "Who's the old fool?")
        self.assertEqual(engine.process_line("I don't give a bugger who he is."), "I don't care who he is.")
        self.assertEqual(engine.process_line('The poxy bowsy left them off.'), 'The wretched bowsy left them off.')
        self.assertEqual(engine.process_line('Arse!'), 'Rear!')
        self.assertEqual(engine.process_line('flabbyarse of a wife'), 'flabby rear of a wife')
        self.assertEqual(engine.process_line('An arse.'), 'A fool.')
        self.assertEqual(engine.process_line('He fell on his arse.'), 'He fell on his rear.')

        # Clean donkey mode must not turn arse into a donkey; the British
        # language rules still soften its vulgar meaning.
        from cleaner import language_check
        clean_mode = RuleEngine(language_check(
            'sample', replace_crude=False, replace_british=True,
            replace_ass=True, ass_override='clean',
        ))
        self.assertEqual(clean_mode.process_line('The arse hurt.'), 'The rear hurt.')
        self.assertEqual(clean_mode.process_line('The ass brayed.'), 'The donkey brayed.')

    def test_dual_meaning_context_protections(self):
        """Legitimate genteel contexts (birds, food) are protected from false positives."""
        from cleaner import RuleEngine, re_list
        engine = RuleEngine(re_list)

        # Avian references must not become 'belly'
        bird_cases = [
            ("A blue tit landed on the fence.", "A blue tit landed on the fence."),
            ("We observed a great tit in the garden.", "We observed a great tit in the garden."),
            ("The marsh tit has distinctive feathers.", "The marsh tit has distinctive feathers."),
            ("A coal tit and a willow tit flew together.", "A coal tit and a willow tit flew together."),
            ("The tufted titmouse was feeding.", "The tufted titmouse was feeding."),
            ("That is a juicy titbit of gossip.", "That is a juicy titbit of gossip."),
            ("This is tit for tat.", "This is tit for tat."),
        ]
        for original, expected in bird_cases:
            self.assertEqual(engine.process_line(original), expected)

        # Vulgar anatomical 'tits' must still be replaced
        self.assertEqual(engine.process_line("Stop staring at her tits."), "Stop staring at her belly.")
        self.assertEqual(engine.process_line("She showed her tit to him."), "She showed her belly to him.")

        # British dessert 'spotted dick' must not become 'spotted toe'
        self.assertEqual(engine.process_line("We had spotted dick for dessert."), "We had spotted dick for dessert.")
        # Standalone vulgar 'dick' is still replaced
        self.assertEqual(engine.process_line("He was being a dick."), "He was being a toe.")
        # A body-part reference is not rewritten as an insult.
        self.assertEqual(engine.process_line("He got kicked in the cunt."), "He got kicked in the crotch.")
        self.assertEqual(engine.process_line("the grey sunken cunt of the world"), "the grey sunken crotch of the world")

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

class TestGolden(unittest.TestCase):
    def test_pg4300_golden(self):
        self.maxDiff = None
        import cleaner
        original_file = 'pg4300-images.html'
        golden_diff_file = 'pg4300-images.golden.diff'

        if not os.path.exists(original_file):
            self.skipTest(f"{original_file} not found")
        if not os.path.exists(golden_diff_file):
            self.skipTest(f"{golden_diff_file} not found")

        with open(original_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # The original file has CRLF. Let's normalize it to LF for comparison.
        original_lines = original_content.replace('\r\n', '\n').splitlines(keepends=True)

        cleaned_content = cleaner.clean_text(original_content)
        cleaned_lines = cleaned_content.splitlines(keepends=True)

        # Generate the unified diff
        diff = difflib.unified_diff(
            original_lines,
            cleaned_lines,
            fromfile=original_file,
            tofile='pg4300-images-cleaned.html',
            lineterm='\n'
        )
        actual_diff = "".join(diff)

        with open(golden_diff_file, 'r', encoding='utf-8') as f:
            expected_diff = f.read()

        if actual_diff != expected_diff:
            # If the diffs are different, show the diff of the diffs
            diff_of_diffs = "".join(difflib.unified_diff(
                expected_diff.splitlines(keepends=True),
                actual_diff.splitlines(keepends=True),
                fromfile='expected_diff',
                tofile='actual_diff',
                lineterm='\n'
            ))
            self.fail(f"Golden diff mismatch!\n\nDiff of diffs:\n{diff_of_diffs}")
if __name__ == '__main__':
    unittest.main()
