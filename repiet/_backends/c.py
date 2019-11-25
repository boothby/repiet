from repiet._backends.generic import backend
import subprocess

class cbackend(backend):
    def define(self, name, ops, dest):
        if dest is None:
            return "{}:{}return 0;".format(name, ops)
        else:
            return "{}:{}goto {};".format(name, ops, dest)

    def pointer(self, options):
        p0, p1, p2, p3 = options
        return """if (pop1(&a)) {
    switch((a%%4+4)%%4) {case 1: goto %s; case 2: goto %s; case 3: goto %s;}
} goto %s;"""%(p1, p2, p3, p0)

    def switch(self, options):
        p0, p1 = options
        return "if (pop1(&a) && a&1) goto {}; goto {};".format(p1, p0);

    def push(self, x):
        return "psh(%d);"%x

    def execute(self, filename, capture_output=False):
        prog = subprocess.run("gcc -o {}.out {}".format(filename, filename), shell=True)
        args = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE) if capture_output else {}
        prog = subprocess.run("./{}.out".format(filename), *args)
        if capture_output:
            return prog.stdout, prog.stderr

    def instruction(self, i):
        return {
            "NOP" : "",
            "POP" : "pop1(&a);",
            "ADD" : "if (pop(&a, &b)) psh(b+a);",
            "SBT" : "if (pop(&a, &b)) psh(b-a);",
            "MLT" : "if (pop(&a, &b)) psh(b*a);",
            "DVD" : "if (pop(&a, &b) && a) psh(b/a);",
            "MOD" : "if (pop(&a, &b) && a) psh((a+b%a)%a);",
            "NOT" : "if (pop1(&a)) psh(!a);",
            "GRT" : "if (pop(&a, &b)) psh(b>a);",
            "DPL" : "if (pop1(&a)) { psh(a); psh(a); }",
            "RLL" : "if (pop(&a, &b)) rll(a, b);",
            "DIN" : "t=scanf(\"%d\", &a); if(t!=0) psh(t==EOF?-1:a);",
            "CIN" : "A=getc(stdin); psh((A==EOF)?-1:A);",
            "DUT" : "if (pop1(&a)) printf(\"%d\", a);",
            "CUT" : "if (pop1(&a)) printf(\"%c\", a);",
         }[i]

    def render(self, defs, start):
        if start is None:
            defs = "end:return 0;"
            start = "end"

        return """#include <stdio.h>
#include <string.h>
int d[30000];
int swp[30000];
int p = 0;
void psh(int x) {d[p++]=x;}
int pop1(int *x) {if(p){x[0] = d[--p];return 1;}return 0;}
int pop(int *x, int *y) {if(p>1){x[0] = d[--p];y[0] = d[--p];return 1;}return 0;}
void rll(int x, int y) {
 if (y<=0 || y > p) return;
 x = (y+x%y)%y;
 if (x == 0) return;
 int z = (x<0)?x+y:-x+y;
 memcpy(swp+y-z, d+p-y, (y-z)*sizeof(int));
 memcpy(swp, d+p-y+z, (y-z)*sizeof(int));
 memcpy(d+p-y, swp, y*sizeof(int));
}
int main() {
int t=0,i=0,a,b;
char A;
""" + defs + """
goto """ + start + """;
}"""
