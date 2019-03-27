from collections import namedtuple
from PIL import Image
from itertools import product

SLIDE = (255, 255, 255)

HL =  {(a,b,c): (3*j+k, i)
                 for i, (x,y) in enumerate(((192, 255), (0, 255), (0,192)))
                     for j, (u,v) in enumerate(((x,y),(y,x)))
                        for k, (a,b,c) in enumerate(((v,u,u), (v,v,u), (u,v,u)))}

Lexeme = namedtuple('lexeme', ['name', 'corners', 'size', 'color'])
class Lexer:
    """
    A lexer class for Piet.  In text languages, a lexer identifies tokens so
    that a parser can collect those tokens into statements.  With Piet,
    it may not be immediately clear what a lexer would do.

    Philisophcally, we consider single-color blocks to be tokens, if the
    color is one of the 18 programming colors.  Whitespace is important for
    control flow, so we take the opportunity to to preprocess it as well.

    Practically, we'd like a fast method to process an image into its
    "symbols" and a layer to keep the image-processing out of the Parser.
    For the sake of cleanliness or memory frugality or something, we let
    the actual image fall out of scope.

    Under both of these considerations, we describe the public interface of
    a Lexer instance L, in two functions.

    The first function, L.at, is used to interrogate the lexed program at
    a pixel address.  The second function, L.slide, is used to quickly slide
    through whitespace.

    Given a point p = (x, y) or None; L.at(p) is 
        * the constant SLIDE if (x, y) is white,
        * None if p is None, if (x, y) is out of bounds, or a blocking pixel
        * the block containing (x, y)

    A block is a namedtuple with the following fields:
        name: a unique identifier for the block (which happens to be a
                point (x,y) in the block)
        corners: a dictionary from each (direction pointer, codel chooser)
                to the pixel in the block furthest in that direction
        size: the number of pixels in the block
        color: the color of the block as an (r, g, b) tuple of ints (bytes)

    If a point p = (x, y) is in a sliding region and d is a direction,
        then L.slide(p, d) is the furthest point reachable by sliding
        d-ward from p.

    Thus, the role of the Lexer is to pre-compute all pixel computation.

    Runs in almost-linear in the number of pixels in the image, and discards
    the Image object after initialization is complete to minimize memory use
    """
    def __init__(self, filename):
        self._parent = {}
        self._rank = {}
        self._slide = {}
        self._lexeme = {}
        find = self._find

        image = Image.open(filename).convert("RGB")
        self.X, self.Y = image.size
        self._lex(image)


    def at(self, p):
        """Returns SLIDE if p is in a sliding region, the block containing
        p if there is one, and None otherwise -- p can be None or (x,y)"""
        if (p, 2) in self._slide:
            return SLIDE
        elif p in self._parent:
            return self._lexeme[self._find(p)]
        else:
            return None

    def slide(self, p, d):
        """Returns the address maximum (x, y) reached by sliding d-ward
        p must be in a sliding region"""
        return self._slide[p, d] if d in (3, 2) else (
                 self._slide[self._slide[p, d^2], d]
               )

    def _lex(self, image):
        """
        Runs the actual lexing algorithm.
        """
        parent = self._parent
        union = self._union
        slide = self._slide
        X, Y = image.size
        getcolor = image.getpixel
        corners = {}
        rank = {}
        # first we walk over the pixels -- when we encounter whitespace, we
        # compute the sliding extents of the whitespace.  processing pixels
        # via product(range(X), range(Y)), the pixel addresses are explored
        # in lexicographic order -- making iterative constructions downward
        # and rightward simple, and upward or leftward more challenging --
        # see the production rules to the right, and self.slide for details

        # also we merge programming-colored pixels into their blocks using
        # a more-or-less standard DisjointSets datastructure. it's fairly
        # well-known that rank can be used to compute set sizes (valid only
        # at roots) -- we use the same trick to compute the "corners"
        for p in product(range(X), range(Y)):
            x, y = p
            color = getcolor(p)
            for q, z, Z, d0, d1 in [((x+1, y), x, X-1, 2, 0),
                                    ((x, y+1), y, Y-1, 3, 1)]:
                                                         #production rules W=white, X=anything but white, C=specific color
                if z >= Z:                               #pq: definition... runtime analysis for data structure use
                    if color == SLIDE:                   #---------------------------------------------------------------
                        slide[slide[p, d0], d1] = p      #W|: right(left(x, y)) := (x, y)
                    continue
                elif z == 0 and color == SLIDE:
                    slide[(p, d0)] = p                   #|W: left(x, y) := (x, y)
                color1 = image.getpixel((q[0],q[1]))
                if color == SLIDE:
                    if color1 == SLIDE:
                        slide[q, d0] = slide[(p, d0)]    #WW: left(x+1, y) := left(x, y) 
                    else:
                        slide[slide[(p, d0)], d1] = p    #WX: right(left(x, y)) := (x, y) ... only left(x,y) has cache thus right is O(left)
                elif color1 == SLIDE:
                    slide[q, d0] = q                     #XW: left(x, y) := (x, y) ... each (x, y) has cache thus left is O(1)
                elif color1 == color and color in HL:
                    union(p, q, rank, corners)           #CC: merge programming pixels of blocks ... amortized O(\alpha(XY))
            if color in HL and p not in parent:
                parent[p] = p
                rank[p] = 1
                corners[p] = {(d, c): p for d in (0, 1, 2, 3) for c in (0, 1)}

        lexemes = self._lexeme
        for p in product(range(X), range(Y)):
            if p == parent.get(p):
                lexemes[p] = Lexeme(p, corners[p], rank[p], getcolor(p))

    def _find(self, p0, rank = None):
        """ mostly standard find... but rank is ephemeral and we only
        need it in the initialization phase """
        try:
            p = self._parent[p0]
        except KeyError:
            self._parent[p0] = p0
            rank[p0] = 1
            return p0
        if p != p0:
            p = self._parent[p0] = self._find(p)
        return p

    def _union(self, p0, p1, rank, corners):
        """ mostly standard union... but rank and corners are ephemeral """
        r0 = self._find(p0, rank)
        r1 = self._find(p1, rank)
        if r0 == r1:
            return
        if rank[r0] < rank[r1]:
            root = r1
            prev = r0
        else:
            root = r0
            prev = r1

        self._parent[prev] = root
        rank[root] += rank[prev]
        corners[root] = _squash_corners(root, prev, corners)

def _squash_corners(p0, p1, corners):
    """compute the corners of the just-merged roots p0 and p1 
    returns a dictionary, to be inserted into self._corner at the
    new root"""

    K0 = corners.get(p0, {})
    K1 = corners.get(p1, {})
    return { (d, c) : _select_corner(d0, d1, c, K0.get((d,c), p0), K1.get((d,c), p1)) 
        for d, (d0, d1) in enumerate ((d0,d1) for d0 in (0,1) for d1 in (0,1))
        for c in (0,1) }

def _select_corner(d0, d1, c, p0, p1):
    """ return the (d0+2*d1, c)-most of the two points p0, p1
    okay and let's be honest this code is like woah.  I just
    wrote it in the tightest form I could imagine, and tweaked
    it until it was correct.
    """
    f = (lambda p: (p[1], p[0])) if d1 else (lambda p: p) 
    x0, y0 = f(p0)
    x1, y1 = f(p1)
    p2 = (x0, y0) if ((
                      (x0 == x1) and ((y1 < y0) if c^d1 else (y0 < y1))
                     ) or (
                      ((x0 < x1) if d0 else (x1 < x0))
                     )) else (x1, y1)
    return f(p2)
