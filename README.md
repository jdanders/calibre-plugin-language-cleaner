# calibre-plugin-language-cleaner
This is a lengthy list of regexes to "clean up" language in books. This works as a profanity filter for Kindle and other ebooks.

I wrote this plugin because I don't like reading vulgar language, but I like reading books with vulgar language in it :). Personally I find books much more enjoyable after being processed with this script. Obviously it is a personal set of filters, but I've done my best to make the changes sound as natural as possible, and after using it for years, I think it's pretty good.

If you'd like to customize it to meet your preferences, there is an option in the plugin configuration to add custom replacements, optionally using regex. There's also a live tester right in the config dialog so you can try your replacements before saving them.


## Installation and Setup

1. In calibre choose **Preferences → Plugins → Load plugin from file**.
2. Choose the plugin zip file.
3. Add the button to the toolbar:

   a. **Preferences → Toolbars & Menus**

   b. Select **The main toolbar**

   c. Find **Clean** in the left list and move it to the right

   d. Click **Apply** and restart Calibre

4. Optionally add it to the right-click context menu too:

   a. **Preferences → Toolbars & Menus**

   b. Select **The context menu for the books in the calibre library**

   c. Find **Clean** in the left list and move it to the right

   d. Click **Apply** and restart Calibre

If you forget either of those steps, the plugin will remind you on the next launch and offer to walk you through it. You can tell it to stop reminding you if you don't need it in both places.

To create the install zip file from source:
* Run the `make_plugin.sh` script, or add these files to a zip file:

      __init__.py
      action.py
      cleaner.py
      config.py
      config_widget.py
      images/
      README.md
      plugin-import-name-language_clean_plugin.txt


## Usage

Select one or more books in your library and click the **Clean** toolbar button (or right-click → **Clean Selected Books**). The plugin will ask for confirmation, then clean the books and report how many replacements were made.

For a single book that has multiple formats, you'll be asked which format to clean before anything happens.

There's also a **Preview Language Changes** option in the button's dropdown menu. This does a dry run on the first selected book and shows you a colour-coded diff of every change that would be made — red for the original text, green for the replacement — without touching the file.

After cleaning, the job log (Jobs → Show job details) lists every individual replacement that was made, grouped by file, so you can review exactly what changed.


## Configuration

Open the config dialog via the button's dropdown menu → **Configure…**, or **Preferences → Plugins → Language Cleaner → Customize**.

**Replacement Options** are grouped by category:

### Profanity — individual word families
- **Replace d\*\*\* variants** — d\*mn and all its variants.
- **Replace b\*\*\*\* variants** — b\*tch and all its variants.
- **Replace s\*\*\* variants** — sh\*t and all its variants.
- **Replace f\*\*\* variants** — the f-bomb and all its variants.
- **Replace h\*\*\* variants** — h\*ll and all its variants.

### Donkey language
The word "\*ss" has two very different meanings. You can choose whether to replace it at all, and how to handle the ambiguous standalone case:
- **Replace \*ss / \*rse (standalone and compound words)** — Global replacement setting. Compound words (sm\*rt-\*ss, j\*ck\*ss, k\*ss-\*ss, etc.) are always replaced regardless of the mode setting.
- **Standalone "\*ss" / "\*rse" means:** choose
  - **auto-detect**: this is default, try to guess mode based on book content
  - **insult** (Tom Clancy style): assume the word is used as an insult
  - **donkey** (C.S. Lewis style): assume the word is describing a donkey

### Religious language
- **Replace uses of God / Jesus / Christ** — Global replacement setting. Do contextual replacements (e.g. "Thank God", "My God!", "For God's sake").
- **Exclamatory "Lord" usage** — The word "God" appears in both reverent and purely exclamatory contexts. Choose
  - **auto-detect**: this is default, try to guess mode based on book content
  - **always exclamatory** (Tom Clancy style): assume usual vain use of God
  - **always reverential** (C.S. Lewis style): assume respectful use of God
- **Replace ALL occurrences of "God" and "Christ"** — Warning: this is turns off contextual smarts and just replaces every occurance  — catches narration, theology, character names, etc. Off by default.

### Crude language
- **Replace crude language** — Body-part references, bathroom humour, and crude compound words (cr\*p, d\*ck, b\*stard, etc.)

### Slurs
- **Replace racial / ethnic slurs** — Common offensive slurs; on by default.

If you want a pretty thorough list of the changes the plugin will make, you could look at [test_cleaner.py](test_cleaner.py) — it is a test suite of changes that should be made.

### Custom replacements
Add your own find/replace pairs to the table. The **Find** column supports Python regular expressions (e.g. `\bword\b`), and **Replace** can use backreferences (e.g. `\1`). Uncheck **Regex** to match text literally. Case sensitivity is controlled per-row. There's a **live tester** at the bottom — type some text, click **Test**, and see the result immediately.

### General options
- **Create backup of original file** — Saves the pre-cleaned version as ORIGINAL_EPUB (or ORIGINAL_AZW3, etc.) inside the library entry. On by default. You can restore it any time via right-click → **Restore** in the Book Details panel.
- **Show confirmation dialog before cleaning** — On by default; uncheck if you clean books frequently and find it annoying.
- **Mute plugin setup instructions** — Stops the plugin from reminding you about toolbar setup on launch.
- **Write change logs to directory** — Writes plain-text before/after copies of the book's content to a folder of your choice. Off by default. Handy if you want to diff versions yourself; I use [WinMerge](http://winmerge.org/) for that.


## KINDLE PROFANITY FILTER

The books on your Kindle that you have loaded from Amazon's cloud are "protected" by "DRM", or digital rights management. It's not a very good protection though and you might find a way to extract them if you Google "DeDRM". The legality of using such a solution is something I cannot help you with.

If you've got unprotected Kindle books (or DeDRM installed), you can use this plugin to clean your library:
* Load the books from your Kindle device into your Calibre library using the Device button
* Remove the books from the device using "Remove books" in the Device tab (so you're not left with two copies)
* Select the books in your library, click **Clean**, and let it run
* Send the cleaned books back to your Kindle using "Send to device"

That's it — no format conversion needed. The plugin handles AZW3 directly. The one exception is old-style Mobipocket files; see the Limitations section below.


## LIMITATIONS

Language filtering is inherently problematic — people interpret words in different ways, and words are used in boundless combinations. This is not a perfect solution, but as I said it is good enough for me.

If you find glaring holes in language that should be filtered, it may be that the source material has formatting tags in the middle of a word. If it is really important to you that the filtering works, you may need to use the "Edit book" feature of calibre first.

Old-style MOBI files (the ones Amazon called "Mobipocket" rather than KF8) can't be cleaned directly because of how they're structured. If you hit that, convert the book to a new MOBI first: right-click → Convert → MOBI output → set "MOBI file type" to "new", then clean the result.

By the way, there is a strong layer of irony here — if vulgar language offends you, you'll probably want to avoid actually looking in the `cleaner.py` file, as it is chock full of it :)
