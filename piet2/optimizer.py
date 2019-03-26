from tracer import Tracer

class Optimizer:
    def __init__(self, filename):
        self._subroutines = {}

        tracer = Tracer(filename)
        self._entry = tracer.entry()
        if self._entry is not None:
            self._optimize(tracer)

    def _optimize(self, tracer):
        subs = self._subroutines
        to_process = self._entry, ()
        while to_process:
            name, to_process = to_process
            sub = tracer.sub(name)
            ops, dests = self._trace(tracer, sub)
            subs[name] = ops, dests
            for dest in dests:
                if dest not in subs:
                    to_process = dest, to_process

    def _trace(self, tracer, sub):
        ops = []
        hits = set()
        vm = None
        while True:
            dests = sub.dests
            subops = sub.ops if len(dests) <= 1 else sub.ops[:-1]
            for op in subops:
                if vm is None:
                    if isinstance(op, int):
                        vm = PPVM()
                        vm.eval(op)
                elif not vm.eval(op):
                    ops.append((vm.stack, vm.outputs))
                    ops.append(op)
                    vm = None

            if vm is not None and vm.stack and len(dests) > 1:
                i = vm.stack.pop() % len(dests)
                if (sub.name, i) in hits:
                    return ops, (dests[i],)
                else:
                    hits.add((sub.name, i))
                    sub = tracer.sub(dests[i])
            else:
                if vm is not None:
                    ops.append((vm.stack, vm.outputs))
                return ops, dests


def _check(n):
    def dec(f):
        def _(self):
            if len(self.stack) < n:
                return False
            args = [self.stack.pop() for _ in range(n)]
            res = f(self, *args)
            if res is not None:
                self.stack.append(res)
            return True
        return _
    return dec
        
class PPVM(object):
    """~~~~~~~~~~ Proving Piet Virtual Machine ~~~~~~~~~
    Just like a Piet virtual machine, but buffers output
    and stops on popping an empty stack or reading input
    This is used for static analysis -- operations on a
    nonempty stack are performed at compile time until a
    cycle is encountered or an exit condition is hit.
    """

    def __init__(self):
        self.stack = []
        self.outputs = []

    def eval(self, op):
        if isinstance(op, int):
            self.stack.append(op)
            return True
        else:
            return self.__getattribute__(op)()

    def NOP(self): return True

    @_check(1)
    def POP(self, a): return

    @_check(2)
    def ADD(self, a, b): return b + a

    @_check(2)
    def SBT(self, a, b): return b - a

    @_check(2)
    def MLT(self, a, b): return b * a

    @_check(2)
    def DVD(self, a, b): return b // a

    @_check(2)
    def MOD(self, a, b): return b % a

    @_check(1)
    def NOT(self, a): return int(not a)

    @_check(2)
    def GRT(self, a, b): return b > a

    @_check(1)
    def DPL(self, a): self.stack.append(a); return a

    @_check(2)
    def RLL(self, a, b):
        a %= b
        if not (b <= 0 or a == 0):
            z = -abs(a) + b * (a < 0)
            self.stack[-b:] = self.stack[z:] + self.stack[-b:z]

    def DIN(self): return False

    def CIN(self): return False

    @_check(1)
    def DUT(self, a): self.outputs.append(str(a))

    @_check(1)
    def CUT(self, a): self.outputs.append(chr(a))


