import numpy as np
from parser import OP
from lexer import HL
from backends import backend
from itertools import chain

base = np.array((0xc0, 0, 0xc0), np.uint8)
operate = np.array((0, 0xc0, 0), np.uint8)
block = np.array((0, 0, 0), np.uint8)
slide = np.array((0xff, 0xff, 0xff), np.uint8)
okblock = np.array((0xc0, 0xc0, 0xc0), np.uint8)


if False:
    base = (5,1)
    baseop = (5,0)
    operate = (2, 1)
    block = (6, 0)
    slide = (6, 1)

    base = 'red'
    operate = 'yes'
    block = '###'
    slide = '   '

    okblock = 'zzz'


OP_ = { op : (dh, dl)
            for dh, row in enumerate(OP)
            for dl, op in enumerate(row)}

HL_ = {v: k for k, v in HL.items()}

def progline(ops, maxlen):
    h = l = 0
    curlen = 0
    yield HL_[h, l]
    for op in ops:
        if isinstance(op, int):
            if op == 1:
               op = 'PSH'
            else:
                raise(ValueError, "progline does not handle PSH(n) for n != 1 -- you can encode greater values with NOPs")
        dh, dl = OP_[op]
        h = (h+dh)%6
        l = (l-dl)%3
        yield HL_[h, l]
        curlen += 1
    for nop in range(curlen, maxlen):
        yield slide 
    
def jmpline0(ops, maxlen):
    yield block
    for op in range(maxlen):
        yield okblock

def jmpline1(ops, maxlen):
    return progline(ops, maxlen)

def jmpline2(ops, maxlen):
    yield slide
    for _ in range(maxlen):
        yield okblock

def jmpline3(ops, maxlen):
    for _ in range(maxlen+1):
        yield slide


def routing_top(n, of_n):
    if n == 0:
        for i in range(of_n):
            yield slide
            yield okblock
        yield slide
        yield block
    else:
        for i in range(n-1):
            yield slide
            yield okblock
        yield slide
        yield block
        yield slide
        yield block
        for i in range(of_n - n - 1):
            yield slide
            yield okblock
        yield slide
        yield block

def routing_mid(n, of_n):
    if n == 0:
        yield slide
        yield block
        for i in range(of_n-1):
            yield slide
            yield block
        yield slide
        yield slide
    else:
        for i in range(2*n-1):
            yield slide
        yield 0, 0
        yield 0, 0
        yield 0, 0
        for i in range(2*(of_n - n)):
            yield slide

def routing_bottom(n, of_n):
    if n == 0:
        for i in range(of_n + 1):
            yield slide
            yield okblock
    else:
        for i in range(n):
            yield slide
            yield okblock
        yield 0, 0
        for i in range(of_n - n):
            yield okblock
            yield slide
        yield block

def routing_jmp(n, of_n):
    for i in range(2*n):
        yield slide
    yield slide
    yield block
    for i in range(2*(of_n - n)):
        yield slide

def swtline0(ops, maxlen):
    return jmpline0(ops, maxlen)

def swtline1(ops, maxlen):
    return jmpline1(ops, maxlen)

def swtline2(ops, maxlen):
    l_c = None
    ll_c = None
    which = slide
    for c in progline(ops, len(ops)):
        if ll_c is not None:
            yield which
            which = okblock
        ll_c = l_c
        l_c = c
    #len(ops)
    yield ll_c 
    yield l_c
    #len(ops)+2
    for _ in range(len(ops), maxlen):
        yield slide
    
    
def swtline3(ops, maxlen):
    l_c = None
    ll_c = None
    which = slide
    for c in progline(ops, len(ops)):
        if ll_c is not None:
            yield which
            which = okblock
        ll_c = l_c
        l_c = c
    #len(ops)
    yield ll_c
    yield block
    #len(ops)+2
    for _ in range(len(ops), maxlen):
        yield okblock

def swtline4(ops, maxlen):
    return jmpline3(ops, maxlen)

def ptrline0(ops, maxlen):
    yield block
    off = max(1, len(ops)-1)
    for _ in range(1, off+2):
        yield okblock

    yield block
    for _ in range(off+2, maxlen):
        yield okblock


def ptrline1(ops, maxlen):
    if len(ops) == 1:
        off = 2
        yield (0, 0)
        yield slide
    else:
        off = len(ops)
        for c in progline(ops[:-1], len(ops)-1):
            yield c
    yield block
    yield slide
    yield slide
    yield 0, 0
    for _ in range(off, maxlen-3):
        yield slide
    

def ptrline2(ops, maxlen):
    yield slide
    off = max(1, len(ops)-1)
    for _ in range(1, off):
        yield okblock
    yield slide
    yield okblock
    yield 3, 1
    yield block
    yield 0, 0
    for _ in range(off+4, maxlen):
        yield slide

def ptrline3(ops, maxlen):
    yield slide
    off = max(2, len(ops))
    for _ in range(2, off):
        yield okblock

    yield 3, 1
    yield 3, 1
    yield 3, 1

    yield 0, 0
    yield slide
    for _ in range(off+3, maxlen):
        yield slide

def ptrline4(ops, maxlen):
    yield slide
    off = max(2, len(ops))
    for _ in range(2, off):
        yield okblock
    yield block
    yield slide
    yield 0, 0
    yield 0, 0
    yield slide
    for _ in range(off+3, maxlen):
        yield slide

def ptrline5(ops, maxlen):
    yield slide
    off = max(2, len(ops))
    for _ in range(2, off+2):
        yield okblock

    yield block
    yield block
    yield okblock
    for _ in range(off+3, maxlen):
        yield okblock

def ptrline6(ops, maxlen):
    return jmpline3(ops, maxlen)

def lastline(maxlen):
    for _ in range(maxlen+1):
        yield slide


class pietbackend(backend):
    def join_instructions(self, strux):
        return sum(strux, ())

    def define(self, name, ops, dest):
        return (name, ops, dest)
    
    def join_defs(self, defs):
        return defs

    def push(self, i):
        return _const(i)

    def pointer(self, options):
        return options,

    def switch(self, options):
        return options,

    def instruction(self, i):
        if isinstance(i, int):
            return _const(i)
        else:
            return i,


    def render(self, defs, start):
        if start is None:
            return "P1 1 1 0"

        def_id = {}
        defs_1 = []
        maxlen = 0
        for name, ops, dest in defs:
            did = def_id.setdefault(name, len(def_id))
            kind = 'jmp'
            deflen = len(ops)
            if ops and dest is None:
                end = ops[-1]
                if isinstance(end, tuple):
                    dest = end
                    if len(end) == 2:
                        ops = ops[:-1] + ('SWT',)
                        kind = 'swt'
                    elif len(end) == 4:
                        ops = ops[:-1] + ('PTR',)
                        deflen += 4
                        kind = 'ptr'
                    else:
                        raise ValueError("bad switch/pointer list")
            maxlen = max(maxlen, deflen)
            defs_1.append((did, kind, ops, dest, name))
        defs = defs_1
        n_defs = len(defs)
        start_id  = def_id[start]

        chunks = []
        rows = 0
        for i in chain(range(start_id, len(defs)), range(start_id)):
            did, kind, ops, dest, name = defs[i]
            did = (start_id-i-1)%n_defs

            if dest is None:
                dest = n_defs
            elif isinstance(dest, tuple):
                dests = tuple((start_id-def_id[d]-1)%n_defs for d in dest)
            else:
                dest = (start_id-def_id[dest]-1)%n_defs
            if kind == 'jmp':
                if i != start_id:
                    rows += 1
                    chunks.append(jmpline0(ops, maxlen))
                    chunks.append(routing_bottom((did+1)%n_defs, n_defs))

                rows += 1
                chunks.append(jmpline1(ops, maxlen))
                chunks.append(routing_jmp(dest, n_defs))

                rows += 1
                chunks.append(jmpline2(ops, maxlen))
                chunks.append(routing_top(did, n_defs))

                if did != 0:
                    rows += 1
                    chunks.append(jmpline3(ops, maxlen))
                    chunks.append(routing_mid(did, n_defs))
                
            elif kind == 'swt':
                if i != start_id:
                    rows += 1
                    chunks.append(swtline0(ops, maxlen))
                    chunks.append(routing_bottom((did+1)%n_defs, n_defs))

                rows += 1
                chunks.append(swtline1(ops, maxlen))
                chunks.append(routing_jmp(dests[0], n_defs))

                rows += 1
                chunks.append(swtline2(ops, maxlen))
                chunks.append(routing_jmp(dests[1], n_defs))

                rows += 1
                chunks.append(swtline3(ops, maxlen))
                chunks.append(routing_top(did, n_defs))

                if did != 0:
                    rows += 1
                    chunks.append(swtline4(ops, maxlen))
                    chunks.append(routing_mid(did, n_defs))

            elif kind == 'ptr':
                if i != start_id:
                    rows += 1
                    chunks.append(ptrline0(ops, maxlen))
                    chunks.append(routing_bottom((did+1)%n_defs, n_defs))

                rows += 1
                chunks.append(ptrline1(ops, maxlen))
                chunks.append(routing_jmp(dests[1], n_defs))

                rows += 1
                chunks.append(ptrline2(ops, maxlen))
                chunks.append(routing_jmp(dests[0], n_defs))

                rows += 1
                chunks.append(ptrline3(ops, maxlen))
                chunks.append(routing_jmp(dests[3], n_defs))

                rows += 1
                chunks.append(ptrline4(ops, maxlen))
                chunks.append(routing_jmp(dests[2], n_defs))

                rows += 1
                chunks.append(ptrline5(ops, maxlen))
                chunks.append(routing_top(did, n_defs))
                if did != 0:
                    rows += 1
                    chunks.append(ptrline6(ops, maxlen))
                    chunks.append(routing_mid(did, n_defs))

            if did == 0:
                rows += 1
                chunks.append(lastline(maxlen))
                chunks.append(routing_mid(did, n_defs))

                cols = len(list(lastline(maxlen))) + len(list(routing_mid(did, n_defs)))

        return b"".join((b"P6\n%d %d\n255\n"%(cols, rows), bytes(z for c in chunks for p in c for z in (p if len(p) == 3 else HL_[p]))))

    def execute(self, filename, capture_output=False):
        args = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE) if capture_output else {}
        prog = subprocess.run("python {}".format(filename), *args, shell=True)
        if capture_output:
            return prog.stdout, prog.stderr







def _const(x):
    T = []
    if x == 1:
        return 1,
    elif x == 0:
        return 1, 'NOT'
    elif x < 0:
        op = 'SBT'
        x = -x
    else:
        op = 'ADD'

    while x:
        if x == 1:
            if op == 'SBT':
                T.append((1, 'NOT', 1, op))
            else:
                T.append((1,))
        elif x == 0:
            T.append((1, 'NOT'))
  
        elif x%2:
            T.append(('DPL', 'ADD', 1, op))
        else:
            T.append(('DPL', 'ADD'))
        x = x//2

    return sum(T[::-1], ())


if __name__=='__main__':
    import compiler, sys
    with open("aaab.ppm", 'wb') as f:f.write(compiler.Compile('../tests/pointer%s.png'%sys.argv[1], 'piet', optimization_level=0))
    print(compiler.Compile('aaab.ppm', 'py', optimization_level=0))

