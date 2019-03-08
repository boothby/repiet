from collections import namedtuple
from itertools import product
from PIL import Image
from operator import itemgetter
import sys
import networkx as nx



Block = namedtuple('block', ['x','y','size'])
Color = namedtuple('color', ['color','abbv','hue','dark'])


class cppbackend:
    def __init__(self, compiler):
        self.compiler = compiler


    command = {
        "NOP" : "",
        "PSH" : "psh(a);",
        "POP" : "pop(a);",
        "ADD" : "if (pop(a, b)) psh(a+b);",
        "SBT" : "if (pop(a, b)) psh(a-b);",
        "MLT" : "if (pop(a, b)) psh(a*b);",
        "DVD" : "if (pop(a, b) && b) psh(a/b);",
        "MOD" : "if (pop(a, b) && b) psh(a-b*(a/b));",
        "NOT" : "if (pop(a)) psh(!a);",
        "GRT" : "if (pop(a, b)) psh(a>b);",
        "PTR" : "if (pop(a)) ((dp + a)%4+4)%4;",
        "SWT" : "if (pop(a)) cc^=a&1;",
        "DPL" : "if (pop(a)) { psh(a); psh(a); }",
        "RLL" : "if (pop(a, b)) rll(a, b);",
        "DIN" : "cin >> a; if(good(cin)) psh(a);",
        "CIN" : "cin >> A; if(good(cin)) psh(A);",
        "DUT" : "if (pop(a)) cout << a;",
        "CUT" : "if (pop(A)) cout << A;",
    }

    def compile_dep(self, x, y, dp, cc):
        block = self.compiler._block[x,y]
        i, ndp, ncc, nx, ny = self.compiler.step(dp, cc, block)
        if i is None:
            return "c_%d_%d_%d_%d: return;"%(x,y,dp,cc)
        elif i == 'PTR':
            return """
c_%d_%d_%d_%d:
if (pop(a)) {
    switch((a%%4+4)%%4) {
        case 1: goto c_%d_%d_%d_%d;
        case 2: goto c_%d_%d_%d_%d;
        case 3: goto c_%d_%d_%d_%d;
    }
} goto c_%d_%d_%d_%d;
            """%(
                x,y,dp,cc,
                nx,ny,(ndp+1)%4,ncc,
                nx,ny,(ndp+2)%4,ncc,
                nx,ny,(ndp+3)%4,ncc,
                nx,ny,ndp,ncc,
            )
        elif i == 'SWT':
            return "c_%d_%d_%d_%d: if (pop(a) && a&1) goto c_%d_%d_%d_%d; goto c_%d_%d_%d_%d;"%(
                x,y,dp,cc,
                nx,ny,ndp,1-ncc,
                nx,ny,ndp,ncc,
            )
        elif i == 'PSH':
            return "c_%d_%d_%d_%d: psh(%d); goto c_%d_%d_%d_%d;"%(
                    x,y,dp,cc, block.size, nx, ny, ndp, ncc)
        else:
            return "c_%d_%d_%d_%d: %s goto c_%d_%d_%d_%d;"%(
                    x,y,dp,cc, self.command[i], nx, ny, ndp, ncc)

def _pyformat(f):
    def _(self, x,y,dp,cc, prepend=""):
        return "    def c_%d_%d_%d_%d(): %s%s"%(x,y,dp,cc, prepend, f(self, x,y,dp,cc))
        return "    def c_%d_%d_%d_%d(): print(%d,%d,%d,%d, stack); %s%s"%(x,y,dp,cc, x,y,dp,cc, prepend, f(self, x,y,dp,cc))
    return _

class pybackend:
    def __init__(self, compiler):
        self.compiler = compiler

    command = {
        "NOP" : "",
        "POP" : "pop();",
        "ADD" : "a,b = pop2(); a is not None and psh(b+a);",
        "SBT" : "a,b = pop2(); a is not None and psh(b-a);",
        "MLT" : "a,b = pop2(); a is not None and psh(b*a);",
        "DVD" : "a,b = pop2(); a is not None and a!=0 and psh(b//a);",
        "MOD" : "a,b = pop2(); a is not None and a!=0 and psh(b%a);",
        "NOT" : "a = pop(); a is not None and psh(int(not a));",
        "GRT" : "a,b = pop2(); a is not None and psh(int(b>a));",
        "PTR" : "a = pop(); dp = (4 + (dp + (a is not None and a))%4)%4;",
        "SWT" : "a = pop(); cc ^= (a is not None and a)&1;",
        "DPL" : "a = pop();  a is not None and psh(a,a);",
        "RLL" : "a,b = pop2(); a is not None and rll(a,b);",
        "DIN" : "a = psh(int(input()));",
        "CIN" : "a = input(); psh(ord(a));",
        "DUT" : "a = pop(); a is not None and print(a, sep='', end='', flush=1);",
        "CUT" : "a = pop(); a is not None and print(chr(max(0,min(255,a))), sep='', end='', flush=1);",
    }


    @_pyformat
    def compile_dep(self, x, y, dp, cc):
        block = self.compiler._block[x,y]
        i, ndp, ncc, nx, ny = self.compiler.step(dp, cc, block)
        if i is None:
            return "return None";
        elif i == 'PTR':
            options = [(nx,ny,ndp,ncc), 
                       (nx,ny,(ndp+1)%4,ncc),
                       (nx,ny,(ndp+2)%4,ncc),
                       (nx,ny,(ndp+3)%4,ncc)]
            options = ["c_%d_%d_%d_%d"%o for o in options]
            return "a = pop(); return [{}][0 if a is None else (a%4+4)%4]".format(', '.join(options))
        elif i == 'SWT':
            options = [(nx,ny,ndp,ncc),
                       (nx,ny,ndp,1-ncc)]
            options = ["c_%d_%d_%d_%d"%o for o in options]
            return "a = pop(); return [{}][1 if a is None else a&1]".format(', '.join(options))
        elif i == 'PSH':
            return "psh({}); return c_{}_{}_{}_{}".format(block.size, nx, ny, ndp, ncc)
        else:
            return "{} return c_{}_{}_{}_{}".format(self.command[i], nx, ny, ndp, ncc)


    def print_str(self, x):
        return "".join(("print(",x,");"))

    def push_stack(self, x):
        return "stack.extend(%r);"%x 

    def wrapup(self, code, filename):
        with open("pypiet.py", 'r') as f:
            template = f.read()
            program = template.replace("%%%DEFN%%%", code)
            with open(filename, 'w') as g:
                g.write(program)
        

class Compiler:
    def __init__(self, filename, backend='c++'):
        self._pars = pars = Parser(filename)
        self._parent = {}
        self._rank = {}
        self._block = {}
        if backend == 'c++':
            self._backend = cppbackend(self)
        elif backend == 'python':
            self._backend = pybackend(self)

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

    def collect_deps(self, block, deps):
        for dp, cc, i, next_dp, next_cc, x, y in self.block_neighbors(block):
            CC = [0,1] if i == 'SWT' else [next_cc]
            DP = [0,1,2,3] if i == 'PTR' else [next_dp]
            for ndp in DP:
                for ncc in CC:
                    deps.add_edge((block.x, block.y, dp, cc), (x, y, ndp, ncc), instruction=i)

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

    def compile(self, filename = None):
        parsed = nx.DiGraph()
        code = []
        skip = ('0xffffff', '0x000000')
        for block in self._block.values():
            if self._pars.matrix[block.y][block.x] not in skip:
                self.collect_deps(block, parsed)

        deps = {(0,0,0,0)}
        for u, v in nx.traversal.depth_first_search.dfs_edges(parsed, (0,0,0,0)):
            x,y,dp,cc = v
            i = parsed[u][v]['instruction']
            deps.add((x,y,dp,cc))

        for (x,y,dp,cc) in deps:
            defn = self._backend.compile_dep(x,y,dp,cc)
            code.append(defn)

        code = "\n".join(code)
        if filename is None:
            return code
        else:
            self._backend.wrapup(code, filename)

    def collect_deps2(self, block, deps):
        for dp, cc, i, next_dp, next_cc, x, y in self.block_neighbors(block):
            CC = [0,1] if i == 'SWT' else [next_cc]
            DP = [0,1,2,3] if i == 'PTR' else [next_dp]
            for ndp in DP:
                for ncc in CC:
                    code, nx, ny, ndp, ncc = self.optimize_dep(block.x, block.y, dp, cc)
                    deps.add_edge((block.x, block.y, dp, cc), (nx, ny, ndp, ncc), code=code)

    def compile2(self, filename = None):
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


class Parser:
    ##Stolen from http://www.dangermouse.net/esoteric/piet/Piet_py.txt
    #  Author- Ross Tucker
    #  Thanks to Marc Majcher for his project, Piet.pl
    #  Modified by Kelly Boothby to emit instructions instead of immediately executing them

    HEX_BLACK = '0x000000'
    HEX_WHITE = '0xffffff'

    do_arr = [["NOP", "PSH", "POP"],
              ["ADD", "SBT", "MLT"],
              ["DVD", "MOD", "NOT"],
              ["GRT", "PTR", "SWT"],
              ["DPL", "RLL", "DIN"],
              ["CIN", "DUT", "CUT"]]

    hex2tuple = {
        '0xffc0c0':Color('light red',    'lR',0, 0),                            
        '0xffffc0':Color('light yellow', 'lY',1, 0),                            
        '0xc0ffc0':Color('light green',  'lG',2, 0),                            
        '0xc0ffff':Color('light cyan',   'lC',3, 0),                            
        '0xc0c0ff':Color('light blue',   'lB',4, 0),                            
        '0xffc0ff':Color('light magenta','lM',5, 0),                            
        '0xff0000':Color('red',          ' R',0, 1),                            
        '0xffff00':Color('yellow',       ' Y',1, 1),                            
        '0x00ff00':Color('green',        ' G',2, 1),                            
        '0x00ffff':Color('cyan',         ' C',3, 1),                            
        '0x0000ff':Color('blue',         ' B',4, 1),                            
        '0xff00ff':Color('magenta',      ' M',5, 1),                            
        '0xc00000':Color('dark red',     'dR',0, 2),                            
        '0xc0c000':Color('dark yellow',  'dY',1, 2),                            
        '0x00c000':Color('dark green',   'dG',2, 2),                            
        '0x00c0c0':Color('dark cyan',    'dC',3, 2),                            
        '0x0000c0':Color('dark blue',    'dB',4, 2),                            
        '0xc000c0':Color('dark magenta', 'dM',5, 2),                            
        '0xffffff':Color('white',        'Wt',-1,-1),                            
        '0x000000':Color('black',        'Bk',-1,-1)
    }

    def __init__(self, filename):
        self.x, self.y = 0, 0
        self.dp = 0
        self.cc = -1
        self.debug = 0
        self.step_number = 1
        self.block = (0,0)
        self.filename = filename
        self._image = Image.open(self.filename).convert("RGB")
        self.cols, self.rows = self._image.size
        self.matrix = [[0 for x in range(self.cols)] \
                        for y in range(self.rows)]

        for j in range(self.rows):
            for i in range(self.cols):
                r,g,b = self._image.getpixel((i,j))
                rgb = "0x%02x%02x%02x" % (r,g,b)
                if rgb not in self.hex2tuple:
                    rgb = self.HEX_BLACK
                self.matrix[j][i] = rgb

    def _is_valid(self,x,y):        
        return 0 <= x < self.cols and 0 <= y < self.rows and \
               self.matrix[y][x] != self.HEX_BLACK
    
    def neighbors(self,x,y):
        for (dx,dy) in ((0,1),(0,-1),(1,0),(-1,0)):
            if self._is_valid(x+dx,y+dy) and \
                   (x+dx,y+dy) not in self.block and \
                   self.matrix[y][x] == self.matrix[y+dy][x+dx]:
                self.block.add((x+dx,y+dy))
                self.neighbors(x+dx,y+dy)

    def dmesg(self, mesg):
        if self.debug:
            print >>sys.stderr, mesg
            
    def get_edge(self):
        k_1 = int(not(self.dp % 2))
        r_1 = int(not(int(self.dp % 2) - int(self.cc < 0)))
        k_2 = int(self.dp % 2)
        r_2 = int(self.dp < 2)
        self.block = list(self.block)
        self.block.sort(key=itemgetter(k_1), reverse=r_1)
        self.block.sort(key=itemgetter(k_2), reverse=r_2)
        return self.block[0]
        
    def get_next_valid(self, x, y):
        if self.dp == 0:
            x += 1
        elif self.dp == 1:
            y += 1
        elif self.dp == 2:
            x -= 1
        elif self.dp == 3:
            y -= 1
        else:
            print "Can't happen!"
            sys.exit(1)
        return x,y

    def step(self):
        self.dmesg("\n-- STEP: %s" % self.step_number)
        self.block = set([(self.x, self.y)])
        self.neighbors(self.x, self.y) # modifies self.block
        self.block_value = len(self.block)
        i = 1
        seen_white = 0
        ex, ey = self.get_edge()
        while i <= 8:
            nx, ny = self.get_next_valid(ex, ey)
            if not self._is_valid(nx, ny):
                i += 1
                if i % 2:
                    self.dp = (self.dp + 1) % 4                
                else:
                    self.cc *= -1
                self.dmesg("Trying again at %s, %s. DP: %s CC: %s" % \
                           (nx, ny, self.dp, self.cc))
                if self.matrix[ey][ex] != self.HEX_WHITE:
                    self.block = set([(ex, ey)])
                    self.neighbors(ex, ey) # modifies self.block
                    self.block_value = len(self.block)
                    ex, ey = self.get_edge()
            elif self.matrix[ny][nx] == self.HEX_WHITE:
                if not seen_white:
                    seen_white = 1
                    i = 0
                    self.dmesg("Entering white; sliding thru")
                ex, ey = nx, ny
            else: # next color is a color
                self.dmesg("%s @ (%s,%s) -> %s @ (%s,%s) DP:%s CC:%s" % \
                           (self.hex2tuple[self.matrix[self.y][self.x]].color, \
                            self.x, self.y, \
                            self.hex2tuple[self.matrix[ny][nx]].color, \
                            nx, ny,\
                            self.dp, self.cc))
                if not seen_white:
                    dH = self.hex2tuple[self.matrix[ny][nx]].hue - \
                         self.hex2tuple[self.matrix[self.y][self.x]].hue
                    dD = self.hex2tuple[self.matrix[ny][nx]].dark - \
                         self.hex2tuple[self.matrix[self.y][self.x]].dark
                    retval = self.do_arr[dH][dD]
                    self.dmesg("OPER: %s" % (self.do_arr[dH][dD]))
                else:
                    retval = "NOP"


#                self.dmesg("STACK: %s" % self.stack)
                self.x, self.y = nx, ny
                self.step_number += 1
                return retval
        else:
            self.dmesg("Execution trapped, program terminates")
            return None

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

if __name__ == '__main__':
    filename = sys.argv[1]
    c = Compiler(filename, backend="python")
    prog = c.compile(filename+".py")

