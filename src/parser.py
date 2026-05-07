"""
parser.py - Syntax analyzer for the project language.

Implements the layered grammar designed in the previous step:

    program    -> def_list stmt_list
    def_list   -> def def_list | (empty)
    def        -> DEF type ID ( param_list ) { stmt_list }
                | DEF type ID (             ) { stmt_list }
    param_list -> type ID , param_list | type ID
    type       -> INT | FLOAT | BOOL | STRING

    stmt_list  -> stmt ; stmt_list | (empty)
    stmt       -> ID = bexpr
                | IF bexpr THEN { stmt_list } ELSE { stmt_list }
                | WHILE bexpr DO { stmt_list }
                | PRINT ( bexpr )
                | RETURN bexpr

    bexpr      -> expr = expr | expr <> expr | expr
    expr       -> expr +  term  | expr -  term
                | expr +. term  | expr -. term
                | expr ^  term
                | term
    term       -> term *  atom  | term /  atom
                | term *. atom  | term /. atom
                | atom
    atom       -> INT_LIT | FLOAT_LIT | STRING_LIT
                | TRUE | FALSE
                | ID
                | ID ( arg_list ) | ID ( )
                | ( bexpr )
    arg_list   -> bexpr , arg_list | bexpr

The grammar is left-recursive on `expr` and `term` to give standard
left-associative parsing of arithmetic. sly handles left recursion natively
because it uses an LALR(1) parser, just like yacc.

Each grammar action constructs an AST node from ast_nodes.py.
"""
from sly import Parser
from .lexer import PLLexer
from . import ast_nodes as A


class PLParser(Parser):
    tokens = PLLexer.tokens

    # We make the *boolean* operators non-associative so that the parser
    # rejects strings like  a = b = c  as ambiguous (which we want -- the
    # brief says boolean expressions are between TWO arithmetic expressions).
    # Arithmetic operators are left-associative because the grammar itself
    # is left-recursive, so we don't strictly need precedence directives.
    precedence = (
        ('nonassoc', '=', NE),
    )

    # ------------------------------------------------------------------
    # Top-level program
    # ------------------------------------------------------------------

    @_('def_list stmt_list')
    def program(self, p):
        return A.Program(funcs=p.def_list, main=p.stmt_list)

    # ------------------------------------------------------------------
    # Function definitions
    # ------------------------------------------------------------------

    @_('def_ def_list')
    def def_list(self, p):
        return [p.def_] + p.def_list

    @_('')
    def def_list(self, p):
        return []

    # NB: `def` is a Python keyword so we use `def_` as the rule name.
    # The name on the LEFT of @_ doesn't affect the grammar, only the rule's
    # symbol name. We call it 'def_' here.
    @_('DEF type ID "(" param_list ")" "{" stmt_list "}"')
    def def_(self, p):
        return A.FuncDef(return_type=p.type, name=p.ID,
                         params=p.param_list, body=p.stmt_list)

    @_('DEF type ID "(" ")" "{" stmt_list "}"')
    def def_(self, p):
        return A.FuncDef(return_type=p.type, name=p.ID,
                         params=[], body=p.stmt_list)

    @_('type ID "," param_list')
    def param_list(self, p):
        return [A.Param(type=p.type, name=p.ID)] + p.param_list

    @_('type ID')
    def param_list(self, p):
        return [A.Param(type=p.type, name=p.ID)]

    @_('INT')
    def type(self, p): return 'int'

    @_('FLOAT')
    def type(self, p): return 'float'

    @_('BOOL')
    def type(self, p): return 'bool'

    @_('STRING')
    def type(self, p): return 'string'

    # ------------------------------------------------------------------
    # Statement list
    # ------------------------------------------------------------------

    @_('stmt ";" stmt_list')
    def stmt_list(self, p):
        return [p.stmt] + p.stmt_list

    @_('')
    def stmt_list(self, p):
        return []

    # ------------------------------------------------------------------
    # Individual statements
    # ------------------------------------------------------------------

    @_('ID "=" bexpr')
    def stmt(self, p):
        return A.Assign(name=p.ID, expr=p.bexpr)

    @_('IF bexpr THEN "{" stmt_list "}" ELSE "{" stmt_list "}"')
    def stmt(self, p):
        return A.If(cond=p.bexpr,
                    then_block=p.stmt_list0,
                    else_block=p.stmt_list1)

    @_('WHILE bexpr DO "{" stmt_list "}"')
    def stmt(self, p):
        return A.While(cond=p.bexpr, body=p.stmt_list)

    @_('PRINT "(" bexpr ")"')
    def stmt(self, p):
        return A.Print(expr=p.bexpr)

    @_('RETURN bexpr')
    def stmt(self, p):
        return A.Return(expr=p.bexpr)

    # ------------------------------------------------------------------
    # Boolean expression (= or <>) -- always returns bool
    # ------------------------------------------------------------------

    @_('expr "=" expr')
    def bexpr(self, p):
        return A.Compare(op='=', left=p.expr0, right=p.expr1)

    @_('expr NE expr')
    def bexpr(self, p):
        return A.Compare(op='<>', left=p.expr0, right=p.expr1)

    @_('expr')
    def bexpr(self, p):
        return p.expr

    # ------------------------------------------------------------------
    # Arithmetic / string concatenation expression (additive level)
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
    # Multiplicative level
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
    # Atoms
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

    @_('bexpr "," arg_list')
    def arg_list(self, p): return [p.bexpr] + p.arg_list

    @_('bexpr')
    def arg_list(self, p): return [p.bexpr]

    # ------------------------------------------------------------------
    # Error reporting
    # ------------------------------------------------------------------

    def __init__(self):
        super().__init__()
        self.errors = []

    def error(self, tok):
        if tok is None:
            msg = "[parse error] unexpected end of input"
        else:
            msg = (f"[parse error] line {tok.lineno}: unexpected token "
                   f"{tok.type}({tok.value!r})")
        self.errors.append(msg)
        print(msg)

    def parse(self, tokens):
        # Reset error state for each call so the same parser can be reused.
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
# Manual test
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
        # Float arithmetic and string concatenation
        '''
        def float c2f(float c) {
            return c *. 1.8 +. 32.0;
        }
        temp = 100.0;
        msg = "the answer is ";
        result = c2f(temp);
        print(msg ^ "computed");
        print(result);
        ''',
        # While loop
        '''
        i = 0;
        sum = 0;
        while i <> 10 do {
            sum = sum + i;
            i = i + 1;
        };
        print(sum);
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
