"""
test_errors.py - Verify the parser rejects malformed programs gracefully.

These should all produce parse errors, NOT crash the parser.
"""
from lexer import PLLexer
from parser import PLParser, pretty

bad_programs = [
    ('missing semicolon',          'x = 5\ny = 6;'),
    ('mismatched brace',           'x = 5; if true then { x = 1; else { x = 2; };'),
    ('boolean inside arithmetic',  'x = (1 = 2) + 3;'),
    ('chained equality (we want this rejected)', 'x = a = b = c;'),
    ('illegal char',               'x = 5 @ 3;'),
    ('keyword as id',              'x = if;'),
    ('empty parens for op',        'x = 5 + ;'),
]

lex = PLLexer()
par = PLParser()

for label, src in bad_programs:
    print(f'\n--- {label} ---')
    print(f'  source: {src!r}')
    try:
        result = par.parse(lex.tokenize(src))
        if par.errors:
            print(f'  -> rejected ({len(par.errors)} parse error(s))')
        elif result is None:
            print('  -> rejected (parser returned None)')
        else:
            print('  -> ACCEPTED (this is fine if it should be a TYPE error, not a syntax error)')
    except Exception as e:
        print(f'  -> exception: {type(e).__name__}: {e}')
