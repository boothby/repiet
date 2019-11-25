from repiet.tracer import Tracer as _Tracer
from repiet.util import Node as _Node

class StaticEvaluator:
    """
    A static evaluator for Piet.  We take the Nodes output by the Tracer, and
    run them through a specialized virtual machine, producing a new set of
    Nodes.

    The Parser and Tracer have two types of operation,
        * int -- PSH the int onto the stack
        * str -- a 3-character opcode
    whereas the StaticEvaluator produces another type of operation,
        * (tuple, str) -- push the tuple onto the stack, and print the string

    A Node is a namedtuple consisting of a name, a list of operations (each
    an int or a 3-character opcode; see parser.py), and a tuple of
    destinations.  When the destinations are a singleton, we simply jump to
    the node named by that destination.  A node ending with SWT (or PTR)
    will have 2 (or 4) different destinations, to be chosen by examining the
    top of the stack.  Additionally, an empty tuple of destinations halts the
    program.

    StaticEvaluators have a similar interface to Parsers and Tracers -- the
    name of the root is S.root(), and Node objects are fetched with S[name]

    The analysis performed by this class can take quadratic time in the total
    number of operations contained in the output of the Tracer -- which can
    ultimately be linear in the number of pixels contained in the image.
    """
    def __init__(self, filename, **opinions):
        self._traces = {}

        tracer = _Tracer(filename, **opinions)
        self._root = tracer.root()
        if self._root is not None:
            self._evaluate(tracer)

    def root(self):
        """
        Returns the root of the the program.  If the program is trivial (that
        is, returns immediately with no input or output), we return None
        """
        return self._root
    
    def __getitem__(self, name):
        """
        Returns the Node associated with the input `name`, which must not be
        None

        A Node is a namedtuple consisting of:
            * a unique name,
            * a tuple of operations, each being
                * a 3-character opcode
                * an int to be pushed on the stack
                * a pair (tuple, str) of produced through static evaluation
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
        Returns all Node objects as an list
        """
        return list(self._traces.values())

    def _evaluate(self, tracer):
        """
        Runs _eval on the traces with a quick graph traversal algorithm
        """
        traces = self._traces
        #I'm sick of apologizing for this -- what an awesome stack!
        to_process = (self._root, True), ()
        while to_process:
            (name, truestack), to_process = to_process
            trace = tracer[name]
            ops, dests, truestack = self._eval(tracer, trace, truestack)
            dests = [_rename(d, truestack) for d in dests]
            truename = _rename(name, truestack)
            traces[truename] = _Node(truename, tuple(ops), tuple(dests))
            for dest in dests:
                if dest not in traces:
                    to_process = (dest, truestack), to_process

    def _eval(self, tracer, trace, truestack):
        """
        Simulates a Piet interpreter running the operations of this trace,
        using a special virtual machine.  Operations whose impact cannot be
        determined at compile time, are reproduced verbatim in the returned
        Node.  The remainder are executed by the virtual machine, and their
        results are collected into a stack and an output string.
        """

        #list of operations in the static-eval'd trace
        ops = []
        def finish():
            end = vm.finish()
            if any(end): ops.append(end)
            return truestack and not end[0]

        #list of states we've encountered
        hits = {(trace.name, trace.name, truestack)}
        vm = None
        while True:
            print(" entering trace {}, truestack is".format(trace.name, truestack))
            dests = trace.dests
            #we skip the PTR and SWT operations here -- the vm can't handle
            #them... I promise to put it back!
            if len(dests) <= 1:
                traceops = trace.ops
                final = None
            else:
                traceops = trace.ops[:-1]
                final = trace.ops[-1]
            traceops = trace.ops if len(dests) <= 1 else trace.ops[:-1]
            for op in traceops:
                if vm is None:
                    #only start up a vm on a PSH
                    if isinstance(op, int):
                        print("   firing up a VM")
                        vm = _PPVM()
                        vm.eval(op)
                    elif op in ("CIN", "DIN") or not truestack:
                        ops.append(op)
                        truestack = False
                elif not vm.eval(op): #we've got a running vm; hit it!
                    if truestack and op not in ("CIN", "DIN"):
                        #We tried to perform an op on a truly empty stack... chuck
                        #it out and keep on truckin'
                        continue
                    else:
                        #oops, the vm couldn't perform that operation --
                        #grab its output and throw it away.
                        finish()
                        ops.append(op)
                        vm = None
                        truestack = False

            if vm is not None:
                if (vm.stack or truestack) and len(dests) > 1:
                    #here, we've got the opportunity to simplify PTR and SWT
                    #operations -- I know I promised to "put it back" but this is
                    #my opportunity to gobble up more program.  Instead, we perform
                    #the operation and keep going.
                    i = (vm.stack.pop() if vm.stack else 0) % len(dests)
                    dest = dests[i]
                    #and here's where we remember to be careful about going in
                    #cycles.  we can visit any given trace up to 4 times, provided
                    #that it exits to a different trace each time
                    if (trace.name, dest, truestack) in hits:
                        return ops, (dest,), finish()
                    else:
                        hits.add((trace.name, dest, truestack))
                        #fetch the next trace and keep going
                        trace = tracer[dest]
                elif len(dests) > 1:
                    #we want to pop from an apparently (but not provably) empty stack.
                    #put the final conditional back, and quit evaluating
                    return ops, dests, finish()
                elif len(dests) == 1:
                    dest, = dests
                    if (trace.name, dest, truestack) in hits:
                        end = vm.finish()
                        if any(end): ops.append(end)
                        return ops, (dest,), (truestack and not end[0])
                    else:
                        hits.add((trace.name, dest, truestack))
                        trace = tracer[dest]
                else:
                    return ops, dests, finish()
            else:
                if final is not None:
                    if truestack:
                        #the stack is empty so we hop to dests[0]
                        dests = dests[0],
                    else:
                        #otherwise we put the final op back
                        ops.append(final)
                if len(dests) != 1 or (trace.name, dests[0], truestack) in hits:
                    return ops, dests, truestack
                else:
                    hits.add((trace.name, dests[0], truestack))
                    #fetch the next trace and keep going
                    trace = tracer[dests[0]]

def _rename(name, truestack):
    if truestack:
        return name+"_"
    return name

def _check(n):
    """
    This is a method decorator that checks before executing an operation. The
    decorated method returns True if the operator's impact is known at
    runtime, and False otherwise.  The decorator removes the values from the
    stack and passes them on to the original method.    
    """
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
        
class _PPVM(object):
    """~~~~~~~~~~ Proving Piet Virtual Machine ~~~~~~~~~
    Just like a Piet virtual machine, but buffers output
    and stops on popping an empty stack or reading input
    This is used for static analysis -- operations on a
    nonempty stack are performed at compile time until a
    cycle is encountered or an exit condition is hit.
    """

    def __init__(self, ops=()):
        self.stack = []
        self.outputs = []
        for i, op in enumerate(ops):
            if not self.eval(op):
                raise RuntimeError('failed to evaluate\n%s\n%s\n%s'%(ops, (i, op), self.stack))

    def eval(self, op):
        """
        Evaluate a single operation.  SWT and PTR are not handled here.
        This function returns False in the cases that
            * an operation needs a deeper stack than we've currently got
            * an operation requires runtime input from the user
        """
        if isinstance(op, int):
            self.stack.append(op)
            return True
        else:
            return self.__getattribute__(op)()

    def finish(self):
        """
        Returns the collected stack and output as a pair (the new type of
        instruction introduced in this file.
        """
        return tuple(self.stack), ''.join(self.outputs)

    def RLL(self):
        #this is the most complicated part... if a roll goes below the depth
        #of the current stack, then we don't want to pop the RLL arguments.
        #this isn't worth folding into the _check decorator because it's
        #already ugly-general
        stack = self.stack
        #don't forget to discount the arguments we popped...
        if len(stack) < 2 or len(stack)-2 < stack[-2]:
            return False
        a = stack.pop() #was stack[-1]
        b = stack.pop() #was stack[-2]
        if b > 0:
            a %= b
            if a:
                #I think these are the only lines that survived from Ross
                #Tucker's interpreter.  Thanks, Ross!
                z = -abs(a) + b * (a < 0)
                stack[-b:] = stack[z:] + stack[-b:z]
            #else: perform zero rolls at depth b... done!
        #else: DMM says to skip negative-depth rolls... check!
        return True

    #DIN and CIN take user inputs; which we obviously don't know at
    #compile time.
    def DIN(self): return False
    def CIN(self): return False

    #No ops, no problems
    def NOP(self): return True

    #for the next several operations, we return a value onto the stack
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

    #The remaining operations return None, whence nothing is pushed
    @_check(1)
    def POP(self, a): return

    #these two record the value into the list of outputs
    @_check(1)
    def DUT(self, a): self.outputs.append(str(a))

    @_check(1)
    def CUT(self, a): self.outputs.append(chr(a&255))


