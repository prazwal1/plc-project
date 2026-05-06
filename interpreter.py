"""
interpreter.py - TAC interpreter.

Executes the flat list of TAC instructions produced by tac.py.

Execution model
---------------
* There is one global environment (dict) for top-level variables.
* Each function call pushes a new stack frame (dict) that starts with the
  parameter bindings and inherits nothing from the caller -- pure value passing.
* A pending_params list accumulates Param instructions before each Call.
* FuncBegin / FuncEnd are used to build a function table at startup.
* Control flow is implemented by keeping a program counter (pc) and jumping
  to label indices stored in a pre-built label_map.

Operators
---------
  +  -  *  /     : int arithmetic
  +. -. *. /.    : float arithmetic
  ^              : string concatenation
  =              : equality  -> bool
  <>             : inequality -> bool
"""

from tac import (
    Label, Assign, BinOp, Jump, JumpIf, JumpIfNot,
    Param, Call, Return, Print, FuncBegin, FuncEnd, Lit,
)


class RuntimeError_(Exception):
    pass


class Interpreter:
    def __init__(self, instructions: list):
        self.instructions = instructions
        self.label_map: dict[str, int] = {}     # label name -> pc
        self.func_map:  dict[str, int] = {}     # func name  -> pc of first instr after FuncBegin
        self._build_maps()

    # ------------------------------------------------------------------
    # Pre-scan: build label and function address tables
    # ------------------------------------------------------------------

    def _build_maps(self):
        for i, instr in enumerate(self.instructions):
            if isinstance(instr, Label):
                self.label_map[instr.name] = i
            elif isinstance(instr, FuncBegin):
                # The first real instruction is the one after FuncBegin.
                self.func_map[instr.name] = i + 1

    # ------------------------------------------------------------------
    # Run the main body (everything that is NOT inside a function def)
    # ------------------------------------------------------------------

    def run(self):
        # Find where the main body starts: after the last FuncEnd (or 0).
        main_start = 0
        for i, instr in enumerate(self.instructions):
            if isinstance(instr, FuncEnd):
                main_start = i + 1

        global_env: dict = {}
        self._exec(main_start, global_env, pending_params=[])

    # ------------------------------------------------------------------
    # Executor
    # ------------------------------------------------------------------

    def _exec(self, start_pc: int, env: dict, pending_params: list):
        """
        Execute instructions beginning at start_pc.
        Returns when a Return instruction is executed (returns its value)
        or when we fall off the end of the instruction list.
        """
        pc = start_pc

        while pc < len(self.instructions):
            instr = self.instructions[pc]

            # Skip function bodies when running the main body (and vice versa).
            if isinstance(instr, FuncBegin):
                # Fast-forward to matching FuncEnd.
                depth = 1
                pc += 1
                while pc < len(self.instructions) and depth > 0:
                    if isinstance(self.instructions[pc], FuncBegin):
                        depth += 1
                    elif isinstance(self.instructions[pc], FuncEnd):
                        depth -= 1
                    pc += 1
                continue

            if isinstance(instr, FuncEnd):
                # Reached end of a function without a return -- return None.
                return None

            # ----- actual instruction dispatch -------------------------

            if isinstance(instr, Label):
                pc += 1

            elif isinstance(instr, Assign):
                env[instr.dest] = self._resolve(instr.src, env)
                pc += 1

            elif isinstance(instr, BinOp):
                l = self._resolve(instr.left, env)
                r = self._resolve(instr.right, env)
                env[instr.dest] = self._apply_op(instr.op, l, r)
                pc += 1

            elif isinstance(instr, Jump):
                pc = self.label_map[instr.label]

            elif isinstance(instr, JumpIf):
                cond = self._resolve(instr.cond, env)
                pc = self.label_map[instr.label] if cond else pc + 1

            elif isinstance(instr, JumpIfNot):
                cond = self._resolve(instr.cond, env)
                pc = self.label_map[instr.label] if not cond else pc + 1

            elif isinstance(instr, Param):
                pending_params.append(self._resolve(instr.arg, env))
                pc += 1

            elif isinstance(instr, Call):
                if instr.nargs > 0:
                    args = pending_params[-instr.nargs:]
                    del pending_params[-instr.nargs:]
                else:
                    args = []
                result = self._call_func(instr.func, args)
                env[instr.dest] = result
                pc += 1

            elif isinstance(instr, Return):
                return self._resolve(instr.val, env)

            elif isinstance(instr, Print):
                val = self._resolve(instr.val, env)
                print(val)
                pc += 1

            else:
                raise RuntimeError_(f"Unknown instruction: {instr}")

        return None

    # ------------------------------------------------------------------
    # Function call dispatch
    # ------------------------------------------------------------------

    def _call_func(self, name: str, args: list):
        if name not in self.func_map:
            raise RuntimeError_(f"Undefined function '{name}'.")
        # Build the new frame: we need the parameter names.
        # Recover them from the FuncBegin position in the instruction list.
        func_start_pc = self.func_map[name] - 1   # points at FuncBegin
        # Walk forward to collect the Param-load pattern the generator emits.
        # Actually, the generator does NOT emit param-load instructions -- it
        # relies on the caller naming them. We need the FuncDef's param list.
        # We stored them in a side table during generate(); retrieve from there.
        param_names = self._param_names.get(name, [])
        if len(args) != len(param_names):
            raise RuntimeError_(
                f"Function '{name}' expects {len(param_names)} arg(s), "
                f"got {len(args)}."
            )
        frame: dict = dict(zip(param_names, args))
        return self._exec(self.func_map[name], frame, pending_params=[])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _resolve(self, src, env: dict):
        """A TAC operand is either a Lit(value) for literals, or a str name
        (temp or variable) looked up in env."""
        if isinstance(src, Lit):
            return src.value
        if isinstance(src, str):
            if src not in env:
                raise RuntimeError_(f"Undefined variable '{src}'.")
            return env[src]
        return src   # should not normally reach here

    @staticmethod
    def _apply_op(op: str, l, r):
        if op == '+':   return l + r
        if op == '-':   return l - r
        if op == '*':   return l * r
        if op == '/':
            if r == 0:
                raise RuntimeError_("Division by zero.")
            return l // r          # integer division
        if op == '+.':  return l + r
        if op == '-.':  return l - r
        if op == '*.':  return l * r
        if op == '/.':
            if r == 0.0:
                raise RuntimeError_("Division by zero.")
            return l / r
        if op == '^':   return str(l) + str(r)
        if op == '=':   return l == r
        if op == '<>':  return l != r
        raise RuntimeError_(f"Unknown operator '{op}'.")

    # ------------------------------------------------------------------
    # Param-name table (populated by the runner after TACGenerator runs)
    # ------------------------------------------------------------------
    _param_names: dict[str, list[str]] = {}


def make_interpreter(instructions: list, program) -> Interpreter:
    """
    Convenience: build interpreter and attach param-name table derived
    from the original AST so function calls can bind args to names.
    """
    interp = Interpreter(instructions)
    interp._param_names = {
        f.name: [p.name for p in f.params]
        for f in program.funcs
    }
    return interp
