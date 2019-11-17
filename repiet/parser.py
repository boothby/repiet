from repiet.util import SLIDE as _SLIDE, HL as _HL, Node as _Node, OP as _OP, default_opinions as _default_opinions
from repiet.lexer import Lexer as _Lexer

__all__ = ["Parser"]

class Parser:
    """
    A parser class for Piet.  In text languages, a lexer identifies tokens
    so that a parser can collect those tokens into statements.  We define
    tokens (lexemes) as blocks of programming pixels; statements are digrams
    of lexemes.

    This parser provides a layer between the lexer and the compiler.  Where
    the lexer computes blocks and slides, the parser reads the lexed program
    to compute the transitions of an interpreter, recording them as edges in
    a directed graph.

    Thus, the role of the Parser is to pre-compute state transitions, which
    effectively translates a lexed Piet program into a state machine.

    We describe the public interface of a Parser instance P, representing a
    parse tree.  A tree Node contains a name, an instruction and a tuple of
    destinations.  An instruction is either a 3-character opcode or an int
    representing a push.

    To get the name of the root, call P.root(), and Nodes themselves can be
    retrieved by P[name].

    Construction of a parser takes linear time in the size of the lexer
    output, which is linear in the total image size.  The algorithm is a
    depth-first search beginning at the root, processing nodes found by the
    lexer.  Discards the Lexer after initialization, to minimize memory use.
    """
    def __init__(self, filename, **opinions):
        self._opinions = _default_opinions(**opinions)
        self._process_opinions()

        lexer = _Lexer(filename, **opinions)
        p0 = 0, 0
        d = c = 0
        root = lexer.at(p0)
        if root == _SLIDE:
            p0, d, c = self._slide(lexer, p0, d, c)[0]
            root = lexer.at(p0)

        self._graph = {}
        if root is None:
            self._root = None
        else:
            self._root = _name((p0, d, c))
            self._parse(lexer, (p0, d, c))


    def root(self):
        """
        Returns the root of the parse tree.  If the program is trivial (that
        is, halts immediately with no input or output), then the root is None.
        """
        return self._root

    def __getitem__(self, name):
        """
        Returns the Node associated with the input `name`, which must not be
        None

        A Node is a namedtuple consisting of:
            * a unique name
            * a 3-character opcode, an integer n denoting PSH(n) or None
            * a tuple of destination names

        If the 3-character opcode is "PTR" or "SWT" there will be 4 or 2
        destinations, respectively.  If there are zero destinations, the Node
        halts.  Otherwise the node has a single destination.
        """
        return self._graph[name]

    def flatten(self):
        """
        Returns all node objects as a list
        """
        return list(self._graph.values())

    def _parse(self, lexer, state):
        """
        Parses the lexed program with a quick graph traversal algorithm
        """
        #another obnoxious performance hack -- stacks as recursive 2-ples
        front = state, () #                              this is a stack
        while front:
            state, front = front #                       this is a pop
            op, dests = self._knock(lexer, *state)
            name = _name(state)
            dnames = tuple(_name(dest) for dest in dests)
            ops = () if op == "NOP" else (op,)
            self._graph[name] = _Node(name, ops, dnames)
            for dest, dname in zip(dests, dnames):
                if dname not in self._graph:
                    #sentinel value to moderate stack size
                    self._graph[dname] = None
                    front = dest, front #                this is a push

    def _knock(self, lexer, p, d, c, patience=8):
        """
        Simulates a Piet interpreter at block p with DP=d and CC=c.

        Returns an instruction, the size of the current block (to be pushed,
        maybe) and a list of destinations.

        Called "knock" because we pick a corner, peek at the next pixel over
        neighbor in search of digrams.  If we find slidespace, we slide into
        it; if we're blocked, we alternately picking the other corner and
        turning clockwise.  Digrams emit instructions, sliding merely jumps.
        """
        #retrieve the block at p
        b0 = lexer.at(p)
        if b0 == _SLIDE:
            #this occurs for the "nonhalting" sliding opinion
            return "NOP", (p, d, c)

        #identify the (d,p)-most corner of b0, and step one pixel d-ward
        q = self._next(b0.corners[d, c], d)
        #examine the image contents at q
        b1 = lexer.at(q)

        if b1 == _SLIDE:
            #q is in a sliding region -- slide on through, and either NOP
            #over to the next block or quit
            slid = self._slide(lexer, q, d, c)
            if slid == 'timid':
                b1 = None
            else:
                if slid == 'hang':
                    slid = (p, d, c),
                return "NOP", slid

        if b1 is None:
            #either q was out of bounds, or there's a blocking pixel at q.
            #advance either DP or CC, and recurse with 1 unit less patience
            return self._knock(lexer, p, (d+1)%4, c, patience-1) if patience % 2 else (
                   self._knock(lexer, p, d, c^1, patience-1) if patience > 0 else ('NOP', ()))
        else:
            #q has a different programming color.  An interpreter would emit
            #an instruction and slide into b1.  We enumerate the destination
            #states, to be consumed by a compiler.
            h0,l0 = _HL[b0.color]
            h1,l1 = _HL[b1.color]
            #DMM's instructions are based in hue and darkness... awkward
            op = self._OP[(h1-h0)%6][(l0-l1)%3]
            if op == "PSH":
                op = b0.size
            return op, ((q, d, c), (q, d, c^1)) if op == 'SWT' else (
                        tuple((q,(d+i)%4,c) for i in (0,1,2,3)) if op == 'PTR' else
                        ((q, d, c),))

    def _slide(self, lexer, p, d, c):
        """
        Simulates a Piet interpreter sliding through whitespace.  If a block
        is encountered, it is returned in a singleton tuple.  Otherwise, the
        interpreter gets trapped in the sliding region and terminates -- we
        return an empty tuple.
        """
        trail = set()
        stopslide = self._stopslide
        while 1:
            t = stopslide((p, d, c), trail)
            if t is not None:
                return t

            #Slides d-ward from the pixel at p.
            q = lexer.slide(p, d)
            #Go one step d-ward from q
            r = self._next(q, d)
            #examine the image contents at r
            b = lexer.at(r)

            if b is None:
                #either r was out of bounds, or there's a blocking pixel at r
                #advance DP and CC, and recurse with updated trail.
                d = (d+1)%4
                c^= 1
                p = q
            elif b == _SLIDE:
                #this shouldn't happen
                raise RuntimeError(("Bug in Lexer -- {} and {} are adjacent pixels"
                                    "in different sliding regions").format(q, r))
            else:
                #we found a block!
                return (r, d, c),

    def _process_opinions(self):
        """Process the opinions dictionary to ensure that the behavior of
        this class is appropriate.  A more standard approach would be to
        use a factory which dispatches class mixins.  Maybe later."""
        cs = self._opinions['codel_size']
        def next(_self, p, d):
            """The next d-ward point from p=(x, y) -- does not respect boundaries"""
            x, y = p
            return (x+cs, y) if d == 0 else (
                   (x, y+cs) if d == 1 else (
                   (x-cs, y) if d == 2 else (x, y-cs)))

        #this is how one binds methods to instances? TIL
        self._next = next.__get__(self, self.__class__)

        #common mis-implementation addressed by DMM's clarification:
        #   ...or until the interpreter begins retracing its route. If it
        #   retraces its route entirely within a white block, there is no
        #   way out of the white block and execution should terminate.
        #so we've added a few opinions -- 'halting' is correct;
        #'nonhalting' and 'timid' exist to model other interpreters 
        if self._opinions['sliding'] == 'halting':
            def stopslide(s, state, trail):
                if state in trail:
                    return ()
                trail.add(state)
        elif self._opinions['sliding'] == 'nonhalting':
            def stopslide(s, state, trail):
                if state in trail:
                    return 'hang'
                trail.add(state)
        elif self._opinions['sliding'] == 'timid':
            def stopslide(s, state, trail):
                if trail:
                    return 'timid'
                trail.add(state)
        
        #Annoying mis-implementation... some folks get hue and/or lightness
        # changes backwards
        _op = _OP[::-1] if self._opinions['color_dir_h'] == '+' else _OP
        self._OP = [op[::-1] for op in _op] if self._opinions['color_dir_l'] == '+' else _op

        self._stopslide = stopslide.__get__(self, self.__class__)


def _name(state):
    """Makes a unique string for a given state"""
    (x, y), d, c = state
    a = ("X%d" if d&1 else "x%d")%x
    b = ("Y%d" if d&2 else "y%d")%y
    return b+a if c else a+b
