# calibre-plugin-language-cleaner
Lengthy list of regexes to "clean up" language in books. Works as a profanity filter for Kindle and other ebooks.

I wrote this plugin because I don't like reading vulgar language, but I like reading books with vulgar language in it :). Personally I find books much more enjoyable after being processed with this script. Obviously it is a personal set of filters, but I've done my best to make the changes sound as natural as possible, and after using it for years, I think it's pretty good.

If you'd like to customize it to meet your preferences, you just need to go through the lines of cleaner.py and add or remove filters as needed. You'll probably need a pretty good mastery of regular expressions to write new ones unless there is a similar one existing already that you can tweak.

## Installation

To install:
* Download zip file from the [releases](https://github.com/jdanders/calibre-plugin-language-cleaner/releases) page, or create zip from source as described below
* In calibre choose Preference -> Plugins -> Load plugin from file
* Choose the zip file, and the plugin should show up under "File type plugins"

To use:
* Choose the book you'd like and make sure you have an epub format (so convert to epub if you don't already have that format)
* Now do "Convert book" and choose to convert from Epub to Epub (or whatever destination format you want)
* Wait until longer than usual job completes, due the very inefficient way this plugin works

To create install zip from source:
* create a zip file with the three files: `cleaner.py`, `__init__.py`, and `plugin-import-name-language_clean_plugin.txt` called `Language_Cleaner.zip`. This command may help in Linux.

`zip Language_Cleaner cleaner.py __init__.py plugin-import-name-language_clean_plugin.txt`


## KINDLE PROFANITY FILTER

The books on your Kindle that you have loaded from Amazon's cloud are "protected" by "DRM", or digital rights management. It's not a very good protection though and you might find a way to extract them if you Google "DeDRM". The legality of using such a solution is something I cannot help you with.

If you've got unprotected Kindle books (or dedrm installed), you can use this plugin to clean your library:
* Open Calibre
* Load books you wish to filter from the Kindle device into your Calibre Library using the Device button in Calibre
* Delete all the books you loaded from the device (so they are not on the Kindle any more) by using "Remove books" in the Device tab
* Go back to the Library button and "Bulk convert" all the books in the library that you want to edit with "Output Format" of epub (the other default settings are fine)
* Bulk delete the AMZ format from the books in your library (so only epub should be left). Use the "Remove all formats from selected books, except..." option and select EPUB to keep.
* Send the books to your Kindle device using the Calibre "Send to device" option

This will convert and then load the books back on to the Kindle. It might take a minute or two per book, so be patient :)


## LIMITATIONS

I am no expert at calibre, and I could not drum up much help on the support forums, so the integration is pretty weak. It only works on books that are being converted from epub, and only works during the conversion process.

Secret debug tip:
If there is a "c:/Scratch/calibre" folder on your Windows machine or '/tmp/calibre' on Linux (change `logdir` in `__init__.py` if you want), the plugin will write before and after versions of the book as plain text files. Sometimes it does two copies and only one has useful changes. If you'd like to see how it was changed, compare the two files. I use [WinMerge](http://winmerge.org/) and that works well.

By the way, there is a strong layer of irony here -- if vulgar language offends you, you'll probably want to avoid actually looking in the `cleaner.py` file, as it is chock full of it :)
