from repiet.parser import Parser as _Parser
from repiet.util import Node as _Node

class Tracer:
    """
    A tracer class for Piet.  We take the parse tree output by the Parser, and
    compute traces.  By "trace", we mean a sequence of operations which are
    run in that sequence.  These are recorded as Nodes, specified in parser.py

    Where the Parser produces Nodes that may only NOP before transitioning to
    the next Node, the Tracer simplifies the majority of these away.  A Node
    is a namedtuple consisting of a name, a list of operations (each an int or
    a 3-character opcode; see parser.py), and a tuple of destinations.

    The Tracer is (necessarily) cycle-aware, and a Node's destinations may
    contain that Node's name.  The Tracer stops on branching operations -- a
    SWT (or PTR) will have 2 (or 4) different destinations, to be chosen by 
    examining the top of the stack.  Additionally, an empty tuple of
    destinations halts the program.

    Tracers have a similar interface to Parsers -- the name of the root is
    T.root(), and Node objects are fetched with T[name]

    Tracing a parsed program takes linear time in the number of parsed Nodes,
    which is ultimately linear in the number of pixels in the image.
    """
    def __init__(self, filename, **opinions):
        self._traces = {}

        parser = _Parser(filename, **opinions)
        self._root = parser.root()
        if self._root is not None:
            self._trace(parser)

    def root(self):
        """
        Returns the root of the the traced program.  If the program is trivial
        (that is, returns immediately with no input or output), we return None
        """
        return self._root
    
    def __getitem__(self, name):
        """
        Returns the Node associated with the input `name`, which must not be
        None

        A Node is a namedtuple consisting of:
            * a unique name,
            * a tuple of operations, each being a 3-character opcode or an int
            * a tuple of destination names

        If the final operation is "PTR" or "SWT" there will be 4 or 2
        destinations, respectively.  If there are zero destinations, then the
        program halts after executing the operations.  Otherwise, there is a
        single destination and the program jumpts to that destination after
        excuting this node.
        """
        return self._traces[name]

    def flatten(self):
        """
        Returns all Node objects as a list
        """
        return list(self._traces.values())
    
    def _trace(self, parser):
        """
        Traces the parsed program with a quick graph traversal algorithm
        """
        traces = self._traces
        #still using this obnoxiously idiomatic stack construction.  think
        #of the tuple (a,b) as a linked-list datastructure, where a is data
        #and b is essentially "next" (but actually it's the rest of the stack
        to_process = self._root, ()
        while to_process:
            name, to_process = to_process
            node = parser[name]
            ops, dests = self._trace_node(parser, node)
            traces[name] = _Node(name, tuple(ops), dests)
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
                #oops, we've discovered a loop.
                #all cases wind up going the same place
                dests = node.name,
                steps = hits[node.name]
                if steps:
                    #nontrivial intro, let's chop the trace in two
                    intro = ops[:steps]
                    loop = tuple(ops[steps:])
                    #the intro is nontrivial, so we stash the looping portion
                    self._traces[node.name] = Node(node.name, loop, dests)
                    #then, we return the intro segment
                    return intro, dests
                else:
                    #the intro is trivial, this is just a clean loop
                    return ops, dests
            elif len(node.dests) > 1:
                #oops, we hit a branch.  record the operation and bail
                ops.extend(node.ops)
                return ops, node.dests
            hits[node.name] = len(ops)
                #no point in keeping silly NOPs around in our ops...
            ops.extend(node.ops)
            #there's a single destination, so let's step into it
            node = parser[node.dests[0]]
        


