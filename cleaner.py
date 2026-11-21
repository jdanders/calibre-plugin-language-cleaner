#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
import os
import sys
import re
from functools import partial


def keep_case(sub, matchobj, group=0):
    ''' Substitute requested word matching case of matched word '''
    val = matchobj.group(group)
    if val.isupper():
        return sub.upper()

    sub_list = list(sub)
    up_count = 0
    # Test first two to see if all uppercase
    for ii in range(min(2, len(sub), len(val))):
        if val[ii].isupper():
            up_count += 1
            sub_list[ii] = sub_list[ii].upper()

    # Allow further uppercase only if all uppercase (matched at least first two)
    if up_count > 1:
        for ii in range(min(len(sub), len(val))):
            sub_list[ii] = sub_list[ii].upper()

    return "".join(sub_list)


def first_case(sub, matchobj, group=0):
    ''' Keep the case of the first lettter '''
    val = matchobj.group(group)
    if val.isupper():
        return sub.upper()

    if val and val[0].isupper() and sub:
        return sub[0].upper() + sub[1:]
    return sub


def remove_bloody_intensifier(matchobj):
    """Remove standalone intensifier 'bloody', preserving clear blood uses."""
    next_word = matchobj.group('next_word')
    if next_word and next_word.lower() in {
        'battle', 'bones', 'bridge', 'blood', 'face', 'hands', 'nose',
        'shirt', 'skulls', 'wound', 'wounds',
    }:
        return matchobj.group(0)
    if not next_word:
        return ''
    prefix = matchobj.string[:matchobj.start()]
    if matchobj.group('bloody')[0].isupper() and re.search(r'(?:^|[.!?—]\s*)$', prefix):
        return next_word[0].upper() + next_word[1:]
    return next_word


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
    except Exception as e:
        sys.stderr.write("error in drop_first_match: %s\n" % e)
        sys.stderr.write("drop=%s val=%s sub=%s groups=%s\n" % (
            drop, val, sub, matchobj.groups()))
    return val


# ---------------------------------------------------------------------------
# Ass lists \u2014 two mutually exclusive interpretations
# ---------------------------------------------------------------------------

# Prepare two lists for different meanings of ass
dirty_a_list = [
    #########################################
    # dirtier ass
    #########################################
    # haul ass
    (re.compile(r'\b(move|haul|get|drag)\W(ass|arse)\b', re.I), "move fast", keep_case),
    # little ass
    (re.compile(r'little\W?(ass|arse)\b', re.I), "little donkey", keep_case),
    (re.compile(r'little\W?(ass|arse)es\b', re.I), "little donkeys", keep_case),
    #your/own/etc. ass
    (re.compile(r'(?<=(.your|..own|...my|..our|..her|..his|.this|.that|..the|their|those|these|..its|..for)\W)(ass|arse)\b', re.I), "rear", keep_case),
    (re.compile(r'(?<=(.your|..own|...my|..our|..her|..his|.this|.that|..the|their|those|these|..its|..for)\W)(ass|arse)es\b', re.I), "rears", keep_case),
    # asses
    (re.compile(r'\b(ass|arse)es\b', re.I), "rears", keep_case),
    # ass
    (re.compile(r'\ban\W(ass|arse)\b', re.I), "a jerk", keep_case),
    (re.compile(r'\b(ass|arse)\b', re.I), "rear", keep_case),
]

clean_a_list = [
    #########################################
    # cleaner ass
    #########################################
    # haul ass
    (re.compile(r'\b(move|haul|get|drag)\W(ass|arse)\b', re.I), "move fast", keep_case),
    # asses
    (re.compile(r'\basses\b', re.I), "donkeys", keep_case),
    # ass
    (re.compile(r'\ban Ass\b'), "a Donkey", False),  # C.S. Lewis
    (re.compile(r'\ban\Wass\b', re.I), "a donkey", keep_case),
    (re.compile(r'(?<!(in\W|..>))\bass\b', re.I), "donkey", keep_case),
]

# ---------------------------------------------------------------------------
# Religious lists
# ---------------------------------------------------------------------------

s_lord = r'(god|jesus(\W?christ)?|christ)'
lord_list = [
    # Thank God
    (re.compile(r'thank( you\,?)? '+s_lord+r'\b(?! of)', re.I), "thank goodness", first_case),
    # My God
    (re.compile(r'(?<!(..\bin|..\bis|..\bto|..\bof|from|..\bon)\W)my ' + \
                s_lord+r's?\b(?! \w)', re.I), "my goodness", first_case),
    # Oh God
    (re.compile(r'\boh\,?\W*'+s_lord+r'\b', re.I), "oh goodness", first_case),
    # Good God
    (re.compile(r'\bgood '+s_lord+r'\b', re.I), "goodness", first_case),
    # name of God
    (re.compile(r'\bname of '+s_lord+r'\b', re.I), "world", first_case),
    # In God's name
    (re.compile(r'\b(where|what|how|why|when)(\W+)(in\W' + s_lord + r'\W*s name)', re.U+re.I),
        lambda m: m.group(1) + m.group(2) + first_case("in the world", m, group=3), False),
    (re.compile(r'\bin\W'+s_lord+r'\W*s name', re.U+re.I),
        "for goodness sake", first_case),
    # in God
    (re.compile(r'\bin '+s_lord+r'\b', re.I), "in the lord", first_case),
    # of God
    #(re.compile(r'(?<!(.church|society|...time) )of '+s_lord+r'\b',re.I),"of heaven",first_case),
    # to God
    (re.compile(r'\bto '+s_lord+r'\b( [Hh]imself)?', re.I), "to heaven", first_case),
    # by God
    (re.compile(r'\bby '+s_lord+r'\b', re.I), "by the heavens", first_case),
    # God knows (start of sentence, not start of sentence)
    (re.compile(r'([^ ]|\. +)'+s_lord+r' knows', re.I),
     r"\1Heaven knows", False),
    (re.compile(r''+s_lord+r' knows', re.I), "heaven knows", False),
    # For God's sake
    (re.compile(r'\bfor '+s_lord+r'\W*s sake', re.U+re.I),
        "for goodness sake", first_case),
    # Godforsaken
    (re.compile(r'\b'+s_lord+r'.?forsaken\b', re.I), "forsaken", False),
    # Godawful
    (re.compile(r'\b'+s_lord+r'.?awful\b', re.I), "forsaken", keep_case),
]

# Use if this book is likely to take Lord's name in vain
vain_lord_list = [
    (re.compile(r'thanked '+s_lord+r'\b', re.I), "thanked heaven", first_case),
    (re.compile(r'(?<=(.\W\W))'+s_lord +
                r's?(?=[\.,?!])', re.U+re.I), "goodness", keep_case),
    (re.compile(r'(?<=(\"|"|"|\u2014|-))'+s_lord +
                r's?(?=[\.,?!])', re.U+re.I), "goodness", keep_case),
    # Jesus and/or Christ
    (re.compile(r'(?<!of )\bjesus(\W?(christ|almighty))?', re.I), "goodness", first_case),
    (re.compile(r'(?<!of )(?<!jesus )christ\b', re.I), "goodness", keep_case),
    # God
    #(re.compile(r'(?<![Oo][Ff] )\bG[Oo][Dd]\b(?! ([Bb][Ll][Ee][Ss][Ss]|[Ss][Aa][Vv][Ee]))'),"goodness",keep_case),
]

# Replaces every standalone "God" and "Christ" unconditionally.  Off by default.
god_replace_list = [
    (re.compile(r'\bChrist\b', re.I), "goodness", keep_case),
    (re.compile(r'\bG[oO][dD]\b'), "goodness", keep_case),
]

# ---------------------------------------------------------------------------
# Categorised sub-lists
#
# These split the original monolithic re_list into named groups so that
# config_widget.py can offer per-group (and per-word-family) checkboxes.
#
# IMPORTANT: slur_list + crude_list + damn_list + bitch_list + shit_list +
#            fbomb_list + hell_list  ==  re_list  (same order, no omissions).
# test_cleaner.py imports re_list directly and must continue to pass as-is.
# ---------------------------------------------------------------------------

# Racial / ethnic slurs \u2014 separate so users can control independently
slur_list = [
    # Preserve the noun in racialized compounds while removing the slur.
    (re.compile(r'\bniggerlips\b', re.I), 'lips', keep_case),
    (re.compile(r'\bnigger[ -]+lips\b', re.I), 'lips', keep_case),
    (re.compile(r'\bnigger[ -]+mouth\b', re.I), 'mouth', keep_case),
    (re.compile(r'\bnigger[ -]+straw\b', re.I), 'straw', keep_case),
    # Slurs used as people nouns become generic person/people terms.
    (re.compile(r"\bniggers['’]s\b", re.I), "people's", keep_case),
    (re.compile(r"\bniggers['’](?=\W|$)", re.I), "people's", keep_case),
    (re.compile(r"\bnigger['’]s\b", re.I), "person's", keep_case),
    (re.compile(r"\bnigger['’](?=\W|$)", re.I), "person's", keep_case),
    (re.compile(r'\bniggers\b', re.I), 'people', keep_case),
    (re.compile(r'\bnigger\b', re.I), 'person', keep_case),
    # Keep coon replacements constrained to clear human references.
    (re.compile(r'\bcolou?red coons\b', re.I), 'people', keep_case),
    (re.compile(r'\bcolour coon\b', re.I), 'person', keep_case),
    (re.compile(r'\bcolor coon\b', re.I), 'person', keep_case),
    (re.compile(r'\bcoon(?=\s+like\b)', re.I), 'person', keep_case),
    # Related anti-Jewish slurs; ordinary Jew/Jews/Jewish references are kept.
    (re.compile(r'\bthose jewies does\b', re.I), 'those people do', keep_case),
    (re.compile(r'\bdirty jew\b', re.I), 'dirty person', keep_case),
    (re.compile(r'\blittle jewy\b', re.I), 'little fellow', keep_case),
    (re.compile(r'\bjewies\b', re.I), 'people', keep_case),
    (re.compile(r'\bjewy\b', re.I), 'person', keep_case),
    (re.compile(r'\bjewjesuit\b', re.I), 'person', keep_case),
    (re.compile(r'\bjewman\b', re.I), 'man', keep_case),
    (re.compile(r'\bsheeny nachez\b', re.I), 'person', keep_case),
    (re.compile(r'\bsheenies\b', re.I), 'men', keep_case),
    (re.compile(r'\bsheeny\b', re.I), 'man', keep_case),
]

# Strong profanity. Person-directed uses get an insult replacement; any other
# standalone use is still replaced with the standard anatomical term.
strong_profanity_list = [
    (re.compile(r'\b(you|he|she|they|that)(\s+(?:are|is|was|were))?\s+(a\s+)?((?:absolute|miserable|stupid|horrible|complete)\s+)cunt\b', re.I), r'\1\2 \3\4jerk', False),
    (re.compile(r'\b(you|he|she|they|that)(\s+(?:are|is|was|were))?\s+(a\s+)?(?:(?:absolute|miserable|stupid|horrible|complete)\s+)?cunt\b', re.I), r'\1\2 \3jerk', False),
    (re.compile(r'\b(what\s+a\s+)((?:absolute|miserable|stupid|horrible|complete)\s+)?cunt\b', re.I), r'\1\2jerk', False),
    (re.compile(r'\b(called|calls|call)\s+(him|her|them)\s+(?:a\s+)?cunt\b', re.I), r'\1 \2 a jerk', False),
    (re.compile(r'\b(you|they)(\s+(?:are|were))?\s+((?:absolute|miserable|stupid|horrible|complete)\s+)cunts\b', re.I), r'\1\2 \3jerks', False),
    (re.compile(r'\b(you|they)(\s+(?:are|were))?\s+cunts\b', re.I), r'\1\2 jerks', False),
    (re.compile(r'\bwhat\s+a\s+bunch\s+of\s+cunts\b', re.I), 'what a bunch of jerks', keep_case),
    (re.compile(r'(^|[,!?]\s*)cunt\b(?=[,.!?])', re.I), r'\1jerk', False),
    (re.compile(r'\bcunty\b', re.I), 'obnoxious', keep_case),
    # No standalone use is exempt: replace anatomical and metaphorical uses too.
    (re.compile(r'\bcunts\b', re.I), 'crotches', keep_case),
    (re.compile(r'\bcunt\b', re.I), 'crotch', keep_case),
    (re.compile(r'\bcocksucker\b', re.I), 'jerk', keep_case),
    (re.compile(r'\bcocksuckers\b', re.I), 'jerks', keep_case),
]

# Crude insults that are not otherwise covered by ass or strong profanity.
crude_insult_list = [
    # Use the established broad substitute in both insult and lineage senses.
    (re.compile(r'\bbastards\b', re.I), 'mongrels', keep_case),
    (re.compile(r'\bbastard\b', re.I), 'mongrel', keep_case),
    # Restore the vulgar standalone use while protecting the dog breed.
    (re.compile(r'\bcocker\b(?![ -]spaniels?\b)', re.I), 'idiot', keep_case),
    (re.compile(r'\bdick(?:head|weed)\b', re.I), 'jerk', keep_case),
    (re.compile(r'\bdick(?:heads|weeds)\b', re.I), 'jerks', keep_case),
    (re.compile(r'\basswipe\b', re.I), 'jerk', keep_case),
    (re.compile(r'\basswipes\b', re.I), 'jerks', keep_case),
    (re.compile(r'\b(?:jackoff|jerkoff)\b', re.I), 'idiot', keep_case),
    (re.compile(r'\b(?:jackoffs|jerkoffs)\b', re.I), 'idiots', keep_case),
    (re.compile(r'\ban\W(?:ass|arse)hole\b', re.I), 'a jerk', keep_case),
    (re.compile(r'\b(?:ass|arse)hole\b', re.I), 'jerk', keep_case),
    (re.compile(r'\b(?:ass|arse)holes\b', re.I), 'jerks', keep_case),
    (re.compile(r'\bslut\b', re.I), 'trollop', keep_case),
    (re.compile(r'\bsluts\b', re.I), 'trollops', keep_case),
    (re.compile(r'\bwhores\b', re.I), 'prostitutes', keep_case),
    (re.compile(r'\bwhore\b', re.I), 'prostitute', keep_case),
]

# Mild bodily language and bathroom terms.
mild_crude_list = [
    (re.compile(r'take\Wa\Wcrap(per)?', re.I), 'use the toilet', keep_case),
    (re.compile(r'\bcrapper', re.I), 'toilet', keep_case),
    (re.compile(r'\bcrap\b', re.I), 'garbage', keep_case),
    (re.compile(r'\bcrapped\b', re.I), 'wet', keep_case),
    (re.compile(r'take\Wa\Wpiss\b', re.I), 'use the toilet', keep_case),
    (re.compile(r'\bpiss[\s-]+poor\b', re.I), 'very poor', keep_case),
    (re.compile(r'\bpiss(?:ing)?\s+(?:about|around)\b', re.I), 'messing around', keep_case),
    (re.compile(r'\bhorse[ -]?piss\b', re.I), 'horse urine', keep_case),
    (re.compile(r'\bpisspots\b', re.I), 'chamber pots', keep_case),
    (re.compile(r'\bpisspot\b', re.I), 'chamber pot', keep_case),
    (re.compile(r'\bhaving a piss\b', re.I), 'using the toilet', keep_case),
    (re.compile(r'\bpiss on\b', re.I), 'urinate on', keep_case),
    (re.compile(r'\bpissed on\b', re.I), 'urinated on', keep_case),
    (re.compile(r'\bpissed against\b', re.I), 'urinated against', keep_case),
    (re.compile(r'\bpissed quick short at\b', re.I), 'urinated quickly at', keep_case),
    (re.compile(r'\b(I|you|he|she|it|we|they)([’\'](?:m|s|re)|\s+(?:am|are|is|was|were))\s+pissed\s+off\b', re.I), r'\1\2 angry', False),
    (re.compile(r'\bpissed off\b(?=\s+(?:his|her|their|my|our|your)\b)', re.I), 'annoyed', keep_case),
    (re.compile(r'\bpiss\s+off(?=[,!.?]|$)', re.I), 'go away', keep_case),
    (re.compile(r'\bpissing\b', re.I), 'urinating', keep_case),
    (re.compile(r'\bpissed\b', re.I), 'drunk', keep_case),
    (re.compile(r'\bpiss\b', re.I), 'urine', keep_case),
]

# Sexual/anatomical references with explicit contextual protections.
sexual_anatomical_list = [
    (re.compile(r'\bscrotumtightening\b', re.I), 'gut-tightening', keep_case),
    (re.compile(r'\bwhoredom\b', re.I), 'prostitution', keep_case),
    # Avoid bird names, tit for tat, tit-tat-toe, titular, titmouse/titmice,
    # and titbit.
    (re.compile(r'(?<!\bblue )(?<!\bgreat )(?<!\bcoal )(?<!\bmarsh )(?<!\bcrested )(?<!\bwillow )(?<!\blong-tailed )(?<!\btufted )\b[tT][iI][tT][sS]?\b(?! for)(?!-tat)(?!-ul)(?!mouse)(?!mice)(?!bit)', re.I), 'belly', keep_case),
    (re.compile(r'dick(?=(in[^\s])?\W(around|with|on\b|up\b|over|under|through))', re.U+re.I), 'mess', first_case),
    (re.compile(r'dick(?=(in[^\s][^o]))', re.U+re.I), 'mess', keep_case),
    (re.compile(r'(?<=[Kk]now )dick'), 'squat', keep_case),
    (re.compile(r'(?<!spotted )\bdick\b(?!-ciss)'), 'toe', keep_case),
    (re.compile(r'topless\Wbar', re.I), 'bar', keep_case),
    (re.compile(r'\bwhorehouse\b', re.I), 'brothel', keep_case),
]

# British and Irish words, restricted to clear insult/idiom contexts. Prick is
# omitted because its ordinary verb use is common.
british_list = [
    # This clear compound is an anatomical insult, not an ordinary word ending
    # in "arse" (such as coarse or sparse).
    (re.compile(r'\bflabbyarse\b', re.I), 'flabby rear', keep_case),
    (re.compile(r'\b(?:move|haul|get|drag)\W+arse\b', re.I), 'move fast', keep_case),
    (re.compile(r'\ban\Warse\b', re.I), 'a fool', keep_case),
    (re.compile(r'\barses\b', re.I), 'rears', keep_case),
    (re.compile(r'\barse\b', re.I), 'rear', keep_case),
    (re.compile(r'\bwhat a\W+twat\b', re.I), 'what a fool', keep_case),
    (re.compile(r'\bwhat a bunch of\W+twats\b', re.I), 'what a bunch of fools', keep_case),
    (re.compile(r'\byou\W+(?:absolute\W+|daft\W+|stupid\W+)?twat\b', re.I), 'you fool', keep_case),
    (re.compile(r'\byou\W+(?:absolute\W+|daft\W+|stupid\W+)?twats\b', re.I), 'you fools', keep_case),
    (re.compile(r'\b(those|these)\W+twats\b', re.I), r'\1 fools', False),
    (re.compile(r'\bwanker\b', re.I), 'idiot', keep_case),
    (re.compile(r'\bwankers\b', re.I), 'idiots', keep_case),
    (re.compile(r'\btosser\b', re.I), 'fool', keep_case),
    (re.compile(r'\btossers\b', re.I), 'fools', keep_case),
    (re.compile(r'\b(?:talking|speaking)\W+b[oa]llocks\b', re.I), 'talking nonsense', keep_case),
    (re.compile(r'\bwhat a load of\W+b[oa]llocks\b', re.I), 'what a load of nonsense', keep_case),
    (re.compile(r'\bthat(?:\'s| is)\W+b[oa]llocks\b', re.I), "that's nonsense", keep_case),
    (re.compile(r'\bthe old b[oa]llocks\b', re.I), 'the old fool', keep_case),
    (re.compile(r'(?m)^\s*b[oa]llocks\s*[!.?]', re.I), 'nonsense', keep_case),
    (re.compile(r'\bbugger\s+off\b', re.I), 'go away', keep_case),
    (re.compile(r'\bbugger\s+it\b', re.I), 'forget it', keep_case),
    (re.compile(r'\bwhere the bugger is\b', re.I), 'where the heck is', keep_case),
    (re.compile(r'\bpoor buggers\b', re.I), 'poor fellows', keep_case),
    (re.compile(r'\bpoor bugger([’\']s)?\b', re.I), r'poor fellow\1', False),
    (re.compile(r'\bbuggered\s+up\b', re.I), 'messed up', keep_case),
    (re.compile(r'\b(I[’\']?m|I am|he[’\']?s|he is|she[’\']?s|she is|we[’\']?re|we are|they[’\']?re|they are)\s+buggered(?=\s*[.!?,;:]?$)', re.I), r'\1 exhausted', False),
    (re.compile(r'\bbuggering\s+(?:about|around)\b', re.I), 'messing around', keep_case),
    (re.compile(r'\bbugger\s+all\b', re.I), 'nothing', keep_case),
    (re.compile(r'(?m)^\s*bugger\s*[!.?]', re.I), 'darn', keep_case),
    (re.compile(r'\byou(?:\W+(?:daft|stupid|silly))?\W+bugger\b', re.I), 'you fool', keep_case),
    (re.compile(r"\b(don't|dont|do not) give a bugger\b", re.I), r'\1 care', False),
    (re.compile(r'\bfecking\b', re.I), 'darn', keep_case),
    (re.compile(r'\bscutter\b', re.I), 'rubbish', keep_case),
    (re.compile(r'\bpoxy\b', re.I), 'wretched', keep_case),
    (re.compile(r'\bcock[\s-]?up\b', re.I), 'mess up', keep_case),
    (re.compile(r'\bbloody\s+hell\b', re.I), 'heck', keep_case),
    (re.compile(r'\b(a|the)\s+bloody\s+(fool|idiot)\b', re.I), r'\1 \2', False),
    (re.compile(r'\bbloody\s+(fool|idiot)\b', re.I), r'\1', False),
    (re.compile(r'\bmost\s+bloody(?=\s+(?:awful|good|bad|stupid|useless|ridiculous|boring)\b)', re.I), 'most', keep_case),
    (re.compile(r'\bbloody(?=\s+(?:awful|good|bad|stupid|useless|ridiculous|boring|lucky|sorry|safe|near)\b)', re.I), 'very', keep_case),
    # Remaining standalone uses are intensifiers unless the next word marks a
    # clear literal blood reference; compounds such as bloodying are untouched.
    (re.compile(r'(?P<bloody>\bbloody)(?:\s+(?P<next_word>[A-Za-z]+)|\s+(?=\()|(?=[,!.?;:]|$))', re.I), remove_bloody_intensifier, False),
]

# Compatibility alias for consumers of the former combined crude sub-list.
crude_non_ass_list = strong_profanity_list + crude_insult_list + mild_crude_list + sexual_anatomical_list + british_list
unambiguous_profanity_list = strong_profanity_list + crude_insult_list

# Ass compound words (mode-independent) \u2014 toggled by replace_ass preference.
# These are always replaced regardless of ass_mode (dirty/clean/auto) because
# "smartass" and "jackass" are unambiguously insulting in context.
ass_compound_list = [
    #########################################
    # ass compound words (mode-independent)
    #########################################
    # smart ass
    (re.compile(r'smart\W?(ass|arse)\b', re.I), "smart aleck", keep_case),
    (re.compile(r'smart\W?(ass|arse)es\b', re.I), "smart alecks", keep_case),
    # kiss ass
    (re.compile(r'kissin[^\s]\W(ass|arse)(es)?\b',
                re.U+re.I), "kissing up", keep_case),
    (re.compile(r'kiss(\W+\w+){0,5}\W+(ass|arse)(es)?\b', re.I), "fly a kite", keep_case),
    (re.compile(r'kiss.{1,6}(ass|arse)(es)?\b', re.I), "fly a kite", keep_case),
    # kick ass
    (re.compile(r'kick\W?(ass|arse)\b', re.I), "kick booty", keep_case),
    (re.compile(r'kick\W?(ass|arse)es\b', re.I), "kick booties", keep_case),
    # cover ... ass
    (re.compile(r'(cover.{0,8} )(ass|arse)\b', re.I), r"\1rear", False),
    (re.compile(r'(cover.{0,8} )(ass|arse)es\b', re.I), r"\1rears", False),
    # kick ... ass
    (re.compile(r'(kick.{0,8} )(ass|arse)\b', re.I), r"\1rear", False),
    (re.compile(r'(kick.{0,8} )(ass|arse)\b', re.I), r"\1rears", False),
    # assed
    (re.compile(r'\bhalf[- ]ass(?:ed)?\b', re.I), 'half-baked', keep_case),
    (re.compile(r'\b(ass|arse)ed\b', re.I), "ended", keep_case),
    # badass is used as an adjective for impressive/tough.
    (re.compile(r'\bbadasses\b', re.I), 'tough people', keep_case),
    (re.compile(r'\bbadass\b', re.I), 'tough', keep_case),
    # jack/dumbass
    (re.compile(r'(?<=his )jackass\b', re.I), "donkey", keep_case),
    (re.compile(r'(?<=bray like a )(jack|dumb)ass\b', re.I), "donkey", keep_case),
    (re.compile(r'(jack|dumb)ass\b', re.I), "jerk", keep_case),
    (re.compile(r'(jack|dumb)asses\b', re.I), "jerks", keep_case),
    # horse's ass
    (re.compile(r'horse[^\s]?s ?(ass|arse)\b', re.U+re.I), "jerk", keep_case),
    (re.compile(r'horse[^\s]?s ?(asses|arses)\b', re.U+re.I), "jerks", keep_case),
]

# crude_list preserves the canonical flat rule order; the smaller lists below
# are separately controlled by preference flags in language_check.
crude_list = (strong_profanity_list + sexual_anatomical_list + crude_insult_list
              + mild_crude_list + ass_compound_list + british_list)

# "Damn" and all its variants
damn_list = [
    # Replace goddammit and dammit with 'dang it'
    (re.compile(r'([^\.?!] *) Goddam([mn])', re.I), r'\1 goddam\2', False),
    (re.compile(r'(?:gods?)?dammit', re.I), 'dang it', keep_case),
    #########################################
    # Replace damn and its varieties
    #########################################
    # I'll be damned
    (re.compile(r'be(\W+)(?:gods?[ -]*)?damned', re.I), r'be\1darned', False),
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
    (re.compile(r'\b(your|our|her|his|this|that|the|their|those|these|for|so|some|one|one more|too)( +)(?:gods? *)?damn(?:ed)?\b(?!-)', re.I), r'\1', False),
    # a damn
    (re.compile(r'(?<=\b[aA] )(?:gods? *)?damn(?:ed)',
                re.I), 'darn', keep_case),
    # damned good, damn sure, etc (Clancy's favorites)
    (re.compile(r'\b((?:gods? *)?damn(?:ed))(?:\W+)(sure|near|sight|good|much|hard|easy|big|little|glad|clever|mess|smart|fine|fool|right|thing|much|shame|nice|mean|bad|lucky|late|important)', re.I), '', drop_first_match),
    (re.compile(r'\b((?:gods? *)?damn(?:ed)?)(?:\W+)well', re.I), 'darn well', keep_case),
    # Religious damning
    (re.compile(r'\b(?:gods? *)?damned\b', re.I), 'cursed', keep_case),
    (re.compile(r'\b(?:gods? *)?damnedest', re.I), 'very best', keep_case),
    (re.compile(r'\b(?:gods? *)?damning', re.I), 'condemning', keep_case),
    (re.compile(r'\b(?:gods? *)?damnable', re.I), 'condemning', keep_case),
    (re.compile(r'\b(?:gods? *)?damnably', re.I), 'cursedly', keep_case),
    (re.compile(r'\b(?:gods? *)?damnatory', re.I), 'condemning', keep_case),
    (re.compile(r'\b(?:gods? *)?damnation', re.I), 'condemnation', keep_case),
    # damn it
    (re.compile(r', (?:gods? *)?damn it(?: all)?\b', re.I), '', keep_case),
    (re.compile(r'((?:gods? *)?damn it(?: all)?, +)(.)', re.I), '', drop_first_match),
    # a damn something, like "a damn nuisance"
    (re.compile(r'\ba(\W+)(?:gods? *)?damn(?= \w)\b', re.I), r'a\1blasted', False),
    # a damn (object)
    (re.compile(r'\ba(\W+)(?:gods? *)?damn\b', re.I), r'a\1cent', False),
    # damn you/his/her/etc
    (re.compile(r'\b(?:gods? *)?damn you to hell', re.I), 'curse you', keep_case),
    (re.compile(r'\b(?:gods? *)?damn(?= (him|his|her|you|next|the|you))', re.I),
        'curse', keep_case),
    # Word by itself
    (re.compile(r'\b(?:gods? *)?damn\b', re.I), 'dang', keep_case),
    # Final catch-all
    (re.compile(r'(?:gods? *)?damn', re.I), 'dang', keep_case),
]

# "Bitch" and all its variants
bitch_list = [
    #########################################
    # Bitch
    #########################################
    (re.compile(r'\bbitchiness\b', re.I), 'meanness', keep_case),
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
    # Explicit inflections; avoid partial-word matches leaving suffixes behind.
    (re.compile(r'\bbitchy\b', re.I), 'mean', keep_case),
    (re.compile(r'\bbitches\b', re.I), 'jerks', keep_case),
    # Final catch-all: clean the profane stem even inside compounds.
    (re.compile(r'\bbitch(e)?', re.I), 'jerk', keep_case),
]

# "Shit" and all its variants
shit_list = [
    #########################################
    # Shit
    #########################################
    # Convert shite to shit so later specific rules catch it
    (re.compile(r'\bshite\b', re.I), 'shit', keep_case),
    (re.compile(r'\bdipshits\b', re.I), 'idiots', keep_case),
    (re.compile(r'\bdipshit\b', re.I), 'idiot', keep_case),
    (re.compile(r'\bshitfaced\b', re.I), 'drunk', keep_case),
    (re.compile(r'\bbatshit\s+crazy\b', re.I), 'completely crazy', keep_case),
    (re.compile(r'\b(?:apeshit|batshit)\b', re.I), 'wild', keep_case),
    (re.compile(r'\b(he|she|it)\s+shits\b', re.I), r'\1 defecates', False),
    (re.compile(r'\b(they|we|you)\s+shit\b', re.I), r'\1 defecate', False),
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
]

# The f-bomb and all its variants
fbomb_list = [
    #########################################
    # f-bomb
    #########################################
    # Handle common compounds before the general f-word substitutions.
    (re.compile(r'\bfuckwits\b', re.I), 'idiots', keep_case),
    (re.compile(r'\bfuckwit\b', re.I), 'idiot', keep_case),
    (re.compile(r'\bfuckfaces\b', re.I), 'jerks', keep_case),
    (re.compile(r'\bfuckface\b', re.I), 'jerk', keep_case),
    (re.compile(r'\bfuckheads\b', re.I), 'idiots', keep_case),
    (re.compile(r'\bfuckhead\b', re.I), 'idiot', keep_case),
    (re.compile(r'\bfuckboys\b', re.I), 'jerks', keep_case),
    (re.compile(r'\bfuckboy\b', re.I), 'jerk', keep_case),
    (re.compile(r'\bun-?fucking-?(?=believable)', re.I), 'un', keep_case),
    # clean up script...
    (re.compile(r'(m[OoUu]th[AaEe]r?[ -]?)?fuck', re.I), 'zxsa', keep_case),
    # clean up script...
    (re.compile(r'(m[OoUu]th[AaEe]r?[ -]?)?fook', re.I), 'zxsa', keep_case),
    # f yourself
    (re.compile(r'zxsa[\W]?yourself', re.I), "kill yourself", first_case),
    # cluster f
    (re.compile(r'cluster[\W]?zxsa', re.I), "massive failure", first_case),
    # f your
    (re.compile(r'zxsa[\W]?your', re.I), "harass your", first_case),
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
    (re.compile(r' (zxsain[^\s]?(?: well)?)(\W+)',
                re.U+re.I), "", drop_first_match),
    (re.compile(r' (zxsain[^\s]?(?: well)?)(\b)',
                re.U+re.I), "", drop_first_match),
    (re.compile(r'zxsain[^\s]?', re.U+re.I), "frigging", keep_case),
    # f'er
    (re.compile(r'zxsaer', re.I), "idiot", keep_case),
    # f'it
    (re.compile(r'zxsa\W?it(\Wall)?', re.I), "phoo", keep_case),
    # f the
    (re.compile(r'zxsa(?=[\W]the)', re.I), "forget", keep_case),
    # f our/his/her/etc
    (re.compile(
        r'zxsa(?=(ed)?\W(our|her|his|us|this|that|their|those|these|them|[^\s]em|for|a\b))', re.U+re.I), "harass", keep_case),
    # f [name/noun]
    (re.compile(r'zxsa(?= ([A-Z][a-z]+|old|the\b|that\b|this\b))(?!\W(up|with))', re.I), "curse", keep_case),
    # f'ed
    (re.compile(r'zxsaed', re.I), "messed", keep_case),
    # verb
    (re.compile(r'zxsa(?=\W(around|with|on\b|up\b|over|under|through))', re.I),
        "mess", first_case),
    (re.compile(r'(?<=to\W)zxsa', re.I), "mess", first_case),
    # f, f ups
    (re.compile(r'zxsa(\W?up)?', re.I), "idiot", keep_case),
]

# "Hell" and all its variants
hell_list = [
    #########################################
    # hell
    #########################################
    # hellhound
    (re.compile(r'\bhell\W?hound', re.I), 'demonhound', keep_case),
    # hell-word (not helldiver bird)
    (re.compile(r'\bhell(?=-[^oO])(?!-diver)', re.I), 'demon', keep_case),
    # hell's bells
    (re.compile(r'\bhell[^o]{0,4}s?\W?bells?', re.I), 'by golly', keep_case),
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
    (re.compile(r'(?<=\bfor\Wthe\W)hell\b', re.I), 'heck', keep_case),
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
    (re.compile(r'(?i)\b(how|for|where|what|whatever|who|why|when)(\Wthe\W)(?:[a-z]+\W+)?(hell)\b'),
                lambda m: m.group(1) + m.group(2) + keep_case('heck', m, group=3), False),
    # Interjection uses, including the older "O hell!" form.
    (re.compile(r'\b(?:O|Oh)\W+hell(?=[,!.?]|$)', re.I), 'Oh heck', keep_case),
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
    (re.compile(r'(?<=\bis )hell\b', re.I), 'perdition', keep_case),
    (re.compile(r'(?<=\bit[^\s]s )hell\b', re.U+re.I), 'perdition', keep_case),
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
    (re.compile(r'\bhell\Ws', re.U+re.I), 'perdition\'s', keep_case),
    # interjection hell (preceeded by . or " or --, etc, followed by ,
    (re.compile(r'(?<=([\.?!,]\W\W|..\"|.."|.."|.\W\W))hell(?=[,!])',
                re.U+re.I), 'heck', keep_case),
    # >hell< shows up in html with italics or emphasis
    (re.compile(r'\>hell\<', re.U+re.I), '>perdition<', keep_case),
    # General fallback: the hell filter replaces every remaining standalone
    # use, including literal religious references, with the chosen substitute.
    (re.compile(r'\bhell\b', re.I), 'perdition', keep_case),
]

# ---------------------------------------------------------------------------
# re_list \u2014 the original monolithic list, preserved exactly as it was.
# Equals slur_list + crude_list + damn_list + bitch_list + shit_list +
#         fbomb_list + hell_list  (same order throughout).
# test_cleaner.py imports this name directly.
# ---------------------------------------------------------------------------
re_list = slur_list + crude_list + damn_list + bitch_list + shit_list + fbomb_list + hell_list


class RuleEngine:
    def __init__(self, rules):
        self.rules = rules
        # Keywords that should trigger an "early exit" optimization if none are present in a line.
        # This preserves the exact sequential regex behavior while skipping clean lines.
        keywords = set()
        for pattern, _, _ in rules:
            # Heuristic to extract keywords:
            # 1. Standardize common boundaries and remove backslashed tokens
            p_str = re.sub(r'\\[bWwSsDd]', ' ', pattern.pattern)
            # 2. Collapse character classes like [oO] to their first character
            p_str = re.sub(r'\[([a-zA-Z])[^\]]*\]', r'\1', p_str)
            # 3. Handle lookahead/lookbehind - remove the assertions but keep the content
            p_str = re.sub(r'\(\?<=([^\)]+)\)', r'\1', p_str)
            p_str = re.sub(r'\(\?=([^\)]+)\)', r'\1', p_str)
            # 4. Extract literal word characters of length 2+
            words = re.findall(r'[a-zA-Z]{2,}', p_str)
            for w in words:
                keywords.add(w.lower())

        # Ensure cascading keywords are included
        if 'zxsa' in keywords:
            keywords.add('fuck')
            keywords.add('fook')

        if keywords:
            # Sort by length descending to help the regex engine
            pattern = '(?:' + '|'.join(sorted((re.escape(k) for k in keywords), key=len, reverse=True)) + ')'
            self.keywords_re = re.compile(pattern, re.I)
        else:
            self.keywords_re = None

    def process_line(self, line):
        # Optimization: If no keyword is present, skip all regexes.
        if self.keywords_re and not self.keywords_re.search(line):
            return line

        # Maintain exact parity by running all rules in sequence.
        for pattern, sub, pcase in self.rules:
            if pcase:
                line = pattern.sub(partial(pcase, sub), line)
            else:
                line = pattern.sub(sub, line)
        return line

    def process_text(self, text):
        return "\n".join(self.process_line(line) for line in text.split("\n"))


def clean_text(text):
    replacement_list = language_check(text)
    engine = RuleEngine(replacement_list)
    return engine.process_text(text)


def language_check(text, vain_override='auto', ass_override='auto',
                   replace_slurs=True, replace_crude=True,
                   replace_damn=True, replace_bitch=True,
                   replace_shit=True, replace_fbomb=True,
                   replace_hell=True, replace_religious=True,
                   replace_ass=True, replace_god=False,
                   debug=False, replace_strong=None, replace_sexual=None,
                   replace_insults=None, replace_mild_crude=None,
                   replace_british=None):
    """
    Build the ordered list of replacement rules based on content and preferences.

    Per-word-family flags (all default True for backward compatibility):
      replace_strong   \u2014 C-word, cocksucker, and F-word family replacements.
      replace_slurs    \u2014 racial/ethnic slurs
      replace_crude    \u2014 legacy master fallback for the newer crude groups.
      replace_sexual   \u2014 sexual/anatomical replacements.
      replace_insults  \u2014 crude insult replacements.
      replace_mild_crude \u2014 mild bodily/bathroom terms.
      replace_british  \u2014 British/Irish slang and intensifier replacements.
      replace_damn     \u2014 "damn" and all variants
      replace_bitch    \u2014 "bitch" and all variants
      replace_shit     \u2014 "shit" and all variants
      replace_fbomb    \u2014 legacy argument; F-word rules now follow replace_strong.
      replace_hell     \u2014 "hell" and all variants
      replace_religious \u2014 lord_list / vain_lord_list
      replace_ass      \u2014 standalone *ss/*rse and donkey-related compounds
                         AND the dirty_a_list / clean_a_list for standalone *ss.
                         When False, ass/arse rules in this group are skipped.
      replace_god      \u2014 replace every standalone "God" not preceded by "of" and
                         not followed by "bless" or "save" (god_replace_list).
                         Broad catch-all \u2014 defaults to False.

    vain_override: 'auto' | 'always' | 'never'
      Controls whether vain_lord_list is applied.
      'always' \u2014 assume the author uses "God/Jesus/Christ" as an exclamation
                 (Tom Clancy style).
      'never'  \u2014 assume all uses are sincere/reverential (C.S. Lewis style).
      'auto'   \u2014 detect from text.

    ass_override: 'auto' | 'dirty' | 'clean'
      Only used when replace_ass=True.
      'dirty' \u2014 assume "ass" means rear end / insult (dirty_a_list).
      'clean' \u2014 assume "ass" means donkey (clean_a_list, C.S. Lewis style).
      'auto'  \u2014 detect from text.
    """
    ret_val = []
    replace_strong = replace_crude if replace_strong is None else replace_strong
    replace_sexual = replace_crude if replace_sexual is None else replace_sexual
    replace_insults = replace_crude if replace_insults is None else replace_insults
    replace_mild_crude = replace_crude if replace_mild_crude is None else replace_mild_crude
    replace_british = replace_crude if replace_british is None else replace_british

    if replace_slurs:
        ret_val += slur_list
    if replace_strong:
        ret_val += strong_profanity_list
    if replace_sexual:
        ret_val += sexual_anatomical_list
    if replace_insults:
        ret_val += crude_insult_list
    if replace_mild_crude:
        ret_val += mild_crude_list
    if replace_ass:
        ret_val += ass_compound_list
    if replace_british:
        ret_val += british_list
    if replace_damn:
        ret_val += damn_list
    if replace_bitch:
        ret_val += bitch_list
    if replace_shit:
        ret_val += shit_list
    if replace_strong:
        # Keep the former F-word rule position while sharing the strong toggle.
        ret_val += fbomb_list
    if replace_hell:
        ret_val += hell_list

    if replace_religious:
        ret_val += lord_list

    # Determine if this book is likely to take Lord's name in vain
    use_vain = False
    if vain_override == 'always':
        use_vain = True
    elif vain_override == 'never':
        use_vain = False
    else:  # auto
        vain_trigger = (
            r"(for Christ's sake|Holy Christ|Holy Jesus|for God's sake|God almighty|"
            r"goddamn|dammit|fook|fuck|motherfuck|cunt|cocksuck|dickhead|dickweed|"
            r"asshole|arsehole|slut|shit)"
        )
        if re.search(vain_trigger, text, re.I):
            use_vain = True

    if replace_religious and use_vain:
        if debug:
            print("Looks like book uses Lord's name in vain")
        ret_val += vain_lord_list
    elif replace_religious:
        if debug:
            print("Looks like book does not use Lord's name in vain")

    if replace_god:
        ret_val += god_replace_list

    # Ass has two very different contexts. Guess which to use.
    if replace_ass:
        use_dirty_ass = False
        if ass_override == 'dirty':
            use_dirty_ass = True
        elif ass_override == 'clean':
            use_dirty_ass = False
        else:  # auto
            if re.search(r"(dumbass|asshole|arsehole|asswipe|smart\W?(ass|arse)|kick\W?(ass|arse)|ass\W?kick|ass\W?handed|badass|cover.{0,5}(ass|arse))", text, re.I):
                use_dirty_ass = True

        if use_dirty_ass:
            ret_val += dirty_a_list
            if debug:
                print("Looks like book does not need the donkey treatment")
        else:
            ret_val += clean_a_list
            if debug:
                print("Looks like book calls donkeys asses")
    else:
        if debug:
            print("Ass/arse replacements disabled")

    return ret_val
