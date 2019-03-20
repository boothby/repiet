from collections import namedtuple
from PIL import Image
from itertools import product
from lexer import Lexer, SLIDE, HL


Node = namedtuple('node', ['name', 'op', 'dests'])

OP = [["NOP", "PSH", "POP"],
      ["ADD", "SBT", "MLT"],
      ["DVD", "MOD", "NOT"],
      ["GRT", "PTR", "SWT"],
      ["DPL", "RLL", "DIN"],
      ["CIN", "DUT", "CUT"]]

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

    We describe the public interface of a Parser instance P, in two 
    functions.  This interface encodes states as Nodes.  A Node contains
    a name, an instruction and a list of destinations.  An instruction is
    either a 3-character opcode or an int representing a push.

    The first function, P.entry, returns the entry point to the image as a
    State.  The second function, P.node, returns a Node associated with a
    given state.  

    Construction of a parser takes linear time in the size of the lexer
    output, which is linear in the total image size.  The algorithm is a
    depth-first search beginning at the entry point, processing nodes found
    by the lexer.  Discards the Lexer after initialization, to minimize memory
    use.
    """
    def __init__(self, filename):
        lexer = Lexer(filename)
        p0 = 0, 0
        d = c = 0
        entry = lexer.at(p0)
        if entry == SLIDE:
            p0, d, c = _slide(self, p0, d, c)[0]
            entry = lexer.at(p0)

        self._graph = {}
        if entry is None:
            self._entry = None
        else:
            self._entry = _name((p0, d, c))
            self._parse(lexer, (p0, d, c))


    def entry(self):
        """
        Returns the entry point to the parsed program.  If the program is
        trivial (that is, returns immediately with no input or output), then
        the entry point is None.
        """
        return self._entry

    def node(self, state):
        """
        Returns the Node associated with the input `state`, which must not be
        None

        A Node is a namedtuple consisting of:
            * a State object (equal to input `state`),
            * a 3-character opcode, an integer n denoting PSH(n) or None
            * a list of destination states

        If the 3-character opcode is "PTR" or "SWT" there will be 4 or 2
        destinations, respectively.  If there are zero destinations, `state`
        is a halting node.  Otherwise the node has a single destination.
        """
        return self._graph[state]

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
            self._graph[name] = Node(name, op, dnames)
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
        #identify the (d,p)-most corner of b0, and step one pixel d-ward
        q = _next(b0.corners[d, c], d)
        #examine the image contents at q
        b1 = lexer.at(q)

        if b1 is None:
            #either q was out of bounds, or there's a blocking pixel at q.
            #advance either DP or CC, and recurse with 1 unit less patience
            return self._knock(lexer, p, (d+1)%4, c, patience-1) if patience % 2 else (
                   self._knock(lexer, p, d, c^1, patience-1) if patience > 0 else ('NOP', ()))
        elif b1 == SLIDE:
            #q is in a sliding region -- slide on through, and either NOP
            #over to the next block or quit
            return "NOP", self._slide(lexer, q, d, c)
        else:
            #q has a different programming color.  An interpreter would emit
            #an instruction and slide into b1.  We enumerate the destination
            #states, to be consumed by a compiler.
            h0,l0 = HL[b0.color]
            h1,l1 = HL[b1.color]
            op = OP[(h1-h0)%6][(l1-l0)%3]
            if op == "PSH":
                op = b0.size
            return op, ((q, d, c), (q, d, c^1)) if op == 'SWT' else (
                        tuple((q,(d+i)%4,c) for i in (0,1,2,3)) if op == 'PTR' else
                        ((q, d, c),))

    def _slide(self, lexer, p, d, c, patience=4):
        """
        Simulates a Piet interpreter sliding through whitespace.  If a block
        is encountered, it is returned in a singleton tuple.  Otherwise, the
        interpreter gets trapped in the sliding region and terminates -- we
        return an empty tuple.
        """
        #Slides d-ward from the pixel at p.
        q = lexer.slide(p, d)
        #Go one step d-ward from q
        r = _next(q, d)
        #examine the image contents at r
        b = lexer.at(r)

        if b is None:
            #either q was out of bounds, or there's a blocking pixel at q
            #advance DP and CC, and recurse with 1 unit less patience
            return self._slide(lexer, q, (d+1)%4, c^1, patience-1) if patience else ()
        elif b == SLIDE:
            #this shouldn't happen
            raise RuntimeError(("Bug in Lexer -- {} and {} are adjacent pixels in"
                                "different sliding regions").format(q, r))
        else:
            #we found a block!
            return (r, d, c),

def _next(q, d):
    """The next d-ward point from (x, y) -- does not respect boundaries"""
    x, y = q
    return (x+1, y) if d == 0 else (
           (x, y+1) if d == 1 else (
           (x-1, y) if d == 2 else (x, y-1)))

def _name(state):
    """Makes a unique string for a given state"""
    (x, y), d, c = state
    a = ("X%d" if d&1 else "x%d")%x
    b = ("Y%d" if d&2 else "y%d")%y
    return b+a if c else a+b
