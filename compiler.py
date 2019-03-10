from itertools import product
import networkx as nx
from parser import Parser
from collections import namedtuple

Block = namedtuple('block', ['x','y','size'])

class Compiler:
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


    def step(self, x, y, d, c):
        pars = self._pars
        pars.x = x
        pars.y = y
        pars.cc = [-1,1][c]
        pars.dp = d
        instruction = pars.step()

        if instruction is None:
            return None, None, None, None, None

        c = self.get_block((pars.x, pars.y))

        return instruction, c.x, c.y, pars.dp, max(0,pars.cc)

    def block_neighbors(self, block):
        for d in range(4):
            for c in 0,1:
                i, n_x, n_y, n_d, n_c= self.step(block.x, block.y, d, c)
                if i is not None:
                    yield d, c, i, n_x, n_y, n_d, n_c

    def collect_deps(self, block, deps):
        for d, c, i, n_x, n_y, n_d, n_c in self.block_neighbors(block):
            CC = [0,1] if i == 'SWT' else [n_c]
            DP = [0,1,2,3] if i == 'PTR' else [n_d]
            for n_d in DP:
                for n_c in CC:
                    deps.add_edge((block.x, block.y, d, c), (n_x, n_y, n_d, n_c), instruction=i)

    def compile_dep(self, x, y, d, c):
        block = self._block[x,y]
        i, n_x, n_y, n_d, n_c = self.step(block.x, block.y, d, c)
        return self._backend.compile_dep((x, y, d, c), (n_x, n_y, n_d, n_c), i, block.size)


    def compile(self, filename = None):
        parsed = nx.DiGraph()
        code = []
        skip = ('0xffffff', '0x000000')
        for block in self._block.values():
            if self._pars.matrix[block.y][block.x] not in skip:
                self.collect_deps(block, parsed)

        f_i, f_x, f_y, f_d, f_c = self.step(0,0,0,0)

        if f_i is not None:
            first = (f_x, f_y, f_d, f_c) if f_i == 'NOP' else (0,0,0,0)
            deps = {first}            
            for u, v in nx.traversal.depth_first_search.dfs_edges(parsed, first):
                x,y,d,c = v
                i = parsed[u][v]['instruction']
                deps.add((x,y,d,c))

            for (x,y,d,c) in deps:
                defn = self.compile_dep(x,y,d,c)
                code.append(defn)
        else:
            first = None
        code = "\n".join(code)

        return self._backend.assemble(code, first, filename)


