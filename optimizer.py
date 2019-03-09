from itertools import product
import networkx as nx
from parser import Parser

class Optimizer:
    def __init__(self, filename, backend):
        self._pars = pars = Parser(filename)
        self._parent = {}
        self._rank = {}
        self._block = {}
        self._backend = backend

        for p in product(range(pars.cols), range(pars.rows)):
            self._explore(p)
        for p in product(range(pars.cols), range(pars.rows)):
            r = self._find(p)
            if r == p:
                size = self._rank[r]
                self._block[p] = Block(p[0], p[1], size)

    def _explore(self, p):
        pars = self._pars
        x, y = p
        c = pars.matrix[y][x]
        if x < pars.cols-1 and c == pars.matrix[y][x+1]:
            self._union(p, (x+1, y))
        if y < pars.rows-1 and c == pars.matrix[y+1][x]:
            self._union(p, (x, y+1))        

    def _union(self, p0, p1):
        r0 = self._find(p0)
        r1 = self._find(p1)
        if r0 == r1:
            return
        if r1 == (0,0) or self._rank[r0] < self._rank[r1]:
            self._parent[r0] = r1
            self._rank[r1] += self._rank[r0]
        else:
            self._parent[r1] = r0
            self._rank[r0] += self._rank[r1]

    def _find(self, p0):
        try:
            p = self._parent[p0]
        except KeyError:
            self._parent[p0] = p0
            self._rank[p0] = 1
            return p0
        if p != p0:
            p = self._parent[p0] = self._find(p)
        return p

    def get_block(self, p):
        r = self._find(p)
        return self._block[r]

    def step(self, dp, cc, block):
        pars = self._pars
        pars.x = block.x
        pars.y = block.y
        pars.cc = [-1,1][cc]
        pars.dp = dp
        instruction = pars.step()

        if instruction is None:
            return None, None, None, None, None

        c = self.get_block((pars.x, pars.y))

        return instruction, pars.dp, max(0,pars.cc), c.x, c.y

    def block_neighbors(self, block):
        for dp in range(4):
            for cc in 0,1:
                i, next_dp, next_cc, x, y = self.step(dp, cc, block)
                if i is not None:
                    yield dp, cc, i, next_dp, next_cc, x, y

    def optimize_dep(self, x0, y0, dp0, cc0):
        backend = self._backend
        code = ""
        x,y,dp,cc = x0,y0,dp0,cc0
        block = self._block[x,y]
        i, ndp, ncc, nx, ny = self.step(dp, cc, block)

        next = nx, ny, ndp, ncc
        vm = PPVM(dp, cc)
        cycledetect = {(x,y,dp,cc)}
        while i is not None and vm.eval(i, block.size):
            x, y, dp, cc = next
            block = self._block[x,y]
            print(cc)
            i, ndp, ncc, nx, ny = self.step(dp, cc, block)
            next = nx, ny, ndp, ncc
            if next in cycledetect:
                break
            else:
                cycledetect.add(next)

        if vm.outputs:
            code += backend.print_str("".join(vm.outputs))
        if vm.stack:
            code += backend.push_stack(vm.stack)

        return backend.compile_dep(x,y,dp,cc, prepend=code), nx, ny, ndp, ncc

    def collect_deps(self, block, deps):
        for dp, cc, i, next_dp, next_cc, x, y in self.block_neighbors(block):
            CC = [0,1] if i == 'SWT' else [next_cc]
            DP = [0,1,2,3] if i == 'PTR' else [next_dp]
            for ndp in DP:
                for ncc in CC:
                    code, nx, ny, ndp, ncc = self.optimize_dep(block.x, block.y, dp, cc)
                    deps.add_edge((block.x, block.y, dp, cc), (nx, ny, ndp, ncc), code=code)

    def compile(self, filename = None):
        parsed = nx.DiGraph()
        code = []
        skip = ('0xffffff', '0x000000')
        for block in self._block.values():
            if self._pars.matrix[block.y][block.x] not in skip:
                self.collect_deps2(block, parsed)

        deps = {(0,0,0,0)}
        for u, v in nx.traversal.depth_first_search.dfs_edges(parsed, (0,0,0,0)):
            x,y,dp,cc = v
            code.append(parsed[u][v]['code'])
            deps.add((x,y,dp,cc))

        code = "\n".join(code)
        if filename is None:
            return code
        else:
            self._backend.wrapup(code, filename)


def _check(n):
    def dec(f):
        def _(self):
            if len(self.stack) < n:
                return False
            args = [self.stack.pop() for _ in range(n)]
            res = f(self, *args)
            if res is not None:
                self.stack.append(res)
            return True
        return _
    return dec
        
class PPVM(object):
    """~~~~~~~~~~ Proving Piet Virtual Machine ~~~~~~~~~
    Just like a Piet virtual machine, but buffers output
    and stops on popping an empty stack or reading input
    This is used for static analysis; provable code is 
    """

    def __init__(self, dp, cc):
        self.dp = dp
        self.cc = cc
        self.stack = []
        self.outputs = []

    def eval(self, f, size):
        self.size = size
        return self.__getattribute__(f)()

    def NOP(self): return True

    @_check(0)
    def PSH(self): return self.size

    @_check(1)
    def POP(self, a): return

    @_check(2)
    def ADD(self, a, b): return b + a

    @_check(2)
    def SBT(self, a, b): return b - a

    @_check(2)
    def MLT(self, a, b): return b * a

    @_check(2)
    def DVD(self, a, b): return b // a

    @_check(2)
    def MOD(self, a, b): return b % a

    @_check(1)
    def NOT(self, a): return int(not a)

    @_check(2)
    def GRT(self, a, b): return b > a

    @_check(1)
    def PTR(self, a): self.dp = (self.dp + a) % 4

    @_check(1)
    def SWT(self, a): self.cc ^= bool(a);

    @_check(1)
    def DPL(self, a): self.stack.append(a); return a

    @_check(2)
    def RLL(self, a, b):
        a %= b
        if not (b <= 0 or a == 0):
            z = -abs(a) + b * (a < 0)
            self.stack[-b:] = self.stack[z:] + self.stack[-b:z]

    def DIN(self): return False

    def CIN(self): return False

    @_check(1)
    def DUT(self, a): self.outputs.append(str(a))

    @_check(1)
    def CUT(self, a): self.outputs.append(chr(a))


