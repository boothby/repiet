from repiet.parser import Parser as _Parser
from repiet.tracer import Tracer as _Tracer
from repiet.optimizer import StaticEvaluator as _StaticEvaluator
from repiet.backends import py3backend as _py3backend, cppbackend as _cppbackend, pietbackend as _pietbackend

class compiler:
    def __init__(self, prog, back):
        self._back = back
        self._root = prog.root()
        self._defs = back.join_defs(self._compile_def(x) for x in prog.flatten())

    def _compile_def(self, node):
        dests = node.dests
        ops = self._back.join_instructions(
                    self._dispatch(op, dests) for op in node.ops)
        return self._back.define(node.name, ops, 
                    dests[0] if len(dests) == 1 else None)

    def render(self):
        try:
            return self._code
        except AttributeError:
            code = self._code = self._back.render(self._defs, self._root)
            return code

    def _dispatch(self, op, dests):
        back = self._back
        if op == 'SWT':
            if len(dests) == 2:
                return back.switch(dests)
            else:
                raise RuntimeError("need 2 options to switch")
        elif op == 'PTR':
            if len(dests) == 4:
                return back.pointer(dests)
            else:
                raise RuntimeError("need 4 options to pointer")
        elif isinstance(op, int):
            return back.push(op)
        elif isinstance(op, str):
            return back.instruction(op)
        elif isinstance(op, tuple):
            stk, out = op
            if stk and out:
                return back.join_instructions((
                    back.push_stack(stk),
                    back.print_str(out),
                ))
            elif stk:
                return back.push_stack(stk)
            elif out:
                return back.print_str(out)
            else:
                return back.instruction('NOP')
        else:
            raise RuntimeError("Unfamiliar operation")

def Compile(filename, backend, optimization_level = 9012):
    if optimization_level <= 0:
        prog = _Parser(filename)
    elif optimization_level == 1:
        prog = _Tracer(filename)
    elif optimization_level > 1:
        prog = _StaticEvaluator(filename)

    if backend in ('py', 'py3'):
        back = _py3backend()
    elif backend in ('c++', 'cpp'):
        back = _cppbackend()
    elif backend in ('piet', ):
        back = _pietbackend()
    else:
        raise NotImplementedError("backend is not implemented")

    return compiler(prog, back).render()

