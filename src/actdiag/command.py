# -*- coding: utf-8 -*-
#  Copyright 2011 Takeshi KOMIYA
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import re
import sys
from ConfigParser import SafeConfigParser
from optparse import OptionParser
import actdiag
import DiagramDraw
import diagparser
from blockdiag.command import create_fontmap, detectfont
from builder import ScreenNodeBuilder


def parse_option():
    version = "%%prog %s" % actdiag.__version__
    usage = "usage: %prog [options] infile"
    p = OptionParser(usage=usage, version=version)
    p.add_option('-a', '--antialias', action='store_true',
                 help='Pass diagram image to anti-alias filter')
    p.add_option('-c', '--config',
                 help='read configurations from FILE', metavar='FILE')
    p.add_option('-o', dest='filename',
                 help='write diagram to FILE', metavar='FILE')
    p.add_option('-f', '--font', default=[], action='append',
                 help='use FONT to draw diagram', metavar='FONT')
    p.add_option('--fontmap',
                 help='use FONTMAP file to draw diagram', metavar='FONT')
    p.add_option('-s', '--separate', action='store_true',
                 help='Separate diagram images for each group (SVG only)')
    p.add_option('-T', dest='type', default='PNG',
                 help='Output diagram as TYPE format')
    p.add_option('--nodoctype', action='store_true',
                 help='Do not output doctype definition tags (SVG only)')
    options, args = p.parse_args()

    if len(args) == 0:
        p.print_help()
        sys.exit(0)

    options.type = options.type.upper()
    if not options.type in ('SVG', 'PNG', 'PDF'):
        msg = "ERROR: unknown format: %s\n" % options.type
        sys.stderr.write(msg)
        sys.exit(0)

    if options.type == 'PDF':
        try:
            import reportlab.pdfgen.canvas
        except ImportError:
            msg = "ERROR: could not output PDF format; Install reportlab\n"
            sys.stderr.write(msg)
            sys.exit(0)

    if options.separate and options.type != 'SVG':
        msg = "ERROR: --separate option work in SVG images.\n"
        sys.stderr.write(msg)
        sys.exit(0)

    if options.config and not os.path.isfile(options.config):
        msg = "ERROR: config file is not found: %s\n" % options.config
        sys.stderr.write(msg)
        sys.exit(0)

    configpath = options.config or "%s/.blockdiagrc" % os.environ.get('HOME')
    if os.path.isfile(configpath):
        config = SafeConfigParser()
        config.read(configpath)

        if config.has_option('blockdiag', 'fontpath'):
            fontpath = config.get('blockdiag', 'fontpath')
            options.font.append(fontpath)

    return options, args


def main():
    options, args = parse_option()

    infile = args[0]
    if options.filename:
        outfile = options.filename
    elif infile == '-':
        outfile = 'output.' + options.type.lower()
    else:
        outfile = re.sub('\..*', '', infile) + '.' + options.type.lower()

    try:
        if infile == '-':
            import codecs
            stream = codecs.getreader('utf-8')(sys.stdin)
            tree = diagparser.parse_string(stream.read())
        else:
            tree = diagparser.parse_file(infile)

        fontmap = create_fontmap(options)
        diagram = ScreenNodeBuilder.build(tree, separate=options.separate)
        draw = DiagramDraw.DiagramDraw(options.type, diagram, outfile,
                                       fontmap=fontmap,
                                       antialias=options.antialias,
                                       nodoctype=options.nodoctype)
        draw.draw()
        draw.save()
    except UnicodeEncodeError, e:
        msg = "ERROR: UnicodeEncodeError caught (check your font settings)\n"
        sys.stderr.write(msg)
    except Exception, e:
        sys.stderr.write("ERROR: %s\n" % e)