"""
test_complex.py - End-to-end: a non-trivial program through lex+parse.
"""
from lexer import PLLexer
from parser import PLParser, pretty

src = '''
# Compute the n-th Fibonacci number and a label string.

def int fib(int n) {
    if n = 0 then {
        return 0;
    } else {
        if n = 1 then {
            return 1;
        } else {
            return fib(n - 1) + fib(n - 2);
        };
    };
}

def string greet(string name) {
    return "hello, " ^ name ^ "!";
}

def float circle_area(float r) {
    return 3.14159 *. r *. r;
}

# Main program
n = 10;
result = fib(n);
msg = greet("world");
area = circle_area(2.5);

print(msg);
print(result);
print(area);

# Iterative loop
i = 0;
total = 0;
while i <> n do {
    total = total + i;
    i = i + 1;
};
print(total);
'''

lex = PLLexer()
par = PLParser()
ast = par.parse(lex.tokenize(src))

if par.errors:
    print(f"\n{len(par.errors)} parse error(s)")
else:
    print("Parsed successfully!\n")
    print(pretty(ast))
