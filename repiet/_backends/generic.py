class backend:
    def print_str(self, x):
        return self.join_instructions(
            z for c in x for z in (
                self.push(ord(c)),
                self.instruction('CUT')
            )
        )

    def push_stack(self, x):
        return self.join_instructions(self.push(c) for c in x)

    def join_instructions(self, strux):
        return "".join(strux)

    def join_defs(self, defs):
        return "\n".join(defs)

    def define(self, curr, dep):
        raise NotImplementedError

    def pointer(self, options):
        raise NotImplementedError

    def switch(self, options):
        raise NotImplementedError

    def instruction(self, i):
        raise NotImplementedError

    def execute(self, filename):
        raise NotImplementedError

    def render(self):
        raise NotImplementedError

