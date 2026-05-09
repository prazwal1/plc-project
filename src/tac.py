"""
tac.py - Three-Address Code (TAC) generation.

TAC is an intermediate representation (IR) where every instruction has at most
three addresses (usually: destination = operand1 operator operand2). It flattens
the nested, tree-structured AST into a flat list of simple sequential instructions
resembling assembly, but with infinite virtual registers (called temporaries: t0, t1, ...).

PREPARE FOR THE TEST:
- Loops and If statements are flattened using Jump and conditional Jumps (JumpIf / JumpIfNot).
- Expression generation recursively flattens trees and returns the temporary variable holding the result.
"""

from dataclasses import dataclass
from typing import Any
from . import ast_nodes as A


# ------------------------------------------------------------------
# Flat Instruction Classes (Addresses/Registers are strings)
# ------------------------------------------------------------------

@dataclass
class Lit:
    """Wraps literal values (e.g., Lit(5)) to distinguish them from variable names in TAC."""
    value: Any

@dataclass
class Label:
    """Represents a code label for jump targets (e.g., L0:, L1:)"""
    name: str

@dataclass
class Assign:
    """Represents a copy instruction (e.g., dest = src)"""
    dest: str
    src: Any          # Either a Lit(value) or a temporary/variable name (str)

@dataclass
class BinOp:
    """Represents three-address binary operations (e.g., dest = left op right)"""
    dest: str
    op: str
    left: Any
    right: Any

@dataclass
class Jump:
    """Unconditional jump (e.g., goto label)"""
    label: str

@dataclass
class JumpIf:
    """Conditional jump if condition is true (e.g., if cond goto label)"""
    cond: Any
    label: str

@dataclass
class JumpIfNot:
    """Conditional jump if condition is false (e.g., ifnot cond goto label)"""
    cond: Any
    label: str

@dataclass
class Param:
    """Pushes a parameter onto the call stack before a function call."""
    arg: Any

@dataclass
class Call:
    """Executes a function call with nargs arguments (e.g., dest = call func [nargs])"""
    dest: str
    func: str
    nargs: int

@dataclass
class Return:
    """Return statement from a function (e.g., return val)"""
    val: Any

@dataclass
class Print:
    """Executes a print command on a value (e.g., print val)"""
    val: Any

@dataclass
class FuncBegin:
    """Marker showing the entry point (prologue) of a function definition block."""
    name: str

@dataclass
class FuncEnd:
    """Marker showing the exit point (epilogue) of a function definition block."""
    name: str


# ------------------------------------------------------------------
# TAC Code Generator
# ------------------------------------------------------------------

class TACGenerator:
    def __init__(self):
        # Monotonically increasing counters to ensure globally unique temporary and label names
        self._temp_count = 0
        self._label_count = 0
        self.code: list = []           # Output list of flat instructions

    # ------ Helpers --------------------------------------------------

    def _new_temp(self) -> str:
        """Creates a brand new virtual register name (e.g., 't0', 't1')."""
        t = f't{self._temp_count}'
        self._temp_count += 1
        return t

    def _new_label(self) -> str:
        """Creates a brand new code jump target label (e.g., 'L0', 'L1')."""
        l = f'L{self._label_count}'
        self._label_count += 1
        return l

    def _emit(self, instr):
        """Appends a generated instruction to the final flat instructions list."""
        self.code.append(instr)

    # ------ Public entry point ---------------------------------------

    def generate(self, program: A.Program) -> list:
        """Processes functions and main body statements, returning a single flat list of instructions."""
        for f in program.funcs:
            self._gen_func(f)
        for stmt in program.main:
            self._gen_stmt(stmt)
        return self.code

    # ------ Functions ------------------------------------------------

    def _gen_func(self, f: A.FuncDef):
        """Generates instructions for a function, sandwiched between prologue and epilogue markers."""
        self._emit(FuncBegin(f.name))
        # Parameter bindings are resolved automatically by the interpreter at call time
        for stmt in f.body:
            self._gen_stmt(stmt)
        self._emit(FuncEnd(f.name))

    # ------ Statements flattening ------------------------------------

    def _gen_stmt(self, stmt):
        """Processes statements and emits corresponding jump-based control flow or copies."""
        
        # --- Assignment (x = expr) ---
        if isinstance(stmt, A.Assign):
            src = self._gen_expr(stmt.expr)
            self._emit(Assign(stmt.name, src))

        # --- If Statement ---
        elif isinstance(stmt, A.If):
            cond = self._gen_expr(stmt.cond)
            else_label = self._new_label()
            end_label  = self._new_label()
            
            # 1. If cond is false, jump over the 'then' block to the 'else' block
            self._emit(JumpIfNot(cond, else_label))
            
            # 2. Process 'then' block
            for s in stmt.then_block:
                self._gen_stmt(s)
            # 3. Unconditionally jump over the 'else' block
            self._emit(Jump(end_label))
            
            # 4. Process 'else' block
            self._emit(Label(else_label))
            for s in stmt.else_block:
                self._gen_stmt(s)
                
            # 5. Loop exit target
            self._emit(Label(end_label))

        # --- While Statement ---
        elif isinstance(stmt, A.While):
            test_label = self._new_label()
            end_label  = self._new_label()
            
            # 1. Emplace the loop condition test entry label
            self._emit(Label(test_label))
            cond = self._gen_expr(stmt.cond)
            
            # 2. If loop test condition evaluates to false, jump out of loop
            self._emit(JumpIfNot(cond, end_label))
            
            # 3. Process loop body statements
            for s in stmt.body:
                self._gen_stmt(s)
                
            # 4. Jump back to perform the condition test again
            self._emit(Jump(test_label))
            
            # 5. Emplace the loop exit target label
            self._emit(Label(end_label))

        # --- Print Statement ---
        elif isinstance(stmt, A.Print):
            val = self._gen_expr(stmt.expr)
            self._emit(Print(val))

        # --- Return Statement ---
        elif isinstance(stmt, A.Return):
            val = self._gen_expr(stmt.expr)
            self._emit(Return(val))

        else:
            raise ValueError(f"Unknown statement: {type(stmt)}")

    # ------ Expressions (Returns the string name of the temporary/variable holding the value) ---

    def _gen_expr(self, node) -> str:
        """Recursively flattens expression AST nodes into flat sequential temporary assignments."""
        
        # --- Literals ---
        if isinstance(node, (A.IntLit, A.FloatLit, A.StringLit, A.BoolLit)):
            t = self._new_temp()
            self._emit(Assign(t, Lit(node.value)))
            return t

        # --- Variable reference ---
        if isinstance(node, A.Var):
            return node.name        # Return name directly (it already lives in environment)

        # --- Binary Operations (Arithmetic) ---
        if isinstance(node, A.BinOp):
            l = self._gen_expr(node.left)
            r = self._gen_expr(node.right)
            t = self._new_temp()
            self._emit(BinOp(t, node.op, l, r))
            return t

        # --- Comparison Operations ---
        if isinstance(node, A.Compare):
            l = self._gen_expr(node.left)
            r = self._gen_expr(node.right)
            t = self._new_temp()
            self._emit(BinOp(t, node.op, l, r))  # Under the hood, comparisons are flattened into BinOp instructions
            return t

        # --- Function Calls ---
        if isinstance(node, A.Call):
            # 1. Evaluate arguments from left to right and emit Param instructions
            for arg in node.args:
                a = self._gen_expr(arg)
                self._emit(Param(a))
            # 2. Emit the Call instruction
            t = self._new_temp()
            self._emit(Call(t, node.name, len(node.args)))
            return t

        raise ValueError(f"Unknown expression node: {type(node)}")


# ------------------------------------------------------------------
# Pretty-print helper for debugging & reporting
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
