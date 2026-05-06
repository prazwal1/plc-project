# PL — A Statically Typed Programming Language

A small, fully working programming language built from scratch for the PL-26 course project.  
The pipeline goes: **source text → Lexer → Parser → Type Checker → TAC Generator → Interpreter**.

---

## Language Features

| Feature | Detail |
|---|---|
| **Types** | `int`, `float`, `bool`, `string` |
| **Typing** | Static — inferred from first assignment, no declarations needed |
| **Int operators** | `+` `-` `*` `/` — standard precedence (`*`/`/` before `+`/`-`) |
| **Float operators** | `+.` `-.` `*.` `/.` — same precedence rules |
| **String operator** | `^` (concatenation) |
| **Boolean expressions** | `=` (equality), `<>` (inequality) between two arithmetic values |
| **Statements** | Assignment, `if-then-else`, `while-do` |
| **Functions** | Value parameter passing, recursion |
| **Built-in** | `print()` — works with any type |

---

## Quick Start

```bash
# Install dependencies (once)
uv sync

# Run a program
python main.py examples/ex_functions.pl

# Dump three-address code instead of running
python main.py --tac examples/ex_functions.pl

# Interactive REPL
python main.py
```

---

## Project Structure

```
.
├── lexer.py          # Tokeniser (sly)
├── parser.py         # LALR(1) parser → AST  (sly)
├── ast_nodes.py      # AST node dataclasses
├── type_checker.py   # Static type checker / type inferencer
├── tac.py            # Three-address code generator
├── interpreter.py    # TAC interpreter
├── main.py           # Pipeline driver + REPL
└── ex_*.pl           # Example programs (one per feature)
```

---

## Example Programs

| File | Demonstrates |
|---|---|
| `ex_types.pl` | int, float, bool, string — inference, no declarations |
| `ex_arithmetic.pl` | Operator precedence, separate int/float/string ops |
| `ex_boolean.pl` | `=` and `<>` comparisons |
| `ex_if_else.pl` | if-then-else |
| `ex_while.pl` | while loop |
| `ex_functions.pl` | Functions, recursion, value passing |

---

## Language Grammar (summary)

```
program    → def* stmt*

def        → def type id ( params ) { stmt* }
params     → type id (, type id)*

stmt       → id = expr ;
           | if bexpr then { stmt* } else { stmt* } ;
           | while bexpr do { stmt* } ;
           | print ( bexpr ) ;
           | return bexpr ;

bexpr      → expr = expr | expr <> expr | expr

expr       → expr (+|-|+.|-.|^) term | term
term       → term (*|/|*.|/.) atom | atom
atom       → int_lit | float_lit | string_lit | true | false
           | id | id ( args ) | ( bexpr )

type       → int | float | bool | string
```

---

## Type Inference Algorithm

Variables have no explicit type annotation. The checker infers the type from the **first assignment** and locks it:

1. Scan all `def` headers → populate the function signature table.
2. For each function body, bind parameters then walk statements.
3. For each `id = expr`: infer type of `expr`; if `id` is new, record that type; if `id` exists, verify it matches.
4. For binary operators, the allowed operand types are fixed (no overloading):
   - `+  -  *  /`   → both sides must be `int`, result `int`
   - `+. -. *. /.`  → both sides must be `float`, result `float`
   - `^`            → both sides must be `string`, result `string`
   - `=  <>`        → both sides same `int`/`float`, result `bool`
5. `if`/`while` conditions must type-check to `bool`.
6. `return` type must match the declared function return type.

---

## Three-Address Code

The TAC generator flattens the AST into simple instructions with temporaries `t0, t1, …`:

```
t0 = 6           # load literal
n = t0
param n
t1 = call factorial [1]   # call with 1 arg
result = t1
print result
```

Control flow uses labelled jumps:

```
L0:
    t2 = 6
    t3 = i <> t2
    ifnot t3 goto L1
    ...
    goto L0
L1:
```

Run `python main.py --tac <file>` to see the full TAC for any program.
