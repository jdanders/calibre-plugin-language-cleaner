#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function, with_statement)
import time
import os
import mimetypes
import codecs
import sys
from functools import partial
from calibre_plugins.language_clean_plugin.cleaner import *
from calibre.ebooks.tweak import *
from optparse import OptionGroup, Option
from calibre.customize import FileTypePlugin
logdir = "c:/Scratch/calibre"
__license__ = 'GPL v3'
__copyright__ = '2012, Jordan Anderson'
__docformat__ = 'restructuredtext en'

#from __future__ import with_statement


class CleanerPlugin(FileTypePlugin):

    name = 'Language Cleaner'  # Name of the plugin
    description = ('Replace naughty or offensive language with something more '
                   'acceptable (to me at least)')
    # Platforms this plugin will run on
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Jordan Anderson'  # The author of this plugin
    version = (2019, 9, 2)   # The version number of this plugin
    # The file types that this plugin will be applied to
    file_types = set(['epub'])
    on_preprocess = True  # Run this plugin after conversion is complete
    minimum_calibre_version = (0, 7, 53)

    def run(self, path_to_ebook):
        #print ("*"*60,"\n","you are in Language Cleaner")
        #print ("*"*60,"\n")
        ebook_file = path_to_ebook
        fmt = ebook_file.rpartition('.')[-1].lower()
        exploder, rebuilder = get_tools(fmt)
        tmppath = '_tweak_' + os.path.basename(ebook_file).rpartition('.')[0]
        with TemporaryDirectory(tmppath) as tdir:
            #prints ("Relevant info:",tdir,fmt,ebook_file)
            try:
                opf = exploder(ebook_file, tdir)
            except WorkerError as e:
                prints('Failed to unpack', ebook_file)
                prints(e.orig_tb)
                raise SystemExit(1)
            except Error as e:
                prints(as_unicode(e), file=sys.stderr)
                raise SystemExit(1)
            # Debug
            print ("Created tdir:", tdir, "and found opf", opf)
            #print (os.popen("ll "+tdir).read())
            #print ("OPF CONTENTS:")
            #print (open(opf,'r').read())
            # manipulate all of the files
            opf = open(opf, 'r').read().split('\n')
            # first, assemble the entire text to evaluate context
            text = ""
            for f in walk(tdir):
                opf_line = [ii for ii in opf if
                            os.path.basename(f).lower() in ii.lower()]
                ftype = mimetypes.guess_type(f)[0]
                if not ftype and "html" in f.split('.')[-1]:
                    print('Non-text type %s for file %s but forcing text mode'
                          % (ftype, f))
                    ftype = 'text'
                if not ftype:
                    print('Non-text type %s for file %s' % (ftype, f))
                elif opf_line and 'text' in ftype:
                    encodings = ['utf-8', 'windows-1252', 'windows-1250']
                    for e in encodings:
                        try:
                            text += codecs.open(f, 'r', encoding=e).read()
                        except UnicodeDecodeError:
                            print('File %s: got unicode error with %s , trying different encoding' % (f, e))
                        else:
                            print('File %s: opening the file with encoding:  %s ' % (f, e))
                            break
            replacement_list = language_check(text)
            start_text = text
            end_text = ""
            # Now do replacements on each file
            for f in walk(tdir):
                opf_line = [ii for ii in opf if
                            os.path.basename(f).lower() in ii.lower()]
                # Not sure what the correct way to determine which files should
                # be edited. Seems like most are marked 'application/' in type
                print ("File", f, "\nOPF line:\n", opf_line)
                ftype = mimetypes.guess_type(f)[0]
                if not ftype and "html" in f.split('.')[-1]:
                    print('Non-text type %s for file %s but forcing text mode'
                          % (ftype, f))
                    ftype = 'text'
                if not ftype:
                    print('Non-text type %s for file %s' % (ftype, f))
                elif opf_line and 'text' in ftype:
                    print ("Cleaning", f)
                    text = open(f, 'r').read()
                    output = ""
                    for line in text.split("\n"):
                        # Go through all elements of replacement_list
                        for search, sub, pcase in replacement_list:
                            if pcase:  # Preserve case
                                line = search.sub(partial(pcase, sub), line)
                            else:  # Don't preserve case
                                line = search.sub(sub, line)
                        output += line + "\n"
                    open(f, 'w').write(output)
                    end_text += output
            if start_text.replace('\n', "") == end_text.replace('\n', ''):
                print ("Language cleaner made no changes")
            else:
                if os.path.exists(logdir):
                    open(logdir+os.sep+'%s_init.txt' %
                         (os.path.basename(ebook_file)+str(time.time())), 'w').write(start_text)
                    open(logdir+os.sep+'%s_mod.txt' %
                         (os.path.basename(ebook_file)+str(time.time())), 'w').write(end_text)
            prints('Rebuilding', ebook_file, 'please wait ...')
            try:
                rebuilder(tdir, ebook_file)
            except WorkerError as e:
                prints('Failed to rebuild', ebook_file)
                prints(e.orig_tb)
                raise SystemExit(1)
            prints(ebook_file, 'successfully cleaned')

        #print (path_to_ebook,ext,str(mi))
        #print ("you are returning from Language Cleaner")
        return ebook_file
