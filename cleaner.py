#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
import os
import sys
import re


def keep_case(sub, matchobj):
    ''' Substitute requested word matching case of matched word '''
    val = matchobj.group(0)
    up_count = 0
    if val.isupper():
        sub = sub.upper()
    else:
        # Test first two to see if all uppercase
        for ii in range(min(2, len(sub), len(val))):
            if val[ii].isupper():
                up_count += 1
                sub = sub[:ii] + sub[ii].upper() + sub[ii+1:]
        # Allow further uppercase only if all uppercase
        for ii in range(min(len(sub), len(val))):
            if up_count > 1:
                up_count += 1
                sub = sub[:ii] + sub[ii].upper() + sub[ii+1:]
    return sub


def first_case(sub, matchobj):
    ''' Keep the case of the first lettter '''
    val = matchobj.group(0)
    if val.isupper():
        sub = sub.upper()
    else:
        try:
            for ii in range(1):
                if val[ii].isupper():
                    sub = sub[:ii] + sub[ii].upper() + sub[ii+1:]
        except:
            print("*"*60, "sub=", sub, "val=", val, "*"*60)
    return sub


def drop_first_match(sub, matchobj):
    ''' Drop first match, match case of first and return second '''
    drop = matchobj.group(1)
    val = matchobj.group(2)
    try:
        for ii in range(len(drop)):  # find first alpha in drop
            if drop[ii].isalpha():
                if drop[ii].isupper():  # uppercase, so copy to val
                    for jj in range(len(val)):  # find first alpha in val
                        if val[jj].isalpha():
                            val = val[:jj] + val[jj].upper() + val[jj+1:]
                            break
                break
    except:
        print("*"*50, "error in drop_first_match")
        print(drop)
        print(val)
        print(str(sub))
        print(str(matchobj.groups()))
    return val


# Prepare two lists for different meanings of ass
dirty_a_list = [
    #########################################
    # dirtier ass
    #########################################
    # haul ass
    (re.compile(r'\b(move|haul)\Wass\b', re.I), "move fast", keep_case),
    # little ass
    (re.compile(r'little\W?ass\b', re.I), "little donkey", keep_case),
    (re.compile(r'little\W?asses\b', re.I), "little donkeys", keep_case),
    #your/own/etc. ass
    (re.compile(r'(?<=(.your|..own|...my|..our|..her|..his|.this|.that|..the|their|those|these|..its|..for)\W)ass\b', re.I), "rear", keep_case),
    (re.compile(r'(?<=(.your|..own|...my|..our|..her|..his|.this|.that|..the|their|those|these|..its|..for)\W)asses\b', re.I), "rears", keep_case),
    # asses
    (re.compile(r'\basses\b', re.I), "rears", keep_case),
    # ass
    (re.compile(r'\ban\Wass\b', re.I), "a jerk", keep_case),
    (re.compile(r'\bass\b', re.I), "rear", keep_case),
]

clean_a_list = [
    #########################################
    # cleaner ass
    #########################################
    # haul ass
    (re.compile(r'\bhaul\Wass\b', re.I), "move fast", keep_case),
    # asses
    (re.compile(r'\basses\b', re.I), "donkeys", keep_case),
    # ass
    (re.compile(r'\ban Ass\b'), "a Donkey", False),  # C.S. Lewis
    (re.compile(r'\ban\Wass\b', re.I), "a donkey", keep_case),
    (re.compile(r'(?<!in\W)\bass\b', re.I), "donkey", keep_case),
]

s_lord = '(god|jesus(\W?christ)?|christ)'
lord_list = [
    # Thank God
    (re.compile(r'thank( you\,?)? '+s_lord+r'\b', re.I), "thank goodness", first_case),
    # My God
    (re.compile(r'(?<!(..\bin|..\bis|..\bto|..\bof|from|..\bon)\W)my ' + \
                s_lord+r's?\b(?! \w)', re.I), "my goodness", first_case),
    # Oh God
    (re.compile(r'\boh\,? '+s_lord+r'\b', re.I), "oh goodness", first_case),
    # Good God
    (re.compile(r'\bgood '+s_lord+r'\b', re.I), "goodness", first_case),
    # name of God
    (re.compile(r'\bname of '+s_lord+r'\b', re.I), "world", first_case),
    # In God's name
    (re.compile(r'(?<=where\W)\bin\W'+s_lord + \
                '\W*s name', re.U+re.I), "in the world", first_case),
    (re.compile(r'\bin '+s_lord+'\W*s name', re.U+re.I),
        "for goodness sake", first_case),
    # in God
    (re.compile(r'\bin '+s_lord+r'\b', re.I), "in the lord", first_case),
    # of God
    #(re.compile(r'(?<!(.church|society|...time) )of '+s_lord+r'\b',re.I),"of heaven",first_case),
    # to God
    (re.compile(r'\bto '+s_lord+r'\b', re.I), "to heaven", first_case),
    # by God
    (re.compile(r'\bby '+s_lord+r'\b', re.I), "by the heavens", first_case),
    # God knows (start of sentence, not start of sentence)
    (re.compile(r'([^ ]|\. +)'+s_lord+' knows', re.I),
     r"\1Heaven knows", False),
    (re.compile(r''+s_lord+' knows', re.I), "heaven knows", False),
    # For God's sake
    (re.compile(r'\bfor '+s_lord+'\W*s sake', re.U+re.I),
        "for goodness sake", first_case),
    # Godforsaken
    (re.compile(r'\b'+s_lord+'.?forsaken\b', re.I), "forsaken", keep_case),
    # Godawful
    (re.compile(r'\b'+s_lord+'.?awful\b', re.I), "forsaken", keep_case),
]

# Use if this book is likely to take Lord's name in vain
vain_lord_list = [
    (re.compile(r'thanked '+s_lord+r'\b', re.I), "thanked heaven", first_case),
    (re.compile(r'(?<=([\.?!,]\W\W|..\"|..”|..“|.\W\W))'+s_lord +
                's?(?=[\.,?!])', re.U+re.I), "goodness", keep_case),
    # Jesus and/or Christ
    (re.compile(r'(?<!of )\bjesus(\W?(christ|almighty))?', re.I), "goodness", first_case),
    (re.compile(r'(?<!of )(?<!jesus )christ\b', re.I), "goodness", keep_case),
    # God
    #(re.compile(r'(?<![Oo][Ff] )\bG[Oo][Dd]\b(?! ([Bb][Ll][Ee][Ss][Ss]|[Ss][Aa][Vv][Ee]))'),"goodness",keep_case),
]


# 3 element list: [search phrase, replace value, preserve case function]
re_list = [
    #########################################
    # Random stuff
    #########################################
    # Remove suggestive 'tits' with not suggestive belly
    # don't do 'tit for tat', tit-tat-toe, or split tit-ular
    (re.compile(r'\b[tT][iI][tT][sS]?\b(?! for)(?!-tat)(?!-ul)',
                re.I), 'belly', keep_case),
    # Slut is rude, replace with slightly better hussy
    (re.compile(r'\bslut\b', re.I), 'hussy', keep_case),
    (re.compile(r'\bsluts\b', re.I), 'hussies', keep_case),
    # Change topless bar to just bar
    (re.compile(r'topless\Wbar', re.I), 'bar', keep_case),
    # Replace whore with woman (not always a good replacement)
    # (re.compile(r'\bwhore\b',re.I),'woman',keep_case),
    # (re.compile(r'\bwhores\b',re.I),'women',keep_case),
    # Whorehouse becomes brothel
    (re.compile(r'whorehouse', re.I), 'brothel', keep_case),
    # Crap and crapper to 'use the toilet'
    (re.compile(r'take\Wa\Wcrap(per)?', re.I), 'use the toilet', keep_case),
    (re.compile(r'\bcrapper', re.I), 'toilet', keep_case),
    # Crap and crapper to garbage
    (re.compile(r'\bcrap\b', re.I), 'garbage', keep_case),
    (re.compile(r'\bcrapped\b', re.I), 'wet', keep_case),
    # Cock-up with mess-up
    (re.compile(r'\bcock.?up\b', re.I), "mess up", keep_case),
    # Cocksucker with sucker
    (re.compile(r'\bcock.?(?=suc)', re.I), "", False),
    # Cocker with idiot (but not cocker spaniel
    (re.compile(r'\bcocker\b(?![ -]spani)', re.I), "idiot", keep_case),
    # Cunt
    (re.compile(r'\bcunt\b', re.I), 'groin', keep_case),
    # Replace goddammit and dammit with 'dang it'
    (re.compile(r'([^\.?!] *) Goddam([mn])', re.I), r'\1 goddam\2', False),
    (re.compile(r'(?:gods?)?dammit', re.I), 'dang it', keep_case),
    #########################################
    # Replace ass and its varieties (see specific lists above, dirty_a_list and clean_a_list)
    #########################################
    # smart ass
    (re.compile(r'smart\W?ass\b', re.I), "smart aleck", keep_case),
    (re.compile(r'smart\W?asses\b', re.I), "smart alecks", keep_case),
    # kiss ass
    (re.compile(r'kissin[^\s]\Wass(es)?\b',
                re.U+re.I), "kissing up", keep_case),
    (re.compile(r'kiss.{1,6}ass(es)?\b', re.I), "fly a kite", keep_case),
    # kick ass
    (re.compile(r'kick\W?ass\b', re.I), "kick booty", keep_case),
    (re.compile(r'kick\W?asses\b', re.I), "kick booties", keep_case),
    # cover ... ass
    (re.compile(r'(cover.{0,8} )ass\b', re.I), r"\1rear", False),
    (re.compile(r'(cover.{0,8} )asses\b', re.I), r"\1rears", False),
    # kick ... ass
    (re.compile(r'(kick.{0,8} )ass\b', re.I), r"\1rear", False),
    (re.compile(r'(kick.{0,8} )ass\b', re.I), r"\1rears", False),
    # assed
    (re.compile(r'\bassed\b', re.I), "ended", keep_case),
    # jack/dumbass
    (re.compile(r'(?<=bray like a )(jack|dumb)ass\b', re.I), "donkey", keep_case),
    (re.compile(r'(jack|dumb)ass\b', re.I), "jerk", keep_case),
    (re.compile(r'(jack|dumb)asses\b', re.I), "jerks", keep_case),
    # asshole
    (re.compile(r'an\Wasshole', re.I), "a jerk", keep_case),
    (re.compile(r'asshole', re.I), "jerk", keep_case),
    # horse's ass
    (re.compile(r'horse[^\s]?s ?ass\b', re.U+re.I), "jerk", keep_case),
    (re.compile(r'horse[^\s]?s ?asses\b', re.U+re.I), "jerks", keep_case),
    #########################################
    # Replace damn and its varieties
    #########################################
    # I'll be damned
    (re.compile(r'be(\W+)(?:gods? *)?damned', re.I), r'be\1darned', False),
    # Give a damn
    (re.compile(r'give(\W+.{0,10}?)a(\W+)(?:gods? *)?damn',
                re.I), 'care', keep_case),
    (re.compile(
        r'gives(\W+.{0,10}?)a(\W+)(?:gods? *)?damn', re.I), 'cares', keep_case),
    # Damn near
    (re.compile(r'(?:gods? *)?damn(\W+)near', re.I), 'nearly', keep_case),
    # a damn. Worth a damn -> worth a cent (couldn't think of a better word)
    (re.compile(r'((matters?|worth|of)\W+a\W+)(?:gods? *)?damn\b', re.I), r'\1cent', False),
    # of the damned
    (re.compile(r'(of\W*the\W*)(?:gods? *)?damned\b', re.I), r'\1cursed', False),
    # Your damned word, a damn word, etc
    (re.compile(r'(your|our|her|his|this|that|the|their|hose|these|for|so|some|one|one more|too)( +)(?:gods? *)?damn(?:ed)?\b(?!-)', re.I), r'\1', False),
    # a damn
    (re.compile(r'(?<=\b[aA] )(?:gods? *)?damn(?:ed)',
                re.I), 'darn', keep_case),
    # damned good, damn sure, etc (Clancy's favorites)
    (re.compile(r'\b((?:gods? *)?damn(?:ed))(?:\W+)(sure|near|sight|good|much|hard|easy|big|little|glad|clever|mess|smart|fine|fool|right|thing|much|shame|nice|mean|bad|lucky|late|important)', re.I), '', drop_first_match),
    (re.compile(r'\b((?:gods? *)?damn(?:ed))(?:\W+)well', re.I), 'darn well', keep_case),
    # Religious damning
    (re.compile(r'\b(?:gods? *)?damned', re.I), 'cursed', keep_case),
    (re.compile(r'\b(?:gods? *)?damndest', re.I), 'very best', keep_case),
    (re.compile(r'\b(?:gods? *)?damning', re.I), 'condemning', keep_case),
    (re.compile(r'\b(?:gods? *)?damnable', re.I), 'condemning', keep_case),
    (re.compile(r'\b(?:gods? *)?damnably', re.I), 'cursedly', keep_case),
    (re.compile(r'\b(?:gods? *)?damnatory', re.I), 'condemning', keep_case),
    (re.compile(r'\b(?:gods? *)?damnation', re.I), 'condemnation', keep_case),
    # damn it
    (re.compile(r', (?:gods? *)?damn it(?: all)?', re.I), '', keep_case),
    (re.compile(r'((?:gods? *)?damn it(?: all)?, +)(.)', re.I), '', drop_first_match),
    # a damn something, like "a damn nuisance"
    (re.compile(r'\ba(\W+)(?:gods? *)?damn', re.I), r'a\1blasted', False),
    # damn you/his/her/etc
    (re.compile(r'\b(?:gods? *)?damn you to hell', re.I), 'curse you', keep_case),
    (re.compile(r'\b(?:gods? *)?damn(?= (him|his|her|you|next|the|you))', re.I),
        'curse', keep_case),
    # Word by itself
    (re.compile(r'\b(?:gods? *)?damn\b', re.I), 'dang', keep_case),
    # Final catch-all
    (re.compile(r'(?:gods? *)?damn', re.I), 'dang', keep_case),
    #########################################
    # Bitch
    #########################################
    # Son of a bitch
    (re.compile(r's[UuOo]n(s)?([ -])?[OoUu][FfVv]([ -])?(a)?([ -])?bitch(e)?',
                re.I), 'jerk', keep_case),
    # verb
    (re.compile(r'bitchin[^\s]', re.U+re.I), 'complaining', keep_case),
    (re.compile(r'bitched', re.I), 'complained', keep_case),
    (re.compile(r'bitche?(?=s? abo)', re.I), 'complain', keep_case),
    (re.compile(r'(?<=(n([^\s]|o)t ))bitch',
                re.U+re.I), 'complain', keep_case),
    # A bitch
    (re.compile(r's a bitch', re.I), 's tough', keep_case),
    # Bitch by itself
    (re.compile(r'\bbitch(e)?', re.I), 'jerk', keep_case),
    #########################################
    # Shit
    #########################################
    # bullshit
    (re.compile(r'\b(bull|horse|dog|jack)(.)?shit', re.I), 'shit', keep_case),
    # Holy shit
    (re.compile(r'\bholy\W*shit', re.I), 'incredible', keep_case),
    # exclamantion
    (re.compile(r'(?<=oh, )shit\b', re.I), 'shoot', keep_case),
    (re.compile(r'(?<=oh )shit\b', re.I), 'shoot', keep_case),
    (re.compile(r'(?<!\w )shit!', re.I), 'shoot!', keep_case),
    (re.compile(r'(?<=--)shit', re.I), 'shoot', keep_case),
    # no shit
    (re.compile(r'(?<=no\W)shit\b', re.I), 'kidding', keep_case),
    # know shit
    (re.compile(r'(?<=know\W)shit\b', re.I), 'squat', keep_case),
    #shit-load, head, can, hole, pot
    (re.compile(r'shit(.)?load', re.I), 'load', keep_case),
    (re.compile(r'shit(.)?can', re.I), 'trash', keep_case),
    (re.compile(r'shit(.)?pot', re.I), 'toilet', keep_case),
    (re.compile(r'shit(.)?head', re.I), 'idiot', keep_case),
    (re.compile(r'shit(.)?hole', re.I), 'pile of trash', keep_case),
    # verb shittin'
    (re.compile(r'shittin(?=[^\s])?', re.U+re.I), 'kiddin', keep_case),
    # shitter
    (re.compile(r'shitter', re.I), 'toilet', keep_case),
    # shitty
    (re.compile(r'shitty', re.I), 'nasty', keep_case),
    # shit-filled
    (re.compile(r'\Wshit(.)?fill(ed)?', re.I), '', keep_case),
    # shit
    (re.compile(r'(?<=ive a )shit', re.I), 'hoot', keep_case),
    (re.compile(r'(?<=got )shit', re.I), 'nothing', keep_case),
    (re.compile(r'(?<=\w )shit', re.I), 'trash', keep_case),
    (re.compile(r'[S]hit(?=[,\.!?])', re.I), 'incredible', keep_case),
    (re.compile(r'\bshit\b', re.I), 'rubbish', keep_case),
    #########################################
    # f-bomb
    #########################################
    # clean up script...
    (re.compile(r'(m[OoUu]th[AaEe]r?)?fuck', re.I), 'zxsa', keep_case),
    # clean up script...
    (re.compile(r'(m[OoUu]th[AaEe]r?)?fook', re.I), 'zxsa', keep_case),
    # f yourself
    (re.compile(r'zxsa[\W]?yourself', re.I), "kill yourself", first_case),
    # cluster f
    (re.compile(r'cluster[\W]?zxsa', re.I), "massive failure", first_case),
    # f your
    (re.compile(r'zxsa[\W]?your', re.I), "bother your", first_case),
    # f you
    (re.compile(r'(?<!the[\W])zxsa[\W]?you', re.I), "forget you", first_case),
    # the f
    (re.compile(r'(?<=the[\W])zxsa\b', re.I), "heck", keep_case),
    # you f up/with
    (re.compile(r'(?<=you[\W])zxsa(?=[\W][UuWw])', re.I), "mess", first_case),
    # f's
    (re.compile(r'zxsas(?=\W(around|with|on\b|up\b|over|under|through))',
                re.U+re.I), "messes", first_case),
    # f'in
    (re.compile(r'zxsa(?=(in[^\s]?|s)?\W(around|with|on\b|up\b|over|under|through))',
                re.U+re.I), "mess", first_case),
    # f'ing A
    (re.compile(r'zxsain[^\s]? a\b', re.U+re.I), "unbelievable", first_case),
    (re.compile(r' (zxsain[^\s]?(?: well)?)(\W*.)',
                re.U+re.I), "", drop_first_match),
    (re.compile(r'(zxsain[^\s]? (?:well)?)(\W*.)',
                re.U+re.I), "", drop_first_match),
    (re.compile(r'zxsain[^\s]?', re.U+re.I), "frigging", keep_case),
    # f'er
    (re.compile(r'zxsaer', re.I), "idiot", keep_case),
    # f'it
    (re.compile(r'zxsa\W?it', re.I), "phoo", keep_case),
    # f your/his/her/etc
    (re.compile(
        r'zxsa(?=(ed)?\W(your|our|her|his|us|this|that|the\b|their|those|these|them|[^\s]em|for|a\b))', re.U+re.I), "harass", keep_case),
    # f'ed
    (re.compile(r'zxsaed', re.I), "messed", keep_case),
    # f the
    (re.compile(r'zxsa(?=[\W]the)', re.I), "forget", keep_case),
    # verb
    (re.compile(r'zxsa(?=\W(around|with|on\b|up\b|over|under|through))', re.I),
        "mess", first_case),
    (re.compile(r'(?<=to\W)zxsa', re.I), "mess", first_case),
    # f, f ups
    (re.compile(r'zxsa(\W?up)?', re.I), "idiot", keep_case),
    #########################################
    # dick
    #########################################
    # dick around
    (re.compile(r'dick(?=(in[^\s])?\W(around|with|on\b|up\b|over|under|through))',
                re.U+re.I), "mess", first_case),
    # dickin['/g]
    (re.compile(r'dick(?=(in[^\s][^o]))', re.U+re.I), "mess", keep_case),
    #dickweed, dickhead
    (re.compile(r'dick[WwHh]e[AaEe]d', re.I), "jerk", keep_case),
    # know dick
    (re.compile(r'(?<=[Kk]now )dick'), "squat", keep_case),
    # dick on its own (toe is just sort of random...), not bird dickcissel
    (re.compile(r'\bdick\b(?!-ciss)'), "toe", keep_case),
    #########################################
    # bastard
    #########################################
    (re.compile(r'\bbastard', re.I), "mongrel", keep_case),
    #########################################
    # hell
    #########################################
    # hellhound
    (re.compile(r'\bhell\W?hound', re.I), 'demonhound', keep_case),
    # hell-word (not helldiver bird)
    (re.compile(r'\bhell(?=-[^oO])(?!-diver)', re.I), 'demon', keep_case),
    # hell's bells
    (re.compile(r'\bhell.{0,4}s?\W?bells?', re.I), 'by golly', keep_case),
    # hell with
    (re.compile(r'(to|the)\Whell\Wwith', re.I), 'forget', keep_case),
    (re.compile(r'\bhell(?=\Wwith)', re.I), 'heck', keep_case),
    # beats the hell out of
    (re.compile(r'beats\Wthe\Whell\Wout\Wof', re.I), 'beats', keep_case),
    # to hell
    (re.compile(r'(?<=\bto\W)hell\b', re.I), 'perdition', keep_case),
    # some hell
    (re.compile(r'(?<=some\W)hell\b', re.I), 'trouble', keep_case),
    # give/gave hell
    (re.compile(r'(g[IiAa]ve.{0,7}\W)hell\b(?!\Wof)',
                re.I), r'\1trouble', False),
    # raise/raising hell
    (re.compile(r'(rais[IiEe].{0,10}\W)hell\b', re.I), r'\1trouble', False),
    #chance in hell
    (re.compile(r'(?<=chance)( in) hell\b(\W*.)', re.I), '*removed*', drop_first_match),
    #burn in hell
    (re.compile(r'(?<=burn)( in) hell\b(\W*.)', re.I), '*removed*', drop_first_match),
    # living hell
    (re.compile(r'(?<=living\W)hell\b', re.I), 'prison', keep_case),
    # for/etc the hell
    (re.compile(r'(?<=(..for)\Wthe\W)hell\b', re.I), 'heck', keep_case),
    # what the hell[.?!]
    (re.compile(r'what\Wthe\Whell(?=[\.?!\,])',
                re.I), 'what the heck', keep_case),
    # (in) the hell
    (re.compile(
        r'(?: in)? (the)\Whell(?=[ \.?!\,])(?! in)(?! your)(?! out)(?! I\b)(?! of\b)(\W*.)', re.I), '*removed*', drop_first_match),
    (re.compile(r'(?:in\W)?(the)\W+hell (?!in)(?!your)(?!out)(?!I\b)(?!of\b)(\W*.)',
                re.I), '*removed*', drop_first_match),
    #(re.compile(r'(?:\Win)?\W(the)\Whell\b(?=[ \.?!\,])(?! in)(\W*.)',re.I),'*removed*',drop_first_match),
    # what/how/whatever/etc the hell
    (re.compile(r'(?<=(..how|..for|where|.what|tever|..who)\Wthe\W)hell\b',
                re.I), 'heck', keep_case),
    # sure/busy/etc. as hell
    (re.compile(r'(?<!known)( as) hell\b(\W*.)', re.I), '', drop_first_match),
    # helluva
    (re.compile(r'\bhelluva', re.I), 'heck of a', keep_case),
    #way in hell
    (re.compile(r'(?<=way) (in) hell\b(\W*.)', re.I), '', drop_first_match),
    #what in hell
    (re.compile(r'(?<=what) (in) hell\b(\W*.)', re.I), '', drop_first_match),
    # but hell
    (re.compile(r'(?<=but )hell\b', re.I), 'heck', keep_case),
    # to be hell
    (re.compile(r'(?<=to be )hell\b', re.I), 'terrible', keep_case),
    # is/it's hell
    (re.compile(r'(?<=is )hell\b', re.I), 'perdition', keep_case),
    (re.compile(r'(?<=it[^\s]s )hell\b', re.U+re.I), 'perdition', keep_case),
    #Aw, hell
    (re.compile(r'(?<=Aw, )hell\b', re.I), 'heck', keep_case),
    # catch hell
    (re.compile(r'catch hell\b', re.I), 'get in trouble', keep_case),
    (re.compile(r'caught hell\b', re.I), 'got in trouble', keep_case),
    # as hell
    (re.compile(r'sure as hell[ \,]', re.I), 'for sure', keep_case),
    (re.compile(r'ed as hell\b', re.I), 'ed as could be', keep_case),
    (re.compile(r'\bas hell[ \,]', re.I), 'as could be', keep_case),
    # of hell
    (re.compile(r'\bof hell\b', re.I), 'of torture', keep_case),
    # all hell
    (re.compile(r'\ball hell\b', re.I), 'all perdition', keep_case),
    # hell was
    (re.compile(r'\bhell(?= was)', re.I), 'heck', keep_case),
    # hell to pay
    (re.compile(r'\bhell(?= to pay)', re.I), 'heck', keep_case),
    # bloody hell
    (re.compile(r'(?<=bloody.)hell\b', re.I), 'heck', keep_case),
    # dang hell
    (re.compile(r'(?<=dang.)hell\b', re.I), 'heck', keep_case),
    # like hell
    (re.compile(r'(?<=(..look|looked|..hurt) )like hell\b', re.I), 'really bad', keep_case),
    (re.compile(r'(?<=felt )like hell\b', re.I), 'like garbage', keep_case),
    (re.compile(r'L[Ii][Kk][Ee]\W[Hh][Ee][Ll][Ll]'),
     'not a chance', keep_case),
    (re.compile(r'l[Ii][Kk][Ee]\W[Hh][Ee][Ll][Ll]'), 'like mad', keep_case),
    # The hell I
    (re.compile(r'the\Whell\WI\b', re.I), 'the heck I', keep_case),
    # hell of/out/off ...
    (re.compile(r'\bhell(?=\W(of\W|out|off\b|do\W|are\b))', re.I), 'heck', keep_case),
    # hellish
    (re.compile(r'\bhellish', re.I), 'unpleasant', keep_case),
    # this/real hell (not followed by ?)
    (re.compile(r'(?<=(this|real)\W)hell(\W?hole|\W?pit)?(?!\?)', re.I), 'pit', keep_case),
    # hell's
    (re.compile(r'\bhell[^\s]s', re.U+re.I), 'perditions\'s', keep_case),
    # interjection hell (preceeded by . or " or --, etc, followed by ,
    (re.compile(r'(?<=([\.?!,]\W\W|..\"|..”|..“|.\W\W))hell(?=[,!])',
                re.U+re.I), 'heck', keep_case),
    # >hell< shows up in html with italics or emphasis
    (re.compile(r'\>hell\<', re.U+re.I), '>perdition<', keep_case),
]
#+ ass_list + lord_list

DEBUG = True


def language_check(text):
    ret_val = re_list + lord_list
    # Determine if this book is likely to take Lord's name in vain
    if re.search("(for Christ's sake!|Holy Christ!|Holy Jesus!|for God's sake!|God almighty!|goddamn|fuck)", text, re.I):
        if DEBUG:
            print("Looks like book uses Lord's name in vain")
        ret_val += vain_lord_list
    else:
        if DEBUG:
            print("Looks like book does not use Lord's name in vain")
    # Ass has two very different contexts. Guess which to use.
    if re.search("(dumbass|asshole|smart ass|kick ass|ass kick|ass handed|badass|cover.{0,5}ass)", text):
        ret_val += dirty_a_list
        if DEBUG:
            print("Looks like book does not need the donkey treatment")
    else:
        ret_val += clean_a_list
        if DEBUG:
            print("Looks like book calls donkeys asses")
    # open('/tmp/dump.txt','w').write(text)
    return ret_val


'''
from functools import partial
import codecs
text = codecs.open('bad.txt', encoding='utf-8').read()

#if DEBUG:
#    print(text)
#    print("-"*40)
#    print("-"*40)

output = ""
replacement_list = language_check(text)

output = ""
for line in text.split("\n"):
    #Go through all elements of replacement_list
    for search,sub,pcase in replacement_list:
        if pcase: # Preserve case
            line = search.sub(partial(pcase,sub),line)
        else: # Don't preserve case
            line = search.sub(sub,line)
    output += line + "\n"

#if DEBUG:
#    print(output)

codecs.open('clensed.txt','w', encoding='utf-8').write(output)
'''
