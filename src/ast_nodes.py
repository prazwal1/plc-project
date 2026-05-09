"""
ast_nodes.py - Abstract Syntax Tree (AST) node definitions.

Every successful rule match in the parser builds one of these dataclasses.
The AST serves as the clean, tree-structured intermediate representation of the code,
which is walked by the TypeChecker and the TAC Generator.
"""

from dataclasses import dataclass
from typing import List


# ---------------------------------------------------------------------------
# Expression Nodes (Nodes that evaluate to a value)
# ---------------------------------------------------------------------------

@dataclass
class IntLit:
    """Represents a literal integer (e.g., 42)"""
    value: int

@dataclass
class FloatLit:
    """Represents a literal float (e.g., 3.14)"""
    value: float

@dataclass
class StringLit:
    """Represents a literal string (e.g., "hello")"""
    value: str

@dataclass
class BoolLit:
    """Represents a literal boolean (e.g., true or false)"""
    value: bool

@dataclass
class Var:
    """Represents a variable use (e.g., x)"""
    name: str

@dataclass
class BinOp:
    """Represents binary operations (e.g., x + y, x *. y, s1 ^ s2)"""
    op: str          # operator symbol: '+', '-', '+.', '-.', '*', '/', '*.', '/.', '^'
    left: object     # Left sub-expression
    right: object    # Right sub-expression

@dataclass
class Compare:
    """Represents equality/inequality comparisons (e.g., a = b, c <> d)"""
    op: str          # operator symbol: '=' or '<>'
    left: object     # Left sub-expression
    right: object    # Right sub-expression

@dataclass
class Call:
    """Represents a function call (e.g., factorial(n - 1))"""
    name: str        # Function name
    args: List[object] # Arguments passed (list of expression nodes)


# ---------------------------------------------------------------------------
# Statement Nodes (Nodes that execute actions but do not return values)
# ---------------------------------------------------------------------------

@dataclass
class Assign:
    """Represents variable assignment (e.g., x = 5)"""
    name: str        # Left-hand side variable name
    expr: object     # Right-hand side expression node

@dataclass
class If:
    """Represents if-then-else conditions"""
    cond: object              # Condition expression (must check to boolean)
    then_block: List[object]  # Statement list for 'then' branch
    else_block: List[object]  # Statement list for 'else' branch

@dataclass
class While:
    """Represents a while loop"""
    cond: object              # Condition expression (must check to boolean)
    body: List[object]        # Statement list inside loop body

@dataclass
class Print:
    """Represents print statement (e.g., print(x))"""
    expr: object

@dataclass
class Return:
    """Represents return statement inside functions (e.g., return y)"""
    expr: object


# ---------------------------------------------------------------------------
# Top-level Declarations: functions and programs
# ---------------------------------------------------------------------------

@dataclass
class Param:
    """Represents a formal function parameter (e.g., int n)"""
    type: str        # 'int' | 'float' | 'bool' | 'string'
    name: str        # parameter name

@dataclass
class FuncDef:
    """Represents a function definition"""
    return_type: str       # return type ('int' | 'float' | 'bool' | 'string')
    name: str              # function name
    params: List[Param]    # formal parameters list
    body: List[object]     # function body statements list

@dataclass
class Program:
    """Root node representing the entire source code file"""
    funcs: List[FuncDef]   # All defined functions
    main: List[object]     # All main body (top-level) statements
