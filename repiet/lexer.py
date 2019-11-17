from PIL import Image as _Image
from itertools import product as _product
from repiet.util import Lexeme as _Lexeme, SLIDE as _SLIDE, BLOCK as _BLOCK, HL as _HL, default_opinions as _default_opinions

__all__ = ["Lexer"]

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

    Runs in nearly-linear in the number of pixels in the image, and discards
    the Image object after initialization is complete to minimize memory use
    """
    def __init__(self, filename, **opinions):
        self._parent = {}
        self._rank = {}
        self._slide = {}
        self._lexeme = {}
        self._opinions = _default_opinions(**opinions)
        self._process_opinions()

        image = _Image.open(filename).convert("RGB")
        self.X, self.Y = image.size
        self._lex(image)

    def at(self, p):
        """Returns SLIDE if p is in a sliding region, the block containing
        p if there is one, and None otherwise -- p can be None or (x,y)"""
        if (p, 2) in self._slide:
            return _SLIDE
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
        _kind = self._kind
        X, Y = image.size
        cs = self._opinions['codel_size']
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
        for p in _product(range(0, X, cs), range(0, Y, cs)):
            x, y = p
            kind, color = _kind(getcolor(p))
            for q, z, Z, d0, d1 in [((x+cs, y), x, X-cs, 2, 0),  #peek at pixel to right
                                    ((x, y+cs), y, Y-cs, 3, 1)]: #peek at pixel below (left,right -> up,down)
                if z >= Z:                               #rules: W=white, X=nonwhite, C=specific color
                    if kind == 'slide':                  #------------------------------------------------------
                        slide[slide[p, d0], d1] = p      #W|: right(left(x, y)) := (x, y)
                    continue
                elif z == 0 and kind == 'slide':
                    slide[(p, d0)] = p                   #|W: left(x, y) := (x, y)
                kind1, color1 = _kind(getcolor(q))
                if kind == 'slide':
                    if kind1 == 'slide':
                        slide[q, d0] = slide[(p, d0)]    #WW: left(x+1, y) := left(x, y) 
                    else:
                        slide[slide[(p, d0)], d1] = p    #WX: right(left(x, y)) := (x, y)
                elif kind1 == 'slide':
                    slide[q, d0] = q                     #XW: left(x, y) := (x, y) 
                elif kind == 'code' and color1 == color:
                    union(p, q, rank, corners)           #CC: merge programming pixels of blocks
            if kind == 'code' and p not in parent:
                parent[p] = p
                rank[p] = 1
                corners[p] = {(d, c): p for d in (0, 1, 2, 3) for c in (0, 1)}

        lexemes = self._lexeme
        for p in _product(range(0, X, cs), range(0, Y, cs)):
            if p == parent.get(p):
                lexemes[p] = _Lexeme(p, corners[p], rank[p], getcolor(p))

    def _process_opinions(self):
        """Process the opinions dictionary to ensure that the behavior of
        this class is appropriate.  A more standard approach would be to
        use a factory which dispatches class mixins.  Maybe later."""
        opinion = self._opinions['noncoding']
        if opinion == 'block':
            def kind(_self, c):
                if c == _SLIDE: return 'slide', _SLIDE
                elif c in _HL:  return 'code', c
                else:           return 'block', _BLOCK
        elif opinion == 'slide':
            def kind(_self, c):
                if c == _BLOCK: return 'block', _BLOCK
                elif c in _HL:  return 'code', c
                else:           return 'slide', _SLIDE
        elif opinion == 'round':
            def kind(_self, c):
                if c == _BLOCK:   return 'block', _BLOCK
                elif c == _SLIDE: return 'slide', _SLIDE
                else:
                    return ('code',
                             min( ((c[0]-d[0])**2+(c[1]-d[1])**2+(c[2]-d[2])**2, d)
                                for d in _HL)[1])
        self._kind = k = kind.__get__(self, self.__class__)

    def _find(self, p0, rank = None):
        """mostly standard find. rank is ephemeral because we only
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
        """mostly standard union... but in addition to computing rank we
        also locate the block's corners. rank and corners are ephemeral
        because they're only needed during initialization"""
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
    """compute the corners of the just-merged roots p0 and p1.
    returns a dictionary, to be inserted into corners at the
    new root"""
    K0 = corners.get(p0, {})
    K1 = corners.get(p1, {})
    return { (d, c) : _select_corner(d, c, K0.get((d,c), p0), K1.get((d,c), p1))
        for d in (0,1,2,3) for c in (0,1) }

_cornertable = [0xd0e0c, 0x3f24, 0x323130, 0x3f0018]
def _select_corner(d, c, p, q):
    """return the (d, c)-most of the two points p and q."""
    #Uhhh... yeah, packing this into a lookup table is obtuse.
    #request an apology from /dev/urandom and you'll probably
    #get one, eventually?
    bitaddr = c + 2*(p[0]<q[0]) + 4*(p[0]>q[0]) + 8*(p[1]<q[1]) + 16*(p[1]>q[1])
    return q if (_cornertable[d] >> bitaddr)&1 else p
