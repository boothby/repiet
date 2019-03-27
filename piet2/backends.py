import subprocess

class backend:
    def print_str(self, x):
        return self.join_instructions(
            z for c in x for z in (
                self.push(ord(c)),
                self.instruction('UTC')
            )
        )

    def push_stack(self, x):
        return self.join_instructions(self.push(c) for c in x)

    def join_instructions(self, strux):
        return "".join(strux)

    def join_defs(self, defs):
        return "\n".join(defs)

    def define(self, curr, dep):
        raise NotImplementedError

    def exit(self):
        raise NotImplementedError

    def pointer(self, options):
        raise NotImplementedError

    def switch(self, options):
        raise NotImplementedError

    def jump(self, next):
        raise NotImplementedError

    def instruction(self, i):
        raise NotImplementedError

    def execute(self, filename):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

class cppbackend(backend):
    def define(self, name, ops, dest):
        if dest is None:
            return "{}: {}".format(name, ops)
        else:
            return "{}: {}goto {};".format(name, ops, dest)

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

    def jump(self, next):
        return "goto {};".format(next);

    def execute(self, filename, capture_output=False):
        prog = subprocess.run("g++ -o {}.out {}".format(filename, filename), shell=True)
        args = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE) if capture_output else {}
        prog = subprocess.run("./{}.out".format(filename), *args)
        if capture_output:
            return prog.stdout, prog.stderr

    def instruction(self, i):
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
template<typename t> int pop(t &x) {if (d.size()) {x = d.back();d.pop_back();return 1;}return 0;}
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

class py3backend(backend):
    def define(self, name, ops, dest):
        if dest is None:
            return "def {}():\n{}".format(name, ops or ' return')
        else:
            return "def {}():\n{} return {}\n".format(name, ops, dest)

    def exit(self):
        return " return\n"

    def pointer(self, options):
        return " a = pop()\n return [{}][0 if a is None else (a%4+4)%4]\n".format(', '.join(options))

    def switch(self, options):
        return " a = pop()\n return [{}][1 if a is None else a&1]\n".format(', '.join(options))

    def jump(self, next):
        return " return {}\n".format(next)

    def instruction(self, i):
        return {
            "NOP" : "",
            "POP" : " pop()\n",
            "DIN" : " a = psh(int(input()))\n",
            "CIN" : " a = input()\n psh(ord(a))\n",
            "DPL" : " a = pop()\n a is not None and psh(a,a)\n",
            "NOT" : " a = pop()\n a is not None and psh(int(not a))\n",
            "DUT" : " a = pop()\n a is not None and print(a, sep='', end='', flush=1)\n",
            "CUT" : " a = pop()\n a is not None and print(chr(a%256), sep='', end='', flush=1)\n",
            "DVD" : " a,b = pop2()\n a is not None and a!=0 and psh(b//a)\n",
            "MOD" : " a,b = pop2()\n a is not None and a!=0 and psh(b%a)\n",
            "GRT" : " a,b = pop2()\n a is not None and psh(int(b>a))\n",
            "RLL" : " a,b = pop2()\n a is not None and rll(a,b)\n",
            "ADD" : " a,b = pop2()\n a is not None and psh(b+a)\n",
            "MLT" : " a,b = pop2()\n a is not None and psh(b*a)\n",
            "SBT" : " a,b = pop2()\n a is not None and psh(b-a)\n",
         }[i]
    
    def print_str(self, x):
        return "".join((" print(",repr(x),", sep='', end='', flush=1)\n"))

    def push(self, x):
        return " stack.append(%d)\n"%x

    def push_stack(self, x):
        if not x:
            return ""
        elif len(x) == 1:
            return self.push(*x)
        else:
            return " stack.extend({})\n".format(repr(x)) 

    def render(self, defs, start):
        import autopep8
        return autopep8.fix_code("".join(("""stack = []
def psh(*X): stack.extend(X)
def pop(): return stack.pop() if stack else None
def pop2(): return (None, None) if len(stack) < 2 else (stack.pop(), stack.pop())
def rll(x, y):
 x %= y
 if y <= 0 or x == 0: return
 z = -abs(x) + y * (x < 0)
 stack[-y:] = stack[z:] + stack[-y:z]
""", defs, """
if __name__ == "__main__":
    bounce = """, start, """
    while bounce is not None:
        bounce = bounce()
""")))

    def execute(self, filename, capture_output=False):
        args = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE) if capture_output else {}
        prog = subprocess.run("python {}".format(filename), *args, shell=True)
        if capture_output:
            return prog.stdout, prog.stderr

