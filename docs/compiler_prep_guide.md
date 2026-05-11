# Compiler Evaluation & Test Preparation Guide

This guide is designed to help you prepare for the compiler project evaluation/test section. It details how language changes propagate through the 6-stage pipeline of the **PL** programming language, lists the most common hands-on modification tasks, and compiles core theoretical questions you may be asked.

Ask yourself:
1. does it introduce a new character or word? Yes: Edit lexer.py
2. does it have structure? Add a database to ast_nodes.py and add a grammar rule in parser.py
3. doest it have meaning/logic? Add logic to type_checker.py
4. does it have rules about types? Add logic to type_checker.py with isinstance checking.
5. does it change execution? edit tac.py (for structure flatter) and interpreter.py (for dynamic operation result).
6. Does it requireTAC generation? Add TAC generation to tac.py
7. Does it require execution? Add execution logic to interpreter.py

---

## The 6-Stage Pipeline Overview

$$\text{Source Text} \rightarrow \text{Lexer} \rightarrow \text{Parser} \rightarrow \text{Type Checker} \rightarrow \text{TAC Generator} \rightarrow \text{Interpreter}$$

Every feature addition follows this exact flow:
1. **Lexical analysis (`lexer.py`)**: Tokenize the new operator, literal, or keyword.
2. **Syntactic analysis (`parser.py`)**: Define the grammar rules and construct the corresponding AST node.
3. **AST definition (`ast_nodes.py`)**: Ensure there is a dataclass representing the new syntactic construct.
4. **Static type-checking (`type_checker.py`)**: Check and infer types, annotating the AST node with its resolved type.
5. **Intermediate code generation (`tac.py`)**: Flatten the AST node into flat Three-Address Code (TAC) instructions.
6. **Execution (`interpreter.py`)**: Evaluate the flat TAC instructions within the interpreter's environments.

---

## 4 Most Likely Hands-On Coding Tasks

If you are asked to edit the codebase to implement a new feature during the evaluation, it will likely be one of the following tasks:

### Task 1: Adding Comparison Operators (e.g., `<` or `>`)

Since `=` and `<>` are already implemented, adding `<` (less than) is highly common.

1. **`src/lexer.py`**:
   Add `'<'` to the `literals` set (around line 33):
   ```python
   literals = {'+', '-', '*', '/', '^', '=', '(', ')', '{', '}', ',', ';', '<'}
   ```

2. **`src/parser.py`**:
   * Add `'<'` to the `precedence` directive to make it non-associative (around line 55):
     ```python
     precedence = (
         ('nonassoc', '=', NE, '<'),
     )
     ```
   * Add a parsing rule under the `bexpr` section (around line 160):
     ```python
     @_('expr "<" expr')
     def bexpr(self, p):
         return A.Compare(op='<', left=p.expr0, right=p.expr1)
     ```

3. **`src/type_checker.py`**:
   * **No changes needed here!** The `_infer_compare` method already genericizes comparisons for `'int'` and `'float'`.

4. **`src/interpreter.py`**:
   Add the evaluation logic to `_apply_op` (around line 192):
   ```python
   if op == '<':   return l < r
   ```

---

### Task 2: Adding an Integer-Only Operator (e.g., Modulo `%`)

Adding an operator like `%` tests your understanding of grammar precedence layers and static type-checking rules.

1. **`src/lexer.py`**:
   Add `'%'` to the `literals` set (around line 33).

2. **`src/parser.py`**:
   * Add a parsing rule under the `term` section (multiplicative level, around line 200):
     ```python
     @_('term "%" atom')
     def term(self, p): return A.BinOp(op='%', left=p.term, right=p.atom)
     ```

3. **`src/type_checker.py`**:
   * Add `'%'` to the integer operators set `_INT_OPS` (around line 181):
     ```python
     _INT_OPS = {'+', '-', '*', '/', '%'}
     ```

4. **`src/interpreter.py`**:
   Add the evaluation logic to `_apply_op` (around line 192):
   ```python
   if op == '%':
       if r == 0:
           raise RuntimeError_("Division by zero.")
       return l % r
   ```

---

### Task 3: Adding Unary Negation (e.g., `-x` or `-.x`)

Unlike binary subtraction (`a - b`), unary negation acts on a single operand.

1. **`src/ast_nodes.py`**:
   Define a new AST node:
   ```python
   @dataclass
   class UnaryOp:
       op: str  # '-' or '-.'
       expr: object
   ```

2. **`src/parser.py`**:
   Add unary rules under the `atom` section (giving it the highest precedence, around line 210):
   ```python
   @_('"-" atom')
   def atom(self, p): return A.UnaryOp(op='-', expr=p.atom)

   @_('FMINUS atom')
   def atom(self, p): return A.UnaryOp(op='-.', expr=p.atom)
   ```

3. **`src/type_checker.py`**:
   Add type-checking rules for `UnaryOp` in `_infer` (around line 175):
   ```python
   if isinstance(node, A.UnaryOp):
       t = self._check_expr(node.expr)
       if node.op == '-' and t != 'int':
           raise TypeErrorException("Unary '-' requires int.")
       if node.op == '-.' and t != 'float':
           raise TypeErrorException("Unary '-.' requires float.")
       return t
   ```

4. **`src/tac.py`**:
   Represent `-x` as `0 - x` in TAC (around line 175):
   ```python
   if isinstance(node, A.UnaryOp):
       expr_val = self._gen_expr(node.expr)
       t = self._new_temp()
       zero = Lit(0) if node.op == '-' else Lit(0.0)
       self._emit(BinOp(t, node.op, zero, expr_val))
       return t
   ```

---

### Task 4: Adding a `do-while` Loop Statement

Testing control-flow jump layout generation in TAC.

1. **`src/parser.py`**:
   * Add a parsing rule under the `stmt` section (around line 130):
     ```python
     @_('DO "{" stmt_list "}" WHILE bexpr')
     def stmt(self, p):
         return A.DoWhile(body=p.stmt_list, cond=p.bexpr)
     ```

2. **`src/type_checker.py`**:
   Add type-checking rules for `DoWhile` (checking that the condition evaluates to a boolean):
   ```python
   elif isinstance(stmt, A.DoWhile):
       ct = self._check_expr(stmt.cond)
       if ct != 'bool':
           raise TypeErrorException(f"Type error: do-while condition must be bool, got '{ct}'.")
       for s in stmt.body:
           self._check_stmt(s, expected_return)
   ```

3. **`src/tac.py`**:
   Generate the loop block where the body executes first, followed by a conditional jump back to the start:
   ```python
   elif isinstance(stmt, A.DoWhile):
       start_label = self._new_label()
       self._emit(Label(start_label))
       for s in stmt.body:
           self._gen_stmt(s)
       cond = self._gen_expr(stmt.cond)
       self._emit(JumpIf(cond, start_label))
   ```

---

## Theoretical Questions & Answers

### Q1: How does variable type-inference work and where are types locked in?
* **Answer**: We use a monomorphic type-inference strategy in `src/type_checker.py`. When a variable assignment is checked:
  1. We look up the variable name in the environment stack `var_env`.
  2. If it is **not found** (`existing is None`), we infer the type of the assigned expression and **lock/bind it** in the current scope using `self._define(stmt.name, t)`.
  3. If it **is found**, we verify that the type of the new assigned expression matches the locked type, raising a `TypeErrorException` on a mismatch.

### Q2: How does your Lexer handle ambiguous prefixes like `+.` vs `+` or `3.14` vs `3`?
* **Answer**: SLY resolves matches using a "longest match wins" strategy and prioritizes tokens in the order they are declared in `src/lexer.py`.
  * **Operators**: We declare dotted operators (`FPLUS`, `FMINUS`, etc.) before single-character literals, so `+.` is scanned as a single float-plus token rather than `+` and `.`.
  * **Literals**: `FLOAT_LIT` is declared before `INT_LIT` (line 42) so that a sequence like `3.14` is processed as a float rather than being split into `3`, `.`, and `14`.

### Q3: How is operator precedence defined in the Parser without relying on global precedence tables?
* **Answer**: Precedence is handled **syntactically (by design of the grammar)** in `src/parser.py`.
  * We layer the grammar rules so that `atom` matches base elements (highest precedence), `term` matches multiplicative operators (middle precedence), and `expr` matches additive operators (lowest precedence).
  * Because a `term` must be evaluated and reduced before it can be added or subtracted in an `expr`, multiplication and division naturally hold higher precedence over addition and subtraction.

### Q4: How does your TAC Interpreter handle function calls and parameter bindings?
* **Answer**: 
  * **During TAC generation** (`src/tac.py`): Arguments are evaluated sequentially and emitted as `Param` instructions, followed by a `Call` instruction detailing the number of arguments (`nargs`).
  * **During evaluation** (`src/interpreter.py`):
    1. `Param` instructions resolve arguments and append them to a temporary `pending_params` list.
    2. When `Call` is executed, it pops the last `nargs` elements from `pending_params`.
    3. It creates an isolated environment frame mapping the function's formal parameter names to these popped values.
    4. It executes the function starting from its entry address in `func_map`, returning when a `Return` instruction is reached.

### Q5: What is the difference between an Abstract Syntax Tree (AST) and Three-Address Code (TAC)?
* **Answer**: 
  * The **AST** is a high-level, recursive tree structure. It contains nested structures like loops and expressions directly, prioritizing syntax preservation and high-level semantics (used for type checking).
  * **TAC** is a low-level, flat Intermediate Representation (IR). It breaks down all nested expressions into sequential register-like instructions (`t0 = a + b`) and flattens control loops into memory labels and direct jumps (`goto L1`). It is one step above raw Assembly.

### Q6: Did you deal with any Shift-Reduce conflicts? How does your parser handle ambiguous chains?
* **Answer**: 
  * We handled ambiguity primarily through grammar layering (which gives implicit precedence). 
  * However, for boolean operators where `a = b = c` is syntactically ambiguous, we used explicitly defined precedence rules: `precedence = (('nonassoc', '=', NE),)`. Setting them to **nonassoc** causes the parser to strictly ban chaining without explicitly needing deeper grammar nesting.

### Q7: How does your language support recursive function calls?
* **Answer**: 
  * Support is natively derived through dynamic stack frames in `src/interpreter.py`. 
  * Every time a function is called (even recursively), the `_call_func` method initiates a completely distinct Python dictionary frame mapping that function's locals.
  * Because each call context is physically separate in host memory, values don't corrupt, and Python's host call-stack manages the unwinding sequence perfectly.
