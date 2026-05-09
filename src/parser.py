"""
parser.py - Syntax analyzer (Parser) for the PL programming language.

This file uses the 'sly' library to construct an LALR(1) parser. It takes the
stream of tokens from the Lexer and matches them against the formal grammar rules.
If matched, it executes grammar action functions to construct an Abstract Syntax
Tree (AST) made of nodes defined in 'ast_nodes.py'.

PREPARE FOR THE TEST:
- Precedence is defined by the depth/layering of the rules:
  bexpr (comparisons) -> expr (additive/concatenation) -> term (multiplicative) -> atom (base values).
- Left-recursive grammar (e.g., `expr "+" term` where expr is on the left) is natively
  handled by LALR(1) parsers (like Yacc/sly) and produces left-associative parsing.
"""

from sly import Parser
from .lexer import PLLexer
from . import ast_nodes as A


class PLParser(Parser):
    tokens = PLLexer.tokens

    # SLY global precedence setting.
    # We make '=' and 'NE' (<>) non-associative ('nonassoc') to reject expressions
    # like 'a = b = c' at the parser level, ensuring comparison is only between two sides.
    precedence = (
        ('nonassoc', '=', NE),
    )

    # ------------------------------------------------------------------
    # Top-level entry point: program
    # ------------------------------------------------------------------

    @_('def_list stmt_list')
    def program(self, p):
        # A program is a list of function definitions followed by main statements
        return A.Program(funcs=p.def_list, main=p.stmt_list)

    # ------------------------------------------------------------------
    # Function definitions
    # ------------------------------------------------------------------

    @_('def_ def_list')
    def def_list(self, p):
        # Recursively build list of function definitions: [first] + [rest...]
        return [p.def_] + p.def_list

    @_('')
    def def_list(self, p):
        # Base case: empty function list
        return []

    # Note: `def` is a Python keyword, so we use `def_` as the SLY rule name.
    @_('DEF type ID "(" param_list ")" "{" stmt_list "}"')
    def def_(self, p):
        # Matches a function with parameters (e.g., def int foo(int x) { ... })
        return A.FuncDef(return_type=p.type, name=p.ID,
                         params=p.param_list, body=p.stmt_list)

    @_('DEF type ID "(" ")" "{" stmt_list "}"')
    def def_(self, p):
        # Matches a function with NO parameters (e.g., def int foo() { ... })
        return A.FuncDef(return_type=p.type, name=p.ID,
                         params=[], body=p.stmt_list)

    @_('type ID "," param_list')
    def param_list(self, p):
        # Multiple parameters: type name, rest... (e.g., int x, float y)
        return [A.Param(type=p.type, name=p.ID)] + p.param_list

    @_('type ID')
    def param_list(self, p):
        # Single parameter: type name (e.g., int x)
        return [A.Param(type=p.type, name=p.ID)]

    # Map parsed type keywords to standard type string tags
    @_('INT')
    def type(self, p): return 'int'

    @_('FLOAT')
    def type(self, p): return 'float'

    @_('BOOL')
    def type(self, p): return 'bool'

    @_('STRING')
    def type(self, p): return 'string'

    # ------------------------------------------------------------------
    # Statement lists
    # ------------------------------------------------------------------

    @_('stmt ";" stmt_list')
    def stmt_list(self, p):
        # Statements are separated by semicolons: [first] + [rest...]
        return [p.stmt] + p.stmt_list

    @_('')
    def stmt_list(self, p):
        # Base case: empty statement list
        return []

    # ------------------------------------------------------------------
    # Individual statements
    # ------------------------------------------------------------------

    @_('ID "=" bexpr')
    def stmt(self, p):
        # Assignment statement (e.g., x = 5)
        return A.Assign(name=p.ID, expr=p.bexpr)

    @_('IF bexpr THEN "{" stmt_list "}" ELSE "{" stmt_list "}"')
    def stmt(self, p):
        # If-then-else statement. Note p.stmt_list0 and p.stmt_list1 map
        # to the first and second occurrences of `stmt_list` in the rule.
        return A.If(cond=p.bexpr,
                    then_block=p.stmt_list0,
                    else_block=p.stmt_list1)

    @_('WHILE bexpr DO "{" stmt_list "}"')
    def stmt(self, p):
        # While-do loop statement
        return A.While(cond=p.bexpr, body=p.stmt_list)

    @_('PRINT "(" bexpr ")"')
    def stmt(self, p):
        # Print statement (e.g., print(x))
        return A.Print(expr=p.bexpr)

    @_('RETURN bexpr')
    def stmt(self, p):
        # Return statement inside function bodies
        return A.Return(expr=p.bexpr)

    # ------------------------------------------------------------------
    # Boolean expression (= or <>) -- Lowest expression layer (evaluated last)
    # ------------------------------------------------------------------

    @_('expr "=" expr')
    def bexpr(self, p):
        # Equality comparison
        return A.Compare(op='=', left=p.expr0, right=p.expr1)

    @_('expr NE expr')
    def bexpr(self, p):
        # Inequality comparison (<>)
        return A.Compare(op='<>', left=p.expr0, right=p.expr1)

    @_('expr')
    def bexpr(self, p):
        # Fall-through: a regular expression without comparison is still a valid boolean expr
        return p.expr

    # ------------------------------------------------------------------
    # Additive expressions (+, -, float ops, string concatenation)
    # ------------------------------------------------------------------

    @_('expr "+" term')
    def expr(self, p): return A.BinOp(op='+', left=p.expr, right=p.term)

    @_('expr "-" term')
    def expr(self, p): return A.BinOp(op='-', left=p.expr, right=p.term)

    @_('expr FPLUS term')
    def expr(self, p): return A.BinOp(op='+.', left=p.expr, right=p.term)

    @_('expr FMINUS term')
    def expr(self, p): return A.BinOp(op='-.', left=p.expr, right=p.term)

    @_('expr "^" term')
    def expr(self, p): return A.BinOp(op='^', left=p.expr, right=p.term)

    @_('term')
    def expr(self, p): return p.term

    # ------------------------------------------------------------------
    # Multiplicative expressions (*, /, float ops) -- Evaluated before expr
    # ------------------------------------------------------------------

    @_('term "*" atom')
    def term(self, p): return A.BinOp(op='*', left=p.term, right=p.atom)

    @_('term "/" atom')
    def term(self, p): return A.BinOp(op='/', left=p.term, right=p.atom)

    @_('term FTIMES atom')
    def term(self, p): return A.BinOp(op='*.', left=p.term, right=p.atom)

    @_('term FDIVIDE atom')
    def term(self, p): return A.BinOp(op='/.', left=p.term, right=p.atom)

    @_('atom')
    def term(self, p): return p.atom

    # ------------------------------------------------------------------
    # Atoms (Base level - constants, identifiers, function calls, sub-expressions)
    # ------------------------------------------------------------------

    @_('INT_LIT')
    def atom(self, p): return A.IntLit(value=p.INT_LIT)

    @_('FLOAT_LIT')
    def atom(self, p): return A.FloatLit(value=p.FLOAT_LIT)

    @_('STRING_LIT')
    def atom(self, p): return A.StringLit(value=p.STRING_LIT)

    @_('TRUE')
    def atom(self, p): return A.BoolLit(value=True)

    @_('FALSE')
    def atom(self, p): return A.BoolLit(value=False)

    @_('ID')
    def atom(self, p): return A.Var(name=p.ID)

    @_('ID "(" arg_list ")"')
    def atom(self, p): return A.Call(name=p.ID, args=p.arg_list)

    @_('ID "(" ")"')
    def atom(self, p): return A.Call(name=p.ID, args=[])

    @_('"(" bexpr ")"')
    def atom(self, p): return p.bexpr

    # Argument list helper for function calls (e.g., foo(x, y + 1, true))
    @_('bexpr "," arg_list')
    def arg_list(self, p): return [p.bexpr] + p.arg_list

    @_('bexpr')
    def arg_list(self, p): return [p.bexpr]

    # ------------------------------------------------------------------
    # Error reporting and tracking
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self.errors = []

    def error(self, tok):
        # Triggered when there's an illegal token sequence
        if tok is None:
            msg = "[parse error] unexpected end of input"
        else:
            msg = (f"[parse error] line {tok.lineno}: unexpected token "
                   f"{tok.type}({tok.value!r})")
        self.errors.append(msg)
        print(msg)

    def parse(self, tokens):
        # Reset errors list before parsing to prevent accumulation across multiple runs
        self.errors = []
        return super().parse(tokens)


# ---------------------------------------------------------------------------
# Pretty printer for AST inspection
# ---------------------------------------------------------------------------
def pretty(node, indent=0):
    pad = '  ' * indent
    if isinstance(node, list):
        if not node:
            return pad + '[]'
        return '\n'.join(pretty(n, indent) for n in node)
    if hasattr(node, '__dataclass_fields__'):
        cls = type(node).__name__
        lines = [f'{pad}{cls}']
        for fname in node.__dataclass_fields__:
            v = getattr(node, fname)
            if isinstance(v, list):
                lines.append(f'{pad}  {fname}:')
                if v:
                    lines.append(pretty(v, indent + 2))
                else:
                    lines.append(f'{pad}    []')
            elif hasattr(v, '__dataclass_fields__'):
                lines.append(f'{pad}  {fname}:')
                lines.append(pretty(v, indent + 2))
            else:
                lines.append(f'{pad}  {fname}: {v!r}')
        return '\n'.join(lines)
    return pad + repr(node)


# ---------------------------------------------------------------------------
# Local testing on predefined programs (runs when file is executed directly)
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    sources = [
        # Simple program
        '''
        x = 5;
        y = x + 3;
        print(y);
        ''',
        # Function with recursion
        '''
        def int factorial(int n) {
            if n = 0 then { return 1; } else { return n * factorial(n - 1); };
        }
        x = 5;
        y = factorial(x);
        print(y);
        ''',
    ]

    lex = PLLexer()
    par = PLParser()
    for i, src in enumerate(sources, 1):
        print(f'\n===== Program {i} =====')
        print(src.strip())
        print('--- AST ---')
        result = par.parse(lex.tokenize(src))
        print(pretty(result))
