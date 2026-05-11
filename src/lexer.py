"""
lexer.py - Lexical analyzer for the project language.

Token specification follows the lecture-note style: regular definitions for
each token, with special care for the multi-char operators that include '.'
(+. -. *. /.). The order of token rules matters: longest match wins, and
sly tries rules in the order they are declared, so float literals must be
declared before integer literals, and dotted operators before plain ones.

Run as a script to test the lexer interactively or on a file.
"""
from sly import Lexer


class PLLexer(Lexer):
    # --- Token names (uppercase identifiers required by sly) ----------------
    tokens = {
        # Literals
        INT_LIT, FLOAT_LIT,  STRING_LIT,
        # Identifiers and keywords
        ID,
        DEF, INT, FLOAT, BOOL, STRING,
        IF,
          THEN, ELSE, WHILE, DO,
        TRUE, FALSE,
        PRINT, RETURN,
        # Multi-character operators
        FPLUS, FMINUS, FTIMES, FDIVIDE,    # +. -. *. /.
        NE,                                  # <>
        # Single-character operators handled via `literals`
    }

    # Single-character tokens that don't need a regex (sly literal feature)
    literals = {'+', '-', '*', '/', '^', '=', '(', ')', '{', '}', ',', ';'}

    # Things to ignore: spaces, tabs, and comments
    ignore = ' \t'
    ignore_newline = r'\n+'
    ignore_comment = r'\#.*'

    # --- Token regular expressions (declared in priority order) -------------

    # IMPORTANT: float must come before int, otherwise '3.14' would lex as
    #   INT_LIT(3), '.', INT_LIT(14) which is a parse error.
    FLOAT_LIT = r'\d+\.\d+'
    INT_LIT   = r'\d+'

    # String literal: anything between double quotes that isn't a quote.
    # We strip the quotes and unescape \" and \\ in the action below.
    STRING_LIT = r'"([^"\\]|\\.)*"'

    # Dotted operators MUST be declared before the plain ones, because sly
    # uses longest-match-wins and we want '+.' to win over '+'.
    FPLUS    = r'\+\.'
    FMINUS   = r'-\.'
    FTIMES   = r'\*\.'
    FDIVIDE  = r'/\.'

    # Inequality (<>) -- same idea, declare before any single-char operator
    # that could start a prefix.
    NE       = r'<>'

    # Identifier: letter (letter | digit | _)*
    ID       = r'[A-Za-z][A-Za-z0-9_]*'
    

    # ------------------------------------------------------------------------
    # Token actions: convert lexeme strings into Python values where useful,
    # and remap identifiers that match keywords to their proper token type.
    # ------------------------------------------------------------------------

    # Map keyword identifiers onto their token types. ID's regex would match
    # them all otherwise -- this is the standard Lex/sly trick.
    ID['def']    = DEF
    ID['int']    = INT
    ID['float']  = FLOAT
    ID['bool']   = BOOL
    ID['string'] = STRING
    ID['if']     = IF
    ID['then']   = THEN
    ID['else']   = ELSE
    ID['while']  = WHILE
    ID['do']     = DO
    ID['true']   = TRUE
    ID['false']  = FALSE
    ID['print']  = PRINT
    ID['return'] = RETURN

    def INT_LIT(self, t):
        t.value = int(t.value)
        return t

    def FLOAT_LIT(self, t):
        t.value = float(t.value)
        return t

    def STRING_LIT(self, t):
        # Strip surrounding quotes and unescape simple sequences.
        raw = t.value[1:-1]
        t.value = raw.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
        return t

    def ignore_newline(self, t):
        # Track line numbers for better error messages later.
        self.lineno += t.value.count('\n')

    def error(self, t):
        print(f"[lex error] line {self.lineno}: illegal character {t.value[0]!r}")
        self.index += 1


# ---------------------------------------------------------------------------
# Manual test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    src = '''
    def int factorial(int n) {
        if n = 0 then { return 1; } else { return n * factorial(n - 1); };
    }
    x = 5;
    y = factorial(x);
    print("Result is: " ^ "see y");
    print(y);
    pi = 3.14;
    z = pi *. 2.0;
    '''
    lexer = PLLexer()
    for tok in lexer.tokenize(src):
        print(f"  {tok.type:12s} {tok.value!r}")
