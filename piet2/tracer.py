from itertools import product
import networkx as nx
from parser import Parser
from collections import namedtuple

Trace = namedtuple('trace', ['name','ops','dests'])

class Tracer:
    """
    A tracer class for Piet.  We take the parse tree output by the Parser,
    and compute traces.  By "trace", we mean a sequence of operations which
    are run in that sequence.

    Where the Parser produces Nodes that may only NOP before transitioning
    to the next Node, the Tracer simplifies the majority of these away.  A
    Trace is a namedtuple consisting of a name, a list of operations (each
    an int or a 3-character opcode; see parser.py), and a tuple of
    destinations.

    The Tracer is (necessarily) cycle-aware, and a Node's destinations may
    contain that Node's name.  The Tracer stops on branching operations --
    a SWT (or PTR) will have 2 (or 4) different destinations, to be chosen
    by examining the top of the stack.  Additionally, an empty tuple of
    destinations halts the program.

    Tracing a parsed program takes linear time in the number of parsed Nodes.
    """
    def __init__(self, filename):
        self._traces = {}

        parser = Parser(filename)
        self._entry = parser.entry()
        if self._entry is not None:
            self._compile(parser)

    def entry(self):
        """
        Returns the entry point to the traced program.  If the program is
        trivial (that is, returns immediately with no input or output), then
        the entry point is None.
        """
        return self._entry
    
    def trace(self, name):
        """
        Returns the Trace associated with the input `name`, which must not be
        None

        A Trace is a namedtuple consisting of:
            * a unique name,
            * a tuple of operations, each being a 3-character opcode or an int
            * a tuple of destination states

        If the 3-character opcode is "PTR" or "SWT" there will be 4 or 2
        destinations, respectively.  If there are zero destinations, then the
        program halts after executing the operations.  Otherwise, there is a
        single destination and the program jumpts to that destination after
        excuting this trace.
        """
        return self._traces[name]
    
    def _trace(self, parser):
        """
        Traces the parsed program with a quick graph traversal algorithm
        """
        traces = self._traces
        #still using this obnoxiously idiomatic stack construction.  think
        #of the tuple (a,b) as a linked-list datastructure, where a is data
        #and b is essentially "next" (but actually it's the rest of the stack
        to_process = self._entry, ()
        while to_process:
            name, to_process = to_process
            node = parser.node(name)
            ops, dests = self._trace_node(parser, node)
            traces[name] = Trace(name, tuple(ops), dests)
            for dest in dests:
                if dest not in traces:
                    to_process = dest, to_process

    def _trace_node(self, parser, node):
        """
        Simulates a Piet interpreter, accumulating operations until a branch
        or loop is discovered.  In the case of a loop, we split the trace into
        two pieces -- the "intro" portion and "loop" portion.  This is done to
        reduce code duplication -- the alternative would be to record the
        intro and loop as a single trace, and then produce the loop as another
        trace.  As a side-effect, we save a tiny amount of runtime.
        """
        #list of operations encountered during this trace
        ops = []

        #a mapping from the names of nodes we've encountered in this trace, to
        #the length of ops when we first encountered it (to facilitate
        #efficient loop construction)
        hits = {}

        while True:
            if len(node.dests) == 0:
                return ops, ()
            if node.name in hits:
                #oops, we've discovered a loop.  let's chop the trace in two
                steps = hits[node.name]
                intro = ops[:steps]
                loop = ops[steps:]
                #both 'loop' and 'intro' wind up going the same place
                dests = node.name,
                if steps:
                    #the intro is nontrivial, so we stash the looping portion
                    self._traces[node.name] = Trace(node.name, tuple(loop), dests)
                    #then, we return the intro (its name is remembered by _trace
                    return intro, dests
                else:
                    #the intro is trivial, this is just a clean loop
                    return loop, dests
            elif len(node.dests) > 1:
                #oops, we hit a branch.  record the operation and bail
                ops.append(node.op)
                return ops, node.dests
            hits[node.name] = len(ops)
            if node.op != 'NOP':
                #no point in keeping silly NOPs around in our ops...
                ops.append(node.op)
            #there's a single destination, so let's step into it
            node = parser.node(node.dests[0])
        


