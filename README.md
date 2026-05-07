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

# Launch the online compiler (browser UI)
python web/app.py
# then open http://localhost:5000
```

---

## Online Compiler

A browser-based IDE is included in `web/`.  
Start it with:

```bash
python web/app.py
```

Open **http://localhost:5000** to get:

- **Left pane** — CodeMirror editor with syntax highlighting, line numbers, and bracket matching
- **Right pane** — program output (or TAC dump when *Show TAC* is checked)
- **Load example** dropdown — loads any file from `examples/` directly into the editor
- **Ctrl+Enter / Cmd+Enter** — keyboard shortcut to run without leaving the editor

---

## Project Structure

```
.
├── src/
│   ├── ast_nodes.py      # AST node dataclasses
│   ├── lexer.py          # Tokeniser (sly)
│   ├── parser.py         # LALR(1) parser → AST (sly)
│   ├── type_checker.py   # Static type checker / type inferencer
│   ├── tac.py            # Three-address code generator
│   └── interpreter.py    # TAC interpreter
├── web/
│   ├── app.py            # Flask backend (/run, /example/<name>)
│   └── templates/
│       └── index.html    # Single-page compiler UI
├── examples/
│   ├── ex_types.pl
│   ├── ex_arithmetic.pl
│   ├── ex_boolean.pl
│   ├── ex_if_else.pl
│   ├── ex_while.pl
│   └── ex_functions.pl
├── tests/
│   ├── test_complex.py
│   └── test_errors.py
├── main.py               # CLI driver + REPL
└── pyproject.toml
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
t0 = 6
n = t0
param n
t1 = call factorial [1]
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

Run `python main.py --tac <file>` or tick *Show TAC* in the web UI to inspect the generated code.
