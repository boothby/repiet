from pietbackend import _const
from itertools import chain
from optimizer import _PPVM
from heapdict import heapdict
import math
_ppvm = _PPVM()

from itertools import chain


def process_strategies(n, unfold_front = True):
    nopscore = lambda x: abs(x) + 3*(x <= 0) - (x == 0)

    queue = heapdict([((n,), (boundscore(n), 0))])
    bestscore = 2*abs(n)+2
    while queue:
        strat, (score, bound) = queue.popitem()
        if bound >= bestscore:
            continue
        elif score > boundscore(n) + 2:
            continue
        resolved = True
        for i in range(len(strat)):
            op = strat[i]
            if isinstance(op, int):
                score0 = score - boundscore(op)
                strati = strat[:i]
                istrat = strat[i+1:]
                base = None
                if resolved:
                    ops = sum(strati, ())
                    z = _PPVM(ops)
                    if z.stack:
                        base = z.stack[-1]
                resolved = False
                for substrat in get_strategies(op, base):
                    score1 = score0 + sum(len(o) if isinstance(o, tuple) else boundscore(o) for o in substrat)
                    bound1 = bound + sum(len(o) if isinstance(o, tuple) else 0 for o in substrat)
                    key = score1, bound1
                    if bound1 < bestscore and score1 <= boundscore(n) + 2:
                        ssi = strati + substrat + istrat
                        if key < queue.setdefault(ssi, key):
                            queue[ssi] = key

                if unfold_front:
                    break

        if resolved and True:
            bestscore = bound
            yield n, score, bound, sum(strat, ())
#        yield strat

        if resolved and False:
            bestscore = bound
            lq0 = len(queue)
            queue = heapdict(I for I in queue.items() if I[1][1] < bound)
            lq1 = len(queue)
            yield score, bound, queue.peekitem()[1] if lq1 else None, lq0, lq1, sum(strat, ())
#        yield strat
    

def boundscore(n, cache = {1:1, 0:2, -1:3}):
    if n in cache:
        return cache[n]

    minops = cache[n] = abs(n)+3
    for strat in get_strategies(n, None):
        ops = 0
        for m in strat:
            if isinstance(m, tuple):
                ops += len(m)
            elif abs(m) > abs(n):
                break
            else:
                ops += boundscore(m)
        else:
            minops = ops if minops is None else min(ops, minops)

    cache[n] = minops
    return minops


def bmp(n):
    if n > 0:
        yield n,
    elif n == 0:
        yield (1, 'NOT')
    else:
        yield (1, 'NOT', -n, 'SBT',)


def minimize(n, base=None, bound=None, cache = {(1, None):(1,), (0, None): (1, 'NOT'), (-1, None): (1, 1, 'NOT', 'SBT')}):
    if (n, base) in cache:
        return cache[n, base]
    if n is None:
        return cache

    if bound is None:
        bound = 3*abs(n)+3

    nopscore = lambda x: abs(x) + 3*(x <= 0) - (x == 0)
    getscore = lambda s: sum(nopscore(x) if isinstance(x, int) else 1 for x in s)
    if base is None:
        minops, = bmp(n)
    else:
        minops = minimize(n, None, bound//2)
        if minops is None:
            minops, = bmp(n)

    if bound < abs(n):
        return minops
    cache[n, base] = None
    print "?", minops, n, base
    bestscore = getscore(minops)

    strats = list(get_strats(n, base))

    for strat in strats:
        score = 0
        ops = ()
        print ">", strat, n, base
        for m in strat:
            if isinstance(m, str):
                ops += m,
                score += 1
            else:
                if ops:
                    if base is not None and ops[0] == 'DPL':
                        stk = _PPVM((base,) + ops[1:]).stack
                    else:
                        stk = _PPVM(ops).stack
                    top = stk[-1]
                    if len(stk) == 1 and top != n:
                        mops = minimize(top, None, bound//2)
                        if mops is not None:
                            mscore = getscore(mops)
                            if score < mscore:
                                if base is None:
                                    cache[top, None] = ops
                            else:
                                ops = mops
                                score = mscore
                else:
                    top=None
                print "!", n, m, top
                mm = minimize(m, top, bound//2)
                if mm is None:
                    mm, = bmp(m)
                score += getscore(mm)
                ops += mm

        bestscore, minops = min((score, ops), (bestscore, minops))

    cache[n, base] = minops
    return minops

def dpl_strats(n, base):
    #duplicate-and-go
    yield 'DPL', n-base, 'ADD',
    yield 'DPL', base-n, 'SBT1',
    if not base:
        pass
    elif not n%base:
        yield 'DPL', n//base, 'MLT'
    else:
        yield 'DPL', n//base, 'MLT', n%base, 'ADD'

def get_strats(n, base):
    #constant fudging
    for i in [1, 2, 3, 4, 8, 16]:
        yield i, i-n, 'SBT2'
        yield n+i, i, 'SBT3'
        yield i, n-i, 'ADD'
        if n%i==0:
            yield i, n//i, 'MLT'
            yield -i, -n//i, 'MLT'

    if n > 0:    
        #square-rooting
        z = int(n**.5)
        if z*z == n:
            yield z, 'DPL', 'MLT'
        else:
            yield z, 'DPL', 'MLT', n-z*z, 'ADD'
            if n > 2:
                yield z+1, 'DPL', 'MLT', (z+1)*(z+1) - n, 'SBT4'
                yield z, 'DPL', 1, 'ADD', 'MLT', z*(z+1) - n, 'SBT5'
                yield z, 'DPL', 1, 'ADD', 'MLT', n - z*(z+1), 'ADD'

    #duplicate-and-go
    if base is not None:
        for strat in dpl_strats(n, base):
            yield strat

    #halving
    if n%2:
        if n < 0:
            yield n//2, 'DPL', 1, 'SBT0', 'ADD'
        else:
            yield n//2, 'DPL', 1, 'ADD', 'ADD'
    else:
        yield n//2, 'DPL', 'ADD'

    #negating:
    yield 0, -n, 'SBT6',


def get_strategies(n, base):
    #constant fudging
    for i in [1, 2, 3, 4, 8, 16]:
        yield i, i-n, ('SBT2',)
        yield n+i, i, ('SBT3',)
        yield i, n-i, ('ADD',)
        if n%i==0:
            yield i, n//i, ('MLT',)
            yield -i, -n//i, ('MLT',)

    if n > 0:    
        #square-rooting
        z = int(n**.5)
        if z*z == n:
            yield z, ('DPL', 'MLT')
        else:
            yield z, ('DPL', 'MLT'), n-z*z, ('ADD',)
            if n > 2:
                yield z+1, ('DPL', 'MLT'), (z+1)*(z+1) - n, ('SBT4',)
                yield z, ('DPL', 1, 'ADD', 'MLT'), z*(z+1) - n, ('SBT5',)
                yield z, ('DPL', 1, 'ADD', 'MLT'), n - z*(z+1), ('ADD',)

    #duplicate-and-go
    if base is not None:
        for strat in dpl_strategies(n, base):
            yield strat

    #halving
    if n%2:
        if n < 0:
            yield n//2, ('DPL', 1, 'SBT0', 'ADD')
        else:
            yield n//2, ('DPL', 1, 'ADD', 'ADD')
    else:
        yield n//2, ('DPL', 'ADD')

    #negating:
    yield 0, -n, ('SBT6',)

#    if n > 0:    
#        #nopping
#        yield ('NOP',)*(n-1) + (n,),


def halve(n, do_const=False, cache = None):
    if n%2:
        if n < 0:
            yield optimize(n//2, do_const, cache) + ('DPL', 1, 'SBT', 'ADD')
        else:
            yield optimize(n//2, do_const, cache) + ('DPL', 1, 'ADD', 'ADD')
    else:
        yield optimize(n//2, do_const, cache) + ('DPL', 'ADD')

def neg(n, do_const=False, cache = None):
    yield optimize(0) + optimize(-n, do_const, cache) + ('SBT',)

def root(n, do_const=False, cache = None):
    z = int(n**.5)
    if z*z == n:
        yield optimize(z, do_const, cache) + ('DPL', 'MLT')

def const(n, do_const=False, cache = None):
    for i in range(1,17):
        yield optimize(i-n, False, cache) + optimize(i, False, cache) + ('SBT',)
        yield optimize(i, False, cache) + optimize(i+n, False, cache) + ('SBT',)
        yield optimize(i, False, cache) + optimize(n-i, False, cache) + ('ADD',)

def bump(n, do_const=False, cache = None):
    if n > 0:
        yield ('NOP',) * (n-1) + (n,)
    elif n == 0:
        yield (1, 'NOT')
    else:
        yield (1, 'NOT') + ('NOP',) * (abs(n)-1) + (abs(n),) + ('SBT',)

def optimize(n, do_const=True, cache = None):
    if cache is None:
        cache = {1:(1,), 0: (1, 'NOT'), -1: (1, 1, 'NOT', 'SBT')}

    if n in cache:
        return cache[n]

    strategies = []
    if n > 0:
        strategies.append(root)
    strategies.append(halve)
    if n < 0:
        strategies.append(neg)
    if do_const:
        strategies.append(const)
    strategies.append(bump)

    cache[n] = p = min(chain(*(s(n, do_const, cache) for s in strategies)), key=len)

    return p

def _grow(stack, ops):
    if stack[1]:
        a, stk = stack
        b, stk = stk
        yield (b+a, stk), ('ADD', ops)
        yield (b*a, stk), ('MLT', ops)
        yield (b-a, stk), ('SBT', ops)
    a, stk = stack
    if isinstance(ops[0], int):
        yield (a+1, stk), (a+1, ('NOP', ops[1]))    
    if a:
        yield (0, stk), ('NOT', ops)
    yield (a, stack), ('DPL', ops)
    yield (1, stack), (1, ops)

def supertree(levels):
    stack, ops = (1,()), (1,())
    instances = {stack:ops}
    for _ in range(levels):
        newinstances = {}
        for stack, ops in instances.items():
            for s, o in _grow(stack, ops):
                if s in newinstances:
                    if len(o) < len(newinstances[s]):
                        newinstances[s] = o
                elif s in instances:
                    if len(o) < len(instances[s]):
                        newinstances[s] = o
                else:
                    newinstances[s] = o

        instances.update(newinstances)
    
    flatten = lambda x, y: (flatten(*y)+(x,) if y else (x,))
    return {top: flatten(*v) for (top,stk), v in instances.items() if not stk}

def _addmul3(n, base):
    yield ('NOP',)*(n-1) + (n,)
    for i in range(1, (n+1)//2):
        if i > 2 and n%i == 0:
            yield addmul3(i, base) + addmul3(n//i, base) + ('MLT',)
        elif i > 2:
            yield addmul3(i, base) + addmul3(n//i, base) + ('MLT',) + addmul3(n%i, base) + ('ADD',)
    if n>1:
        if n%2:
            yield addmul3(n//2, base) + ('DPL', 'ADD', 1, 'ADD')
        else:
            yield addmul3(n//2, base) + ('DPL', 'ADD')
    if n>3 and base:
        if n%3:
            yield addmul3(3*(n//3), base) + addmul3(n%3, base) + ('ADD',)
        else:
            yield addmul3(n//3, base) + addmul3(3, base) +  ('MLT',) 
            yield addmul3(n//3, base) + ('DPL', 'DPL', 'ADD', 'ADD',)
    if n>4:
        if n%4:
            yield addmul3(4*(n//4), base) + addmul3(n%4, base) + ('ADD',)
        else:
            yield addmul3(n//4, base) + addmul3(4, base) +  ('MLT',) 
            yield addmul3(n//4, base) + ('DPL', 'ADD', 'DPL', 'ADD',)

    if n>1:
        z = int(n**.5)
        if z*z == n:
            yield addmul3(z, base) + ('DPL', 'MLT')
        z = int(n**.3333)
        if z*z*z == n:
            yield addmul3(z, base) + ('DPL', 'DPL', 'MLT', 'MLT')
        z = int(n**.25)
        if z*z*z*z == n:
            yield addmul3(z, base) + ('DPL', 'MLT', 'DPL', 'MLT')
        z = int(n**.2)
        if z*z*z*z*z == n:
            yield addmul3(z, base) + ('DPL', 'DPL', 'MLT', 'DPL', 'MLT', 'MLT')

def addmul3(n, base=1, cache={}):
    if (n, base) in cache:
        return cache[n, base]
    r = cache[n, base] = min(_addmul3(n, base), key=len)

    return r


if __name__ == '__main__':
    from optimizer import _PPVM
    ST = supertree(14)
    for i in range(1, 256):
    #    print i, len(addmul(i)), len(addmul2(i)), len(addmul3(i))#addmul(i), _PPVM(addmul(i)).stack
    #    if len(addmul3(i)):
#        if len(ST[i]) > len(ST[-i]):
#            _PPVM(ST[i])
            print i, ST[i], len(ST[i]), len(optimize(i))
#            _PPVM(ST[-i])
#            print -i, ST[-i], len(ST[-i]), len(optimize(-i))
#            print


