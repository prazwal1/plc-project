"""
main.py - Driver for the programming language.

Pipeline:
  source text
    -> Lexer      (lexer.py)
    -> Parser     (parser.py)      -> AST
    -> TypeChecker (type_checker.py) -> annotated AST
    -> TACGenerator (tac.py)       -> TAC instruction list
    -> Interpreter  (interpreter.py) -> output

Usage:
  python main.py <source_file.pl>   -- run a program file
  python main.py --tac <file>       -- print TAC instead of running
  python main.py                    -- interactive REPL
"""

import sys
from lexer import PLLexer
from parser import PLParser
from type_checker import TypeChecker, TypeErrorException
from tac import TACGenerator, pretty_tac
from interpreter import make_interpreter


def run_source(src: str, show_tac: bool = False):
    lexer  = PLLexer()
    parser = PLParser()

    # 1. Parse
    tokens = lexer.tokenize(src)
    program = parser.parse(tokens)
    if program is None or parser.errors:
        print("Parsing failed.")
        return

    # 2. Type check
    checker = TypeChecker()
    try:
        checker.check(program)
    except TypeErrorException as e:
        print(e)
        return

    # 3. Generate TAC
    gen = TACGenerator()
    instructions = gen.generate(program)

    if show_tac:
        print(pretty_tac(instructions))
        return

    # 4. Interpret
    interp = make_interpreter(instructions, program)
    interp.run()


def repl():
    lexer  = PLLexer()
    parser = PLParser()
    checker = TypeChecker()

    print("PL interpreter. Type your program, end with a blank line.")
    print("Commands:  :tac  (print TAC),  :quit  (exit)\n")

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
        show_tac = False
        if src.strip().startswith(':tac'):
            show_tac = True
            src = src.strip()[4:].strip()

        run_source(src, show_tac=show_tac)


def main():
    args = sys.argv[1:]
    if not args:
        repl()
        return

    show_tac = '--tac' in args
    files = [a for a in args if not a.startswith('--')]

    if not files:
        print("Usage: python main.py [--tac] <source_file>")
        sys.exit(1)

    with open(files[0]) as f:
        src = f.read()

    run_source(src, show_tac=show_tac)


if __name__ == '__main__':
    main()
