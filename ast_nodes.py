"""
ast_nodes.py - Abstract syntax tree node definitions.

Every grammar production builds one of these. We keep them as simple dataclasses
with a `kind` field so debugging output is readable. The type-checker (next phase)
will walk these trees and annotate each node with a `.type` attribute.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Union


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass
class IntLit:
    value: int

@dataclass
class FloatLit:
    value: float

@dataclass
class StringLit:
    value: str

@dataclass
class BoolLit:
    value: bool

@dataclass
class Var:
    name: str

@dataclass
class BinOp:
    op: str          # one of: '+', '-', '+.', '-.', '*', '/', '*.', '/.', '^'
    left: object
    right: object

@dataclass
class Compare:
    op: str          # '=' or '<>'
    left: object
    right: object

@dataclass
class Call:
    name: str
    args: List[object]


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class Assign:
    name: str
    expr: object

@dataclass
class If:
    cond: object
    then_block: List[object]
    else_block: List[object]

@dataclass
class While:
    cond: object
    body: List[object]

@dataclass
class Print:
    expr: object

@dataclass
class Return:
    expr: object


# ---------------------------------------------------------------------------
# Top-level: function definition and program
# ---------------------------------------------------------------------------

@dataclass
class Param:
    type: str        # 'int' | 'float' | 'bool' | 'string'
    name: str

@dataclass
class FuncDef:
    return_type: str
    name: str
    params: List[Param]
    body: List[object]

@dataclass
class Program:
    funcs: List[FuncDef]
    main: List[object]
