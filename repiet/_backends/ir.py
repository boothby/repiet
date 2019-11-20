from repiet._backends.generic import backend

class irbackend(backend):
    def define(self, name, ops, dest):
        if dest is None:
            return "{}:{}".format(name, ops or '')
        else:
            return "{}:{}!{}".format(name, ops, dest)

    def pointer(self, options):
        return "PTR({})".format(' '.join(options))

    def switch(self, options):
        return "SWT({})".format(' '.join(options))

    def instruction(self, i):
        return i

    def push(self, x):
        return repr(x)

    def join_instructions(self, strux):
        return ",".join(strux)

    def render(self, defs, start):
        if start is None:
            return ""
        return "!{}\n{}".format(start, defs)

    def execute(self, filename, capture_output=False):
        raise NotImplementedError
