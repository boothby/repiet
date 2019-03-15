from collections import namedtuple
from PIL import Image
from itertools import product


Block = namedtuple('block', ['x','y','size', 'corners'])

HL =  {(a,b,c): (i, 3*j+k)
                 for i, (x,y) in enumerate(((0,192), (0, 255), (192, 255)))
                     for j, (u,v) in enumerate(((x,y),(y,x)))
                        for k, (a,b,c) in enumerate(((v,u,u), (v,v,u), (u,v,u)))}

SLIDE = (255, 255, 255)

INS = [["NOP", "PSH", "POP"],
       ["ADD", "SBT", "MLT"],
       ["DVD", "MOD", "NOT"],
       ["GRT", "PTR", "SWT"],
       ["DPL", "RLL", "DIN"],
       ["CIN", "DUT", "CUT"]]
"""
clas Parser:
    def __init__(self, filename):
        lexer = Lexer(filename)

        

    def _parse(self, image):
        X, Y = image.size
        find = self._find
        for p in product(range(X), range(Y)):
            r = find(p)
            if r == p:
                x, y = r
                size = self._rank[r]
                color = image.getpixel((x,y))
                block[p] = Block(x, y, size, corners[r], color)


        def step(self, x, y, d, c, patience=8, sliding=False):
            x, y = corners[_find(x, y)][d, c]
            xy1 = self._next(x, y, X, Y, d)            
            

            if color == SLIDE:
                if not sliding:
                    patience = 4
                x2, y2 = self._slide[xy1, d] if d in (1, 2) else self._slide[self._slide[xy1, d^2], d]
                xy3 = self._next(x2, y2, X, Y, d)
                if xy3 is None:
                    return jump(x2, y2, d+1, c^1, patience-1, True) if patience else ()
                return 'NOP', (xy3 + (d, c),)
            elif color in HL:
                color0 = image.getpixel((x, y))
                h0,l0 = HL[color0]
                h1,l1 = HL[color1]
                ins = INS[(h1-h0)%6][(l1-l0)%3]
                return ins, ((x, y, d, c), (x, y, d, c^1)) if ins == 'SWT' else
                            tuple((x,y,(d+i)%4,c) for i in (0,1,2,3)) if ins == 'PTR' else
                            ((x, y, d, c),)
            else:
                return jump(x, y, (d+1)%4, c, patience-1) if patience % 2 else
                       jump(x, y, d, c^1, patience-1) if patience > 0 else ()



        for (x, y), b in blocks.items():
            link = {}
            for d in (0, 1, 2, 3):
                for c in (0, 1):
                    link[x, y, d, c] = jump(x, y, d, c)
            b.corners = link

    def _next(self, x, y, X, Y, d):
        return (((x+1, y) if x < X-1 else None) if d == 0 else
                ((x, y+1) if y < Y-1 else None) if d == 1 else
                 ((x-1, y) if x else None) if d == 2 else
                 ((x, y-1) if y else None))
"""


    
