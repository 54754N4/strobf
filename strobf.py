from core.engine.PolymorphicEngine import PolymorphicEngine
from core.engine.visitors import *
from argparse import ArgumentParser
import sys

if __name__ == '__main__':
    parser = ArgumentParser(
        prog="strobj",
        description="""
            Obfuscates a string using a polymorphic engine into different languages. Generates a
            decryption/deobfuscation routine in any of the following in the target languages (which can be specified
            to the -t or --target parameter):
            bash, c#, c_sharp, csharp, c, cpp, c++, javascript, js, java, masm64, powershell, ps, python, py
        """
    )
    parser.add_argument(
        "-l", "--min-ops",
        dest="min_ops",
        default=8,
        help="minimum number of transformations",
        type=int
    )
    parser.add_argument(
        "-u", "--max-ops",
        dest="max_ops",
        default=10,
        help="maximum number of transformations",
        type=int
    )
    parser.add_argument(
        "-b", "--max-bits",
        dest="max_bits",
        default=16,
        help="number of bits to encode chars into",
        type=int
    )
    parser.add_argument(
        "-t", "--target",
        dest="target",
        metavar="LANG",
        required=True,
        help="language to encode decryption routine",
        choices=[
            'bash',
            'c#', 'c_sharp', 'csharp',
            'c', 'cpp', 'c++',
            'javascript', 'js',
            'java',
            'masm64',
            'powershell', 'ps',
            'python', 'py'
        ]
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-i", "--input", dest="input", help="text to encrypt")
    group.add_argument("-f", "--file", dest="file", help="read from input file")
    group.add_argument("-s", "--stdin", dest="stdin", action="store_true", help="read from stdin")
    args = parser.parse_args()

    # Retrieve input
    text = ""
    if args.stdin:
        text = sys.stdin.read()
    elif args.file is not None:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        text = args.input

    # Generate code
    engine = PolymorphicEngine(args.min_ops, args.max_ops, args.max_bits)
    ctx = engine.transform(text)
    switch = {
        'bash': BashVisitor,
        'c#': CSharpVisitor,
        'c_sharp': CSharpVisitor,
        'csharp': CSharpVisitor,
        'c': CVisitor,
        'cpp': CVisitor,
        'c++': CVisitor,
        'javascript': JavaScriptVisitor,
        'js': JavaScriptVisitor,
        'java': JavaVisitor,
        'masm64': Masm64Visitor,
        'powershell': PowerShellVisitor,
        'ps': PowerShellVisitor,
        'python': PythonVisitor,
        'py': PythonVisitor
    }
    visitor = switch[args.target]()
    print(visitor.visit(ctx))
