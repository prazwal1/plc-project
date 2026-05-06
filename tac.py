"""
tac.py - Three-Address Code (TAC) generation.

Each TAC instruction is a named tuple. The full list of instruction kinds:

  Label(name)                   -- label:
  Assign(dest, src)             -- dest = src          (copy / load literal)
  BinOp(dest, op, left, right)  -- dest = left op right
  Jump(label)                   -- goto label
  JumpIf(cond, label)           -- if cond goto label
  JumpIfNot(cond, label)        -- if !cond goto label
  Param(arg)                    -- push argument
  Call(dest, func, nargs)       -- dest = call func  (nargs args were pushed)
  Return(val)                   -- return val
  Print(val)                    -- print val
  FuncBegin(name)               -- function prologue marker
  FuncEnd(name)                 -- function epilogue marker

Temporaries are named t0, t1, ... (global counter across the whole program so
labels and temps are globally unique -- easy to read in debug output).
"""

from dataclasses import dataclass
from typing import Any
import ast_nodes as A


# ------------------------------------------------------------------
# Instruction dataclasses
# ------------------------------------------------------------------

@dataclass
class Lit:      value: Any   # wraps a literal so it's never mistaken for a var name

@dataclass
class Label:    name: str
@dataclass
class Assign:   dest: str; src: Any          # src is Lit(value) or a temp/var name (str)
@dataclass
class BinOp:    dest: str; op: str; left: Any; right: Any
@dataclass
class Jump:     label: str
@dataclass
class JumpIf:   cond: Any; label: str
@dataclass
class JumpIfNot: cond: Any; label: str
@dataclass
class Param:    arg: Any
@dataclass
class Call:     dest: str; func: str; nargs: int
@dataclass
class Return:   val: Any
@dataclass
class Print:    val: Any
@dataclass
class FuncBegin: name: str
@dataclass
class FuncEnd:   name: str


# ------------------------------------------------------------------
# Generator
# ------------------------------------------------------------------

class TACGenerator:
    def __init__(self):
        self._temp_count = 0
        self._label_count = 0
        self.code: list = []           # flat list of instructions (all functions + main)

    # ------ helpers --------------------------------------------------

    def _new_temp(self) -> str:
        t = f't{self._temp_count}'
        self._temp_count += 1
        return t

    def _new_label(self) -> str:
        l = f'L{self._label_count}'
        self._label_count += 1
        return l

    def _emit(self, instr):
        self.code.append(instr)

    # ------ public entry point ---------------------------------------

    def generate(self, program: A.Program) -> list:
        for f in program.funcs:
            self._gen_func(f)
        for stmt in program.main:
            self._gen_stmt(stmt)
        return self.code

    # ------ functions ------------------------------------------------

    def _gen_func(self, f: A.FuncDef):
        self._emit(FuncBegin(f.name))
        # Parameters are named directly -- the caller pushes Param instructions
        # and the interpreter binds them to the declared param names.
        for stmt in f.body:
            self._gen_stmt(stmt)
        self._emit(FuncEnd(f.name))

    # ------ statements -----------------------------------------------

    def _gen_stmt(self, stmt):
        if isinstance(stmt, A.Assign):
            src = self._gen_expr(stmt.expr)
            self._emit(Assign(stmt.name, src))

        elif isinstance(stmt, A.If):
            cond = self._gen_expr(stmt.cond)
            else_label = self._new_label()
            end_label  = self._new_label()
            self._emit(JumpIfNot(cond, else_label))
            for s in stmt.then_block:
                self._gen_stmt(s)
            self._emit(Jump(end_label))
            self._emit(Label(else_label))
            for s in stmt.else_block:
                self._gen_stmt(s)
            self._emit(Label(end_label))

        elif isinstance(stmt, A.While):
            test_label = self._new_label()
            end_label  = self._new_label()
            self._emit(Label(test_label))
            cond = self._gen_expr(stmt.cond)
            self._emit(JumpIfNot(cond, end_label))
            for s in stmt.body:
                self._gen_stmt(s)
            self._emit(Jump(test_label))
            self._emit(Label(end_label))

        elif isinstance(stmt, A.Print):
            val = self._gen_expr(stmt.expr)
            self._emit(Print(val))

        elif isinstance(stmt, A.Return):
            val = self._gen_expr(stmt.expr)
            self._emit(Return(val))

        else:
            raise ValueError(f"Unknown statement: {type(stmt)}")

    # ------ expressions  (returns the name of the temp/var holding the result)

    def _gen_expr(self, node) -> str:
        if isinstance(node, (A.IntLit, A.FloatLit, A.StringLit, A.BoolLit)):
            t = self._new_temp()
            self._emit(Assign(t, Lit(node.value)))
            return t

        if isinstance(node, A.Var):
            return node.name        # variables live in the env by name

        if isinstance(node, A.BinOp):
            l = self._gen_expr(node.left)
            r = self._gen_expr(node.right)
            t = self._new_temp()
            self._emit(BinOp(t, node.op, l, r))
            return t

        if isinstance(node, A.Compare):
            l = self._gen_expr(node.left)
            r = self._gen_expr(node.right)
            t = self._new_temp()
            self._emit(BinOp(t, node.op, l, r))
            return t

        if isinstance(node, A.Call):
            for arg in node.args:
                a = self._gen_expr(arg)
                self._emit(Param(a))
            t = self._new_temp()
            self._emit(Call(t, node.name, len(node.args)))
            return t

        raise ValueError(f"Unknown expression node: {type(node)}")


# ------------------------------------------------------------------
# Pretty-print TAC for the report / debug output
# ------------------------------------------------------------------

def pretty_tac(instructions: list) -> str:
    lines = []
    for instr in instructions:
        if isinstance(instr, Label):
            lines.append(f'{instr.name}:')
        elif isinstance(instr, FuncBegin):
            lines.append(f'\n--- function {instr.name} ---')
        elif isinstance(instr, FuncEnd):
            lines.append(f'--- end {instr.name} ---\n')
        elif isinstance(instr, Assign):
            if isinstance(instr.src, Lit):
                lines.append(f'    {instr.dest} = {instr.src.value!r}')
            else:
                lines.append(f'    {instr.dest} = {instr.src}')
        elif isinstance(instr, BinOp):
            lines.append(f'    {instr.dest} = {instr.left} {instr.op} {instr.right}')
        elif isinstance(instr, Jump):
            lines.append(f'    goto {instr.label}')
        elif isinstance(instr, JumpIf):
            lines.append(f'    if {instr.cond} goto {instr.label}')
        elif isinstance(instr, JumpIfNot):
            lines.append(f'    ifnot {instr.cond} goto {instr.label}')
        elif isinstance(instr, Param):
            lines.append(f'    param {instr.arg}')
        elif isinstance(instr, Call):
            lines.append(f'    {instr.dest} = call {instr.func} [{instr.nargs}]')
        elif isinstance(instr, Return):
            lines.append(f'    return {instr.val}')
        elif isinstance(instr, Print):
            lines.append(f'    print {instr.val}')
        else:
            lines.append(f'    {instr}')
    return '\n'.join(lines)
