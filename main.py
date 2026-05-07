"""
main.py - CLI driver for the PL interpreter.

Usage:
  python main.py <file.pl>          run a program
  python main.py --tac <file.pl>    print TAC then exit
  python main.py                    interactive REPL
"""

import sys
from src.lexer import PLLexer
from src.parser import PLParser
from src.type_checker import TypeChecker, TypeErrorException
from src.tac import TACGenerator, pretty_tac
from src.interpreter import make_interpreter


def run_source(src: str, show_tac: bool = False) -> str:
    """Run source text through the full pipeline. Returns printed output."""
    import io, contextlib

    lexer  = PLLexer()
    parser = PLParser()

    program = parser.parse(lexer.tokenize(src))
    if program is None or parser.errors:
        return "Parsing failed.\n" + "\n".join(parser.errors)

    checker = TypeChecker()
    try:
        checker.check(program)
    except TypeErrorException as e:
        return str(e)

    gen = TACGenerator()
    instructions = gen.generate(program)

    if show_tac:
        return pretty_tac(instructions)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        interp = make_interpreter(instructions, program)
        interp.run()
    return buf.getvalue()


def repl():
    print("PL interpreter  |  blank line to run  |  :tac  |  :quit\n")
    while True:
        lines = []
        try:
            while True:
                line = input('> ' if not lines else '  ')
                if line.strip() in (':quit', ':exit', 'quit', 'exit'):
                    return
                if line == '' and lines:
                    break
                lines.append(line)
        except EOFError:
            return

        src = '\n'.join(lines)
        show_tac = src.strip().startswith(':tac')
        if show_tac:
            src = src.strip()[4:].strip()

        print(run_source(src, show_tac=show_tac), end='')


def main():
    args = sys.argv[1:]
    if not args:
        repl()
        return

    show_tac = '--tac' in args
    files = [a for a in args if not a.startswith('--')]
    if not files:
        print("Usage: python main.py [--tac] <file.pl>")
        sys.exit(1)

    with open(files[0]) as f:
        src = f.read()

    output = run_source(src, show_tac=show_tac)
    print(output, end='')


if __name__ == '__main__':
    main()
