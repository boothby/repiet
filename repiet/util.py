from collections import namedtuple as _namedtuple

OP = [["NOP", "PSH", "POP"],
      ["ADD", "SBT", "MLT"],
      ["DVD", "MOD", "NOT"],
      ["GRT", "PTR", "SWT"],
      ["DPL", "RLL", "DIN"],
      ["CIN", "DUT", "CUT"]]

SLIDE = (255, 255, 255)

HL =  {(a,b,c): (3*j+k, i)
                 for i, (x,y) in enumerate(((0,192), (0, 255), (192, 255)))
                     for j, (u,v) in enumerate(((x,y),(y,x)))
                        for k, (a,b,c) in enumerate(((v,u,u), (v,v,u), (u,v,u)))}

Node = _namedtuple('node', ['name', 'ops', 'dests'])
Lexeme = _namedtuple('lexeme', ['name', 'corners', 'size', 'color'])

