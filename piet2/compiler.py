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

    def _shortcut(self, parser, node, hits = None, ops = None):
        if ops is None:
            ops = []
            hits = set()
        if len(node.dests) == 0:
            return ops, ()
        if node in hits:
            return ops, (node.name, )
        elif len(node.dests) > 1:
            ops.append(node.op)
            return ops, node.dests
        else:
            hits.add(node)
            dest = parser.node(node.dests[0])
            if node.op != 'NOP':
                ops.append(node.op)
            return self._shortcut(parser, dest, hits, ops)

