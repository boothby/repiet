from pietbackend import _const
from itertools import chain
from optimizer import _PPVM
_ppvm = _PPVM()

from itertools import chain
def halve(n):
    if n%2:
        if n < 0:
            yield optimize(n//2) + ('DPL', 1, 'SBT', 'ADD')
        else:
            yield optimize(n//2) + ('DPL', 1, 'ADD', 'ADD')
    else:
        yield optimize(n//2) + ('DPL', 'ADD')

def neg(n):
    yield optimize(0) + optimize(-n) + ('SBT',)

def root(n):
    z = int(n**.5)
    if z*z == n:
        yield optimize(z) + ('DPL', 'MLT')
    else:
        yield optimize(z) + ('DPL', 'MLT') + optimize(n-z*z) + ('ADD',)
        if n > 2:
            yield optimize(z+1) + ('DPL', 'MLT') + optimize((z+1)*(z+1) - n) + ('SBT',)

def bump(n):
    yield ('NOP',) * (n-1) + (n,)

def optimize(n, cache = {1:(1,), 0: (1, 'NOT'), -1: (1, 1, 'NOT', 'SBT')}):
    if n in cache:
        return cache[n]

    if n < 0:
        cache[n] = p = min(chain(halve(n), neg(n)), key=len)
    else:
        cache[n] = p = min(chain(halve(n), root(n), bump(n)), key=len)
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



from optimizer import _PPVM
ST = supertree(14)
for i in range(1, 256):
#    print i, len(addmul(i)), len(addmul2(i)), len(addmul3(i))#addmul(i), _PPVM(addmul(i)).stack
#    if len(addmul3(i)):
        print i,
        print [i] == _PPVM(ST[i]).stack,
#        print addmul3(i)
        print len(optimize(i)), len(ST[i]),
        print len(addmul3(i)),  ST[i]
        
