from itertools import product
import networkx as nx
from parser import Parser
from collections import namedtuple

Subroutine = namedtuple('subroutine', ['name','ops','dests'])

class Compiler:
    def __init__(self, filename):
        self._subroutines = {}

        parser = Parser(filename)
        self._entry = parser.entry()
        if self._entry is not None:
            self._compile(parser)

    def _compile(self, parser):
        subs = self._subroutines
        to_process = self._entry, ()
        while to_process:
            name, to_process = to_process
            node = parser.node(name)
            ops, dests = self._shortcut(parser, node)
            subs[name] = ops, dests
            for dest in dests:
                if dest not in subs:
                    to_process = dest, to_process

    def _shortcut(self, parser, node):
        ops = []
        hits = {}

        while True:
            if len(node.dests) == 0:
                return ops, ()
            if node.name in hits:
                steps = hits[node.name]
                intro = ops[:steps]
                loop = ops[steps:]
                dests = node.name,
                if steps:
                    self._subroutines[node.name] = loop, dests
                    return intro, dests
                else:
                    return loop, dests
            elif len(node.dests) > 1:
                ops.append(node.op)
                return ops, node.dests
            hits[node.name] = len(ops)
            if node.op != 'NOP':
                ops.append(node.op)
            node = parser.node(node.dests[0])
