import subprocess

class backend:
    def mangle(self, (x, y, d, c)):
        a = ("X%d" if d&1 else "x%d")%x
        b = ("Y%d" if d&2 else "y%d")%y
        return b+a if c else a+b

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
            return self.join_instructions((self.instruction(i, size), self.jump(self.mangle(next))))

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

    def execute(self, filename):
        raise NotImplementedError

    def code_template(self):
        raise NotImplementedError

class cppbackend(backend):
    def define(self, curr, dep):
        return "{}: {}".format(curr, dep)

    def exit(self):
        return "return 0;"

    def pointer(self, options):
        p0, p1, p2, p3 = options
        return """if (pop(a)) {
    switch((a%%4+4)%%4) {case 1: goto %s; case 2: goto %s; case 3: goto %s;}
} goto %s;"""%(p1, p2, p3, p0)

    def switch(self, options):
        p0, p1 = options
        return "if (pop(a) && a&1) goto {}; goto {};".format(p1, p0);

    def join_instructions(self, strux):
        return "".join(strux)

    def jump(self, next):
        return "goto {};".format(next);

    def execute(filename):
        g++ -o ptr1 ptr1.cpp
        prog = subprocess.run("g++ -o {}.out {}".format(filename, filename))
        prog = subprocess.run("./{}.out".format(filename), capture_output=True, text=True)
        return prog.stdout, prog.stderr

    def instruction(self, i, size):
        if i == 'PSH':
            return "psh({});".format(size)
        else:
            return {
                "NOP" : "",
                "POP" : "pop(a);",
                "ADD" : "if (pop(a, b)) psh(b+a);",
                "SBT" : "if (pop(a, b)) psh(b-a);",
                "MLT" : "if (pop(a, b)) psh(b*a);",
                "DVD" : "if (pop(a, b) && a) psh(b/a);",
                "MOD" : "if (pop(a, b) && a) psh((a+b%a)%a);",
                "NOT" : "if (pop(a)) psh(!a);",
                "GRT" : "if (pop(a, b)) psh(b>a);",
                "DPL" : "if (pop(a)) { psh(a); psh(a); }",
                "RLL" : "if (pop(a, b)) rll(a, b);",
                "DIN" : "cin >> a; if(good(cin)) psh(a);",
                "CIN" : "cin >> A; if(good(cin)) psh(A);",
                "DUT" : "if (pop(a)) cout << a;",
                "CUT" : "if (pop(A)) cout << A;",
             }[i]

    def code_template(self):
        return """#include <vector>
#include <iostream>
using namespace std;
vector<int> d;
void psh(int x) {d.push_back(x);}
int pop(int &x) {if (d.size()) {x = d.back();d.pop_back();return 1;}return 0;}
int pop(int &x, int &y) {if (d.size() > 1) {x = d.back();d.pop_back();y = d.back();d.pop_back();;return 1;}return 0;}
void rll(int x, int y) {
 if (y<=0 || y > d.size()) return;
 x = (y+x%y)%y;
 if (x == 0) return;
 int z = (x<0)?x+y:-x+y;
 vector<int> t(y);
 copy(d.end()+z, d.end(), t.begin());
 copy(d.end()-y, d.end()+z, t.begin()-z);
}
int main() {
int t=0,i=0,a,b;
char A;
goto PIET2_GOTO_START;
PIET2_DEFINE_LABELS
}"""

class pybackend(backend):
    def define(self, curr, dep):
        return "def {}():{}".format(curr, dep)
#        return "def {}():print({});{}".format(curr, curr, dep)

    def exit(self):
        return "return;"

    def pointer(self, options):
        return "a = pop(); return [{}][0 if a is None else (a%4+4)%4];".format(', '.join(options))

    def switch(self, options):
        return "a = pop(); return [{}][1 if a is None else a&1];".format(', '.join(options))

    def join_instructions(self, strux):
        return "".join(strux)

    def jump(self, next):
        return "return {};".format(next)

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
def pop(): return stack.pop() if stack else None
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

