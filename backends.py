import subprocess

class backend:
    def mangle(self, (x, y, d, c)):
        a = ("x%d" if d&1 else "X%d")%x
        b = ("y%d" if d&2 else "Y%d")%y
        return a + b if c else b + a

    def compile_dep(self, curr, next, i, size):
        dep = self._compile_dep(next, i, size)
        return self.define(self.mangle(curr), dep)

    def _compile_dep(self, next, i, size):
        n_x, n_y, n_d, n_c = next
        if i is None:
            return self.exit()
        elif i == 'PTR':
            options = [(n_x,n_y,n_d,n_c), 
                       (n_x,n_y,(n_d+1)%4,n_c),
                       (n_x,n_y,(n_d+2)%4,n_c),
                       (n_x,n_y,(n_d+3)%4,n_c)]
            return self.pointer(list(map(self.mangle, options)))
        elif i == 'SWT':
            options = [(n_x,n_y,n_d,n_c),
                       (n_x,n_y,n_d,1-n_c)]
            return self.switch(list(map(self.mangle, options)))
        else:
            return self.join_instructions((self.instruction(i, size), self.jump(next)))

    def print_str(self, x):
        return self.join_instructions(
            z for c in x for z in (
                self.instruction('PSH', ord(c)),
                self.instruction('UTC', 0)
            )
        )

    def push_stack(self, x):
        return self.join_instructions(self.instruction('PSH', c) for c in x)

    def assemble(self, definitions, first, filename):
        template = self.code_template()
        code = template.replace("PIET2_DEFINE_LABELS", definitions).replace("PIET2_GOTO_START", self.mangle(first))
        if filename is None:
            return code
        with open(filename, 'w') as f:
            f.write(code)

    def define(self, curr, dep):
        raise NotImplementedError

    def exit(self):
        raise NotImplementedError

    def pointer(self, options):
        raise NotImplementedError

    def switch(self, options):
        raise NotImplementedError

    def join_instructions(self, strux):
        raise NotImplementedError

    def jump(self, next):
        raise NotImplementedError

    def instruction(self, i):
        raise NotImplementedError

    def execute(filename):
        raise NotImplementedError


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


class pybackend(backend):
    def define(self, curr, dep):
        return "def {}():print({});{}".format(curr, curr, dep)

    def exit(self):
        return "return;"

    def pointer(self, options):
        return "a = pop(); return [{}][0 if a is None else (a%4+4)%4];".format(', '.join(options))

    def switch(self, options):
        return "a = pop(); return [{}][1 if a is None else a&1];".format(', '.join(options))

    def join_instructions(self, strux):
        return "".join(strux)

    def jump(self, next):
        return "return {};".format(self.mangle(next))

    def instruction(self, i, size):
        if i == 'PSH':
            return "psh({});".format(size)
        else:
            return {
                "NOP" : "",
                "POP" : "pop();",
                "DIN" : "a = psh(int(input()));",
                "CIN" : "a = input(); psh(ord(a));",
                "DPL" : "a = pop(); a is not None and psh(a,a);",
                "NOT" : "a = pop(); a is not None and psh(int(not a));",
                "DUT" : "a = pop(); a is not None and print(a, sep='', end='', flush=1);",
                "CUT" : "a = pop(); a is not None and print(chr(max(0,min(255,a))), sep='', end='', flush=1);",
                "DVD" : "a,b = pop2(); a is not None and a!=0 and psh(b//a);",
                "MOD" : "a,b = pop2(); a is not None and a!=0 and psh(b%a);",
                "GRT" : "a,b = pop2(); a is not None and psh(int(b>a));",
                "RLL" : "a,b = pop2(); a is not None and rll(a,b);",
                "ADD" : "a,b = pop2(); a is not None and psh(b+a);",
                "MLT" : "a,b = pop2(); a is not None and psh(b*a);",
                "SBT" : "a,b = pop2(); a is not None and psh(b-a);",
             }[i]
    
    def print_str(self, x):
        return "".join(("print(",x,");"))

    def push_stack(self, x):
        return "stack.extend(%r);"%x 

    def code_template(self):
        return """stack = []
def psh(*X):stack.extend(X)
def pop(): stack and stack.pop()
def pop2(): return (None, None) if len(stack) < 2 else (stack.pop(), stack.pop())
def rll(x, y):
 x %= y
 if y <= 0 or x == 0: return
 z = -abs(x) + y * (x < 0)
 stack[-y:] = stack[z:] + stack[-y:z]
PIET2_DEFINE_LABELS
if __name__ == "__main__":
    bounce = PIET2_GOTO_START
    while bounce is not None:
        bounce = bounce()
"""

    def execute(filename):
        prog = subprocess.run("python {}".format(filename), capture_output=True, text=True)
        return prog.stdout, prog.stderr

