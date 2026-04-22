from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/language_cleaner')
prefs.defaults = {
    # -----------------------------------------------------------------------
    # Slurs
    # -----------------------------------------------------------------------
    'replace_slurs': True,          # racial / ethnic slur replacements

    # -----------------------------------------------------------------------
    # Crude language group
    # -----------------------------------------------------------------------
    'replace_crude': True,          # body-part terms, bathroom humour, crude
                                    # compounds (t*ts, sl*t, cr*p, c*nt, d*ck,
                                    # b*stard, wh*rehouse, ass-compounds, etc.)

    # -----------------------------------------------------------------------
    # Individual profanity word families
    # -----------------------------------------------------------------------
    'replace_damn': True,           # d*mn and all variants
    'replace_bitch': True,          # b*tch and all variants
    'replace_shit': True,           # sh*t and all variants
    'replace_fbomb': True,          # the f-bomb and all variants
    'replace_hell': True,           # h*ll and all variants

    # -----------------------------------------------------------------------
    # Religious language
    # -----------------------------------------------------------------------
    'replace_religious': True,      # lord_list (reverential uses of God/Jesus/Christ)

    # How to handle "vain" / exclamatory uses of the Lord's name:
    #   'auto'   — detect from text
    #   'always' — treat as exclamation (Tom Clancy style)
    #   'never'  — treat as sincere/reverential (C.S. Lewis style)
    'replace_vain_lord': 'auto',

    # Replace every standalone "God" unconditionally (word-boundary match only).
    # Broad catch-all — off by default.
    'replace_god': False,

    # -----------------------------------------------------------------------
    # "Ass" interpretation
    # -----------------------------------------------------------------------
    # How to interpret standalone "ass" / "arse":
    #   'auto'  — detect from text
    #   'dirty' — assume it means rear end or insult (Tom Clancy style)
    #   'clean' — assume it means donkey (C.S. Lewis style)
    'ass_mode': 'auto',

    # Whether to replace ass/arse compound words and standalone ass/arse at all.
    # When False, dirty_a_list / clean_a_list are skipped entirely, and the
    # ass compound words inside crude_list are also suppressed.
    'replace_ass': True,

    # -----------------------------------------------------------------------
    # Misc
    # -----------------------------------------------------------------------
    'custom_replacements': [],      # list of [find_str, replace_str, ignore_case, is_regex]
    'create_backup': True,
    'show_confirm_dialog': True,
    'write_log': False,
    'log_dir': '',                  # custom log directory; empty = calibre config dir
    'mute_setup_warning': False,
    'plugin_fingerprint': None,     # mtime fingerprint; changes on every reinstall/upgrade
}
