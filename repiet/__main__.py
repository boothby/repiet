import argparse
import sys
import repiet
import tempfile

def main(argv=None):
    #Determine if the user has asked for --help.  If not, we hide certain
    #arguments to keep usage / help simple.  This could probably be done
    #with custom formatters, but the approach here is nice and tidy.
    helpparser = argparse.ArgumentParser(description='determine if the user asked for help', add_help=False)
    helpparser.add_argument('--help', action='store_true', dest='longhelp')
    longhelp = helpparser.parse_known_args(argv)[0].longhelp

    parser = argparse.ArgumentParser(prog='repiet', description='Compile or execute a Piet program.',
                                     epilog='' if longhelp else 'Additional arguments available with --help')
    parser.add_argument('source', type=str, help='source image')
    parser.add_argument('-o', '--output', type=str, help='output filename')
    parser.add_argument('-b', '--backend', type=str,
        choices=('c', 'c++', 'piet', 'python', 'repiet'),
        default='python', help='language to compile to')
    parser.add_argument('-O', '--optimize', default=0, type=int, help='optimization level')
    parser.add_argument('-x', '--execute', action='store_true', 
        default=False, help = 'execute the compilation product')

    opinionparser = parser.add_argument_group('parsing/lexing arguments')
    for (op, kw) in repiet.util.opinion_options.items():
        kw['default'] = argparse.SUPPRESS
        if op != 'codel_size' and not longhelp:
            kw['help'] = argparse.SUPPRESS
        opinionparser.add_argument('--'+op, **kw)

    args = parser.parse_args(argv)
    opinions = {k:v for (k,v) in vars(args).items() if k in repiet.util.opinion_options}

    mode = 'w'
    if args.backend == 'c++':
        from repiet.backends import cppbackend as backend
        ext = '.cpp'
    elif args.backend == 'c':
        from repiet.backends import cbackend as backend
        ext = '.c'
    elif args.backend == 'python':
        from repiet.backends import py3backend as backend
        ext = '.py'
    elif args.backend == 'piet':
        from repiet.backends import pietbackend as backend
        ext = '.ppm'
        mode = 'wb'
    elif args.backend == 'repiet':
        from repiet.backends import irbackend as backend
        ext = '.rpir'
    else:
        raise RuntimeError("Bug! 'backend' should be a required parameter but we got here")

    if args.output is None:
        output = "".join((args.source, ext))
    else:
        output = args.output

    backend=backend()

    if args.optimize <= 0:
        prog = repiet.parser.Parser(args.source, **opinions)
    elif args.optimize == 1:
        prog = repiet.tracer.Tracer(args.source, **opinions)
    else:
        prog = repiet.optimizer.StaticEvaluator(args.source, **opinions)

    compiler = repiet.compiler.compiler(prog, backend)
    with open(output, mode) as outfile:
        outfile.write(compiler.render())    

    if args.execute:
        backend.execute(output)

if __name__ == "__main__":
    main()
