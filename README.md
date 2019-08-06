# Repiet

Repiet is a compiler for the [Piet](http://www.dangermouse.net/esoteric/piet.html) graphical language, written in Python.  The
name "repiet" is meant to convey that it can recompile Piet programs into Piet.
Additionally, there are Python and C++ backends (more to come; feel free to
contribute).

To compile a Piet program, we lex it, parse it, and optionally perform some
optimizations.

## Lexing

The lexer computes lexemes, (up, down, left, right)-connected sets of same-colored
pixels, and identifies whitespace and blocking features (non-white, non-coding 
pixels are treated as blocking, an opinion which may change in the future).  As 
the lexemes are computed, we locate eight corners of each; corresponding to the 
eight (dp, cc) states.  As whitespace is located, we identify the 4 pixels reached
by sliding in each of four dp directions.

## Parsing

The parser begins in the upper-left corner of the image, and computes a parse tree
whose nodes correspond to (lexeme, dp, cc) states.  For each node, we compute the
operation (if any) resulting from the (dp, cc)-ward transition from the lexeme, as
well if the next visited lexeme (if any).  If the operation is a switch or a
pointer, there are two or four possible next-visited lexemes respectively.

## Tracing

The tracer collects a parse tree into sequences of non-branching operations.  The
result is a new parse tree, typically with fewer nodes.  Depending on the backend
chosen, this may be a slight optimization.



