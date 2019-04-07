from optimizer import _PPVM
import networkx as nx
from PIL import Image
import numpy as np

OP = [["NOP", "PSH", "POP"],
      ["ADD", "SBT", "MLT"],
      ["DVD", "MOD", "NOT"],
      ["GRT", "PTR", "SWT"],
      ["DPL", "RLL", "DIN"],
      ["CIN", "DUT", "CUT"]]

HL =  {(a,b,c): (3*j+k, i)
                 for i, (x,y) in enumerate(((192, 255), (0, 255), (0,192)))
                     for j, (u,v) in enumerate(((x,y),(y,x)))
                        for k, (a,b,c) in enumerate(((v,u,u), (v,v,u), (u,v,u)))}

HL_ = {v: k for k, v in HL.items()}
HL_[None, 0] = (0,0,0)
HL_[None, 1] = (255, 255, 255)

OP_ = { op : (dh, dl)
            for dh, row in enumerate(OP)
            for dl, op in enumerate(row)}



def render(s, filename, colors=((0,0), (2,0))):
    deps = nx.DiGraph()
    c_i = 0
    xmax = ymax = 0
    for y, line in enumerate(s.split("\n")):
        ymax = max(y, ymax)
        for x, chunk in enumerate(zip(*[iter(line)]*5)):
            xmax = max(x, xmax)
            d = chunk[0]
            arrow = 'v>^<'.find(d)
            if arrow >= 0:
                dx = (1-(arrow&2))*(arrow&1)
                dy = (1-(arrow&2))*(~arrow&1)


                op = ''.join(chunk[1:4])
                print x, y, d, op, x+dx, y+dy
                deps.add_node((x,y), op=op)
                deps.add_edge((x,y), (x+dx, y+dy))

            elif d == ' ':
                if chunk[1] == 'x':
                    deps.add_node((x, y), color=colors[c_i])
                    c_i = (c_i+1)%len(colors)
                elif chunk[1] == 'c':
                    deps.add_node((x, y), color=(int(chunk[2]), int(chunk[3])))
                    c_i = (c_i+1)%len(colors)
                elif chunk[1] == '#':
                    deps.add_node((x, y), color=(None, 0))
                else:
                    deps.add_node((x, y), color=(None, 1))
            else:
                raise RuntimeError("bad chunk {}".format(chunk))

    for e in deps.edges():
        print e

    M = np.zeros((ymax+1, xmax+1, 3), np.uint8)
    for y in range(ymax+1):
        for x in range(xmax+1):
            n = deps.node.get((x,y))
            if n is None:
                M[y][x] = HL_[None,1]
                continue
            if n.has_key('color'):
                M[y][x] = HL_[n['color']]
                continue

            n = (x, y)
            s = n, ()
            hits = set([n])
            while 1:
                if deps.node[n].has_key('color'):
                    c = deps.node[n]['color']
                    print c
                    _, s = s
                    break

                try:
                    m, = deps[n]                    
                except ValueError:
                    raise RuntimeError("{} dependent arrow to nowhere".format((x,y)))

                if m in hits:
                    raise RuntimeError("{} dependent cycle".format(hits))
                hits.add(m)

                s = m, s
                n = m

            while s:
                n, s = s
                op = deps.node[n]['op']
                dh, dl = OP_[op.upper()]
                h, l = c
                c = (h+dh)%6, (l+dl)%3
            M[y][x] = HL_[c]

    im = Image.fromarray(M)
    im.save(filename)
                
def const(x):
    T = []
    if x < 0:
        op = 'SBT'
        x = -x
    else:
        op = 'ADD'
    while x:
        if x%2 == 1:
            T.append((2, 'MLT', 1, op))
        if x%2 == 0:
            T.append((2, 'MLT', 1, 'MLT'))

        x = x//2

    return sum(T[::-1], ((1, 'NOT')))

def rconst(x):
    ops = {2: '<psh <nop ',
           1: '<psh ',
           'SBT': '<sbt ',
           'NOT': '<not ',
           'ADD': '<add ',
           'MLT': '<mlt '}
    return ''.join(ops[op] for op in const(x))

def rconst_erase(x, val):
    ops = {2: val*2,
           1: val,
           'SBT': val,
           'NOT': val,
           'ADD': val,
           'MLT': val,}
    return ''.join(ops[op] for op in const(x))
    return ''.join(val for op in const(x))



def run(ops):
    vm = _PPVM()
    for o in ops:
        print vm.eval(o), vm.stack, o

def topbar(n_functions):
    halt = rconst(n_functions)
    _hlt = rconst_erase(n_functions, '     ')
    
    topleft = """ c00 <psh <not <psh <sbt <grt <swt <dpl {halt}<grt <swt {_hlt}vnop      
vptr      ^nop  ###           ^nop      {_hlt}     ^nop {halt} c00  ### 
>psh  c00 
 c00 """
    print topleft.format(halt=halt, _hlt=_hlt)
    return topleft.format(halt=halt, _hlt=_hlt)

if __name__ == '__main__':
    code = topbar(3)
    render(code, 'foo.png')


