"""
lexer.py - Lexical analyzer (Tokeniser) for the PL programming language.

This file uses the 'sly' library to convert a raw string of source code into 
a sequence of tokens (words/symbols) that the Parser can understand.

HOW SLY LEXING WORKS:
1. SLY reads regex patterns assigned to token names (e.g., FLOAT_LIT = r'\d+\.\d+').
2. SLY matches characters from left to right.
3. Order matters: SLY prioritises rules in the order they are defined in the class.
4. Longest-match-wins: SLY always tries to match the longest possible string.
"""

from sly import Lexer


class PLLexer(Lexer):
    # --- Token names (MUST be uppercase for SLY to register them) -----------
    tokens = {
        # Literals (concrete values)
        FLOAT_LIT, INT_LIT, STRING_LIT,
        
        # Identifiers (variable and function names)
        ID,
        
        # Keywords (special reserved words in the language)
        DEF, INT, FLOAT, BOOL, STRING,
        IF, THEN, ELSE, WHILE, DO,
        TRUE, FALSE,
        PRINT, RETURN,
        
        # Multi-character operators (single-char operators are handled in literals)
        FPLUS, FMINUS, FTIMES, FDIVIDE,    # +. -. *. /. (Float arithmetic)
        NE,                                  # <> (Inequality comparison)
    }

    # Single-character tokens that do not need regex (SLY auto-matches these as tokens)
    literals = {'+', '-', '*', '/', '^', '=', '(', ')', '{', '}', ',', ';'}

    # Characters to ignore completely (spaces and tabs)
    ignore = ' \t'
    
    # Ignore comments starting with '#' until the end of the line
    ignore_comment = r'\#.*'
    
    # Separate rule to track and ignore newlines so we can count lines for error reporting
    ignore_newline = r'\n+'

    # --- Token Regular Expressions (Priority / Order is CRITICAL here) --------

    # CRITICAL PRIORITY 1: FLOAT must be defined before INT.
    # Otherwise, '3.14' would be matched as: INT(3), Literals('.'), INT(14).
    # Defining FLOAT first ensures the whole '3.14' is matched as a FLOAT_LIT.
    FLOAT_LIT = r'\d+\.\d+'
    INT_LIT   = r'\d+'

    # Match string literal: anything inside double quotes "..."
    # Supports backslash escape sequences like \" or \\.
    STRING_LIT = r'"([^"\\]|\\.)*"'

    # CRITICAL PRIORITY 2: Dotted float operators must be defined before ID or plain operators.
    # Longest-match-wins ensures '+.' is matched as FPLUS rather than '+' and an illegal '.' character.
    FPLUS    = r'\+\.'
    FMINUS   = r'-\.'
    FTIMES   = r'\*\.'
    FDIVIDE  = r'/\.'

    # Inequality operator (<>) -- must be defined before '<' or '>' if we add them later.
    NE       = r'<>'

    # Identifiers: Must start with a letter, followed by any letters, digits, or underscores.
    ID       = r'[A-Za-z][A-Za-z0-9_]*'

    # ------------------------------------------------------------------------
    # Keyword Mapping (The SLY ID-dictionary trick)
    # ------------------------------------------------------------------------
    # SLY's ID regex matches reserved keywords like 'if', 'while', or 'int' too.
    # To prevent 'if' from being treated as a variable name, we map those specific
    # lexemes directly to their corresponding keyword token types.
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

    # ------------------------------------------------------------------------
    # Token Actions (Functions executed when a token is matched)
    # ------------------------------------------------------------------------

    def INT_LIT(self, t):
        # Convert matched string (e.g., "123") to a Python integer
        t.value = int(t.value)
        return t

    def FLOAT_LIT(self, t):
        # Convert matched string (e.g., "3.14") to a Python float
        t.value = float(t.value)
        return t

    def STRING_LIT(self, t):
        # Strip surrounding double quotes (first and last characters)
        raw = t.value[1:-1]
        # Replace escaped sequences with actual characters
        t.value = raw.replace('\\"', '"').replace('\\\\', '\\').replace('\\n', '\n')
        return t

    def ignore_newline(self, t):
        # Increment internal line count so errors report the correct line number
        self.lineno += t.value.count('\n')

    def error(self, t):
        # Fallback when an unrecognized character is encountered (e.g., @, $, or %)
        print(f"[lex error] line {self.lineno}: illegal character {t.value[0]!r}")
        self.index += 1


# ---------------------------------------------------------------------------
# Interactive Test Execution (Only runs when executing lexer.py directly)
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
