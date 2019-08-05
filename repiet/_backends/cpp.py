from repiet._backends.generic import backend
import subprocess

class cppbackend(backend):
    def define(self, name, ops, dest):
        if dest is None:
            return "{}: {}".format(name, ops)
        else:
            return "{}: {}goto {};".format(name, ops, dest)

    def pointer(self, options):
        p0, p1, p2, p3 = options
        return """if (pop(a)) {
    switch((a%%4+4)%%4) {case 1: goto %s; case 2: goto %s; case 3: goto %s;}
} goto %s;"""%(p1, p2, p3, p0)

    def switch(self, options):
        p0, p1 = options
        return "if (pop(a) && a&1) goto {}; goto {};".format(p1, p0);

    def push(self, x):
        return "psh(%d);"%x

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

    def render(self, defs, start):
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
goto """ + start + """;
""" + defs + """
}"""
