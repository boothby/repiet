from collections import namedtuple as _namedtuple
import argparse as _argparse

OP = [["NOP", "PSH", "POP"],
      ["ADD", "SBT", "MLT"],
      ["DVD", "MOD", "NOT"],
      ["GRT", "PTR", "SWT"],
      ["DPL", "RLL", "DIN"],
      ["CIN", "DUT", "CUT"]]

SLIDE = (255, 255, 255)
BLOCK = (0, 0, 0)

HL =  {(a,b,c): (3*j+k, i)
         for i, (x,y) in enumerate(((0,192), (0, 255), (192, 255)))
             for j, (u,v) in enumerate(((x,y),(y,x)))
                for k, (a,b,c) in enumerate(((v,u,u), (v,v,u), (u,v,u)))}

CODING = {SLIDE, BLOCK}.intersection(HL)

Node = _namedtuple('node', ['name', 'ops', 'dests'])
Lexeme = _namedtuple('lexeme', ['name', 'corners', 'size', 'color'])

def default_opinions(codel_size=1, noncoding='block', sliding='halting', color_dir_h='-', color_dir_l='-'):
    """Constructs an opinions dictionary for a repiet compiler pass
    (implicity filling in defaults)"""
    return dict(codel_size=codel_size,
                noncoding=noncoding,
                sliding=sliding,
                color_dir_h=color_dir_h,
                color_dir_l=color_dir_l)

#below is stuff used in bin/repiet for argparse -- but it's convenient to
#collect it here instead.
def _positive(arg):
    try:
        val = int(arg)
        if val > 0: return val
    except: pass
    raise _argparse.ArgumentTypeError("%r is not a positive integer" % arg)

opinion_options = {
    'codel_size': {'type':_positive, 'help':'Codel size'},
    'noncoding': {'type':str, 'choices':('block', 'slide', 'round'),
        'help':"Behavior for nonstandard pixel values.  'round' selects the nearest standard value"},
    'sliding': {'type':str, 'choices':('halting', 'nonhalting', 'timid'), 
        'help':("Behavior for sliding regions -- DMM's spec suggests 'halting';"
                "'nonhalting' emulates npiet; 'timid' emulates PietDev") },
    'color_dir_h': {'type':str, 'choices':('-', '+'),
               'help':"Determines how hue-change produces instructions (use + to emulate buggy interpreters)"},
    'color_dir_l': {'type':str, 'choices':('-', '+'), 
               'help':"Determines how lightness-change produces instructions (use + to emulate buggy interpreters)"},
}
