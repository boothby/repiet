import numpy as np

base = np.array((0xc0, 0, 0xc0), np.uint8)
operate = np.array((0, 0xc0, 0), np.uint8)
block = np.array((0, 0, 0), np.uint8)
slide = np.array((0xff, 0xff, 0xff), np.uint8)


base = (5,1)
baseop = (5,0)
operate = (2, 1)
block = (6, 0)
slide = (6, 1)

base = 'red'
operate = 'yes'
block = '###'
slide = '   '

okblock = block
okblock = 'zzz'


def progline(ops, maxlen):
    h = l = 0
    curlen = 0
    yield (h, l)
    for op in ops:
        if isinstance(op, int):
            if op == 1:
               op = 'PSH'
            else:
                raise(ValueError, "progline does not handle PSH(n) for n != 1 -- you can encode greater values with NOPs")
        dh, dl = OP_[op]
        h = (h+dh)%6
        l = (l-dl)%3
        yield h, l
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
    for nop in ops:
        return okblock

def jmpline3(ops, maxlen):
    yield 0, 0
    for nop in ops:
        return slide


def routing_top(n, of_n):
    if n == 0:
        for i in range(2*of_n - 1):
            yield slide
        yield block
    else:
        for i in range(2*n-1):
            yield slide
        yield block
        yield slide
        yield block
        for i in range(2*(of_n - n) - 1)
            yield slide
        yield block

def routing_mid(n, of_n):
    if n == 0:
        yield 0, 0
        yield block
        for i in range(of_n-1):
            yield slide
            yield block
    else:
        for i in range(2*n-1):
            yield slide
        yield 0, 0
        yield 0, 0
        yield 0, 0
        for i in range(2*(of_n - n))
            yield slide

def routing_bottom(n, of_n):
    if n == 0:
        raise RuntimeError("zeroth routing bottom should be off-canvas")
    else:
        for i in range(2*n-1):
            yield slide
        yield slide
        yield 0, 0
        yield slide
        for i in range(2*(of_n - n) - 1)
            yield slide
        yield block

def routing_jmp(n, of_n):
    for i in range(2*(n-1)):
        yield slide
    yield slide
    yield block
    for i in range(2*(of_n - n)):
        yield slide

def swtline0(ops, maxlen):
    return jmpline0(ops, maxlen)

def swtline1(ops, maxlen):
    return jmpline1(ops, maxlen)

def swtline2(ops, maxlen)
    l_c = None
    ll_c = None
    for c in progline(ops, len(ops)):
        ll_c = l_c
        l_c = c
        yield okblock
    yield ll_c
    yield l_c
    
def swtline3(ops, maxlen)
    l_c = None
    ll_c = None
    for c in progline(ops, len(ops)):
        ll_c = l_c
        l_c = c
        yield okblock
    yield ll_c
    yield block

def swtline4(ops, maxlen):
    return jmpline3(ops, maxlen)

def ptrline0(ops, maxlen):
    yield block
    for op in range(maxlen-3):
        yield okblock
    yield block
    yield okblock
    yield okblock

def ptrline1(ops, maxlen):
    for c in progline(ops[:-1], maxlen-4):
        yield c
    yield block
    yield slide
    yield slide
    yield 0, 0

def ptrline2(ops, maxlen):
    for c in progline(ops[:-1], len(ops)-2):
        yield okblock
    yield slide
    yield okblock
    yield 2, 1
    yield block
    yield 0, 0

def ptrline3(ops, maxlen):
    for c in progline(ops[:-1], len(ops)-2):
        yield okblock
    yield 2, 1
    yield 2, 1
    yield 2, 1
    yield 0, 0
    yield slide
    
def ptrline3(ops, maxlen):
    for c in progline(ops[:-1], len(ops)-2):
        yield okblock
    yield block
    yield slide
    yield 0, 0
    yield 0, 0
    yield slide

def ptrline4(ops, maxlen):
    for c in progline(ops[:-1], len(ops)-2):
        yield okblock
    yield okblock
    yield okblock
    yield block
    yield block
    yield okblock

def ptrline5(ops, maxlen):
    return jmpline3(ops, maxlen)

def lastline(maxlen):
    yield 0, 0
    for nop in range(maxlen-1):
        yield slide
    yield 0, 0


