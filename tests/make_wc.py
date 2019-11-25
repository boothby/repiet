import repiet
from repiet.util import Node
nodes = (Node("start",(1,"NOT"),("whitespace",)),
Node("whitespace",("CIN","DPL","DPL",1,"ADD","NOT","SWT"),("ws32","wseof")),
Node("wseof",("POP","POP","DUT"),()),
Node("ws32",(32,"SBT","NOT","SWT"),("ws10","wsskip10")),
Node("wsskip10",("POP",),("whitespace",)),
Node("ws10",(10,"SBT","NOT","SWT"),("letter","whitespace")),
Node("letter",("CIN","DPL","DPL",1,"ADD","NOT","SWT"),("l32","leof")),
Node("leof",("POP","POP",1,"ADD","DUT"),()),
Node("l32",(32,"SBT","NOT","SWT"),("l10","lskip10")),
Node("lskip10",("POP",1,"ADD"),("whitespace",)),
Node("l10",(10,"SBT","NOT","SWT"),("letter","lws")),
Node("lws",(1,"ADD"),("whitespace",)))

nodes = {node.name: node for node in nodes}
class dummyprog:
    def __getitem__(self, name):
        return nodes[name]
    def root(self):
        return "start"
    def flatten(self):
        return list(nodes.values())

backend = repiet.backends.pietbackend
cmpl = repiet.compiler.compiler(dummyprog(), backend())
with open("wc.ppm", "wb") as outfile:
    outfile.write(cmpl.render())

backend = repiet.backends.py3backend
cmpl = repiet.compiler.compiler(dummyprog(), backend())
with open("wc.py", "w") as outfile:
    outfile.write(cmpl.render())

backend = repiet.backends.cbackend
cmpl = repiet.compiler.compiler(dummyprog(), backend())
with open("wc.c", "w") as outfile:
    outfile.write(cmpl.render())

backend = repiet.backends.cppbackend
cmpl = repiet.compiler.compiler(dummyprog(), backend())
with open("wc.cpp", "w") as outfile:
    outfile.write(cmpl.render())
