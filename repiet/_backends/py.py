from repiet._backends.generic import backend
import subprocess

class py3backend(backend):
    def define(self, name, ops, dest):
        if dest is None:
            return "def {}():\n{}".format(name, ops or ' return')
        else:
            return "def {}():\n{} return {}\n".format(name, ops, dest)

    def pointer(self, options):
        return " a = pop()\n return [{}][0 if a is None else (a%4+4)%4]\n".format(', '.join(options))

    def switch(self, options):
        return " a = pop()\n return [{}][1 if a is None else a&1]\n".format(', '.join(options))

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
        if start is None:
            return ""
        return "".join(("""stack = []
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
"""))

    def execute(self, filename, capture_output=False):
        args = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE) if capture_output else {}
        prog = subprocess.run("python3 {}".format(filename), *args, shell=True)
        if capture_output:
            return prog.stdout, prog.stderr

