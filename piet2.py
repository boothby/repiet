import argparse
import sys

if __name__ == '__main__':
    filename = sys.argv[1]
    
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('source', type=str, help = 'source image')
    parser.add_argument('target', type=str, help = 'output filename')
    parser.add_argument('--backend', type=str, 
        choices=['c++', 'python'],
        default='python', help = 'language to compile to')
    parser.add_argument('--optimize', action='store_true', 
        default=False, help = '')
    parser.add_argument('--execute', action='store_true', 
        default=False, help = '')


    args = parser.parse_args()

    if args.backend == 'c++':
        from backends import cppbackend as backend
    elif args.backend == 'python':
        from backends import pybackend as backend
    backend=backend()



    if args.optimize:
        from optimizer import Optimizer as builder
    else:
        from compiler import Compiler as builder

    c = builder(args.source, backend)
    prog = c.compile(args.target)

    if args.execute:
        print(backend.execute(args.target))
