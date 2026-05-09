"""
interpreter.py - Three-Address Code (TAC) Interpreter.

This file executes the flat list of TAC instructions produced by tac.py.

HOW THE INTERPRETER EXECUTES CODE:
1. **Pre-scan**: Loops through instructions once to build:
   - `label_map`: Maps label names to instruction indices (addresses).
   - `func_map`: Maps function names to the first instruction address inside the function body.
2. **Main entry point**: Finds where the main body starts (after the last function declaration)
   and begins executing from there.
3. **Execution Model**:
   - Uses a Program Counter (`pc`) to track the current instruction index.
   - Jumps are executed by simply updating `pc = label_map[target]`.
   - Variables and temporaries live inside environment dictionaries (`env`).
   - Function calls create a fresh dictionary frame starting with bound arguments, inheriting nothing
     from the caller (enforcing pure value-passing).
"""

from .tac import (
    Label, Assign, BinOp, Jump, JumpIf, JumpIfNot,
    Param, Call, Return, Print, FuncBegin, FuncEnd, Lit,
)


class RuntimeError_(Exception):
    """Exception thrown when a dynamic error occurs during program execution."""
    pass


class Interpreter:
    def __init__(self, instructions: list):
        self.instructions = instructions
        
        # O(1) Address Lookup Maps
        self.label_map: dict[str, int] = {}     # label name -> instruction index
        self.func_map:  dict[str, int] = {}     # function name -> instruction index of first statement after FuncBegin
        
        self._build_maps()

    # ------------------------------------------------------------------
    # Pre-scan: Build jump label and function entry offset tables
    # ------------------------------------------------------------------

    def _build_maps(self):
        """Pre-scans the instruction stream to save label and function address offsets."""
        for i, instr in enumerate(self.instructions):
            if isinstance(instr, Label):
                self.label_map[instr.name] = i
            elif isinstance(instr, FuncBegin):
                # The first executable instruction in a function is the one immediately following FuncBegin
                self.func_map[instr.name] = i + 1

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    def run(self):
        """Starts program execution at the main top-level statements block."""
        # Find where main body starts: right after the last function definition block.
        main_start = 0
        for i, instr in enumerate(self.instructions):
            if isinstance(instr, FuncEnd):
                main_start = i + 1

        # Global variables environment (maps variable name -> value)
        global_env: dict = {}
        
        # Execute the main body starting from main_start address
        self._exec(main_start, global_env, pending_params=[])

    # ------------------------------------------------------------------
    # Core Executor Loop
    # ------------------------------------------------------------------

    def _exec(self, start_pc: int, env: dict, pending_params: list):
        """
        Executes instructions starting at start_pc.
        Continues until:
        - A Return instruction is executed (returns evaluated value).
        - We reach the end of the instruction stream.
        """
        pc = start_pc

        while pc < len(self.instructions):
            instr = self.instructions[pc]

            # --- Skip function body blocks when running main (and vice versa) ---
            if isinstance(instr, FuncBegin):
                # Fast-forward past the entire function body to matching FuncEnd
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
                # If a function execution naturally reaches FuncEnd without returning, return None
                return None

            # -----------------------------------------------------------
            # Instruction Dispatch Logic
            # -----------------------------------------------------------

            if isinstance(instr, Label):
                # Labels are just target markers: skip to next instruction
                pc += 1

            elif isinstance(instr, Assign):
                # Resolve the source operand and store it in env[dest]
                env[instr.dest] = self._resolve(instr.src, env)
                pc += 1

            elif isinstance(instr, BinOp):
                # Resolve left and right values, evaluate operation, store in env[dest]
                l = self._resolve(instr.left, env)
                r = self._resolve(instr.right, env)
                env[instr.dest] = self._apply_op(instr.op, l, r)
                pc += 1

            elif isinstance(instr, Jump):
                # Jump target: update program counter directly to label address
                pc = self.label_map[instr.label]

            elif isinstance(instr, JumpIf):
                cond = self._resolve(instr.cond, env)
                # Jump if cond evaluates to True, otherwise go to next instruction (pc + 1)
                pc = self.label_map[instr.label] if cond else pc + 1

            elif isinstance(instr, JumpIfNot):
                cond = self._resolve(instr.cond, env)
                # Jump if cond evaluates to False, otherwise go to next instruction (pc + 1)
                pc = self.label_map[instr.label] if not cond else pc + 1

            elif isinstance(instr, Param):
                # Push evaluated argument onto our list of pending parameters before a Call
                pending_params.append(self._resolve(instr.arg, env))
                pc += 1

            elif isinstance(instr, Call):
                # Pop nargs arguments from our pending parameters list
                if instr.nargs > 0:
                    args = pending_params[-instr.nargs:]
                    del pending_params[-instr.nargs:]
                else:
                    args = []
                # Execute the function with popped arguments and store returned value in env[dest]
                result = self._call_func(instr.func, args)
                env[instr.dest] = result
                pc += 1

            elif isinstance(instr, Return):
                # Return immediately, evaluating the return value
                return self._resolve(instr.val, env)

            elif isinstance(instr, Print):
                val = self._resolve(instr.val, env)
                print(val)
                pc += 1

            else:
                raise RuntimeError_(f"Unknown instruction: {instr}")

        return None

    # ------------------------------------------------------------------
    # Function Execution Dispatch
    # ------------------------------------------------------------------

    def _call_func(self, name: str, args: list):
        """Binds argument values to parameters, pushes a new stack frame, and executes function."""
        if name not in self.func_map:
            raise RuntimeError_(f"Undefined function '{name}'.")
            
        # Retrieve original formal parameter names for this function
        param_names = self._param_names.get(name, [])
        if len(args) != len(param_names):
            raise RuntimeError_(
                f"Function '{name}' expects {len(param_names)} arg(s), "
                f"got {len(args)}."
            )
            
        # Create a brand new isolated stack frame environment (dictionary).
        # This maps param names directly to passed argument values.
        frame: dict = dict(zip(param_names, args))
        
        # Execute function starting at its first instruction PC address
        return self._exec(self.func_map[name], frame, pending_params=[])

    # ------------------------------------------------------------------
    # Resolution Helpers
    # ------------------------------------------------------------------

    def _resolve(self, src, env: dict):
        """Resolves operand: returns concrete value if Lit(val), else retrieves it from env."""
        if isinstance(src, Lit):
            return src.value
        if isinstance(src, str):
            if src not in env:
                raise RuntimeError_(f"Undefined variable/temp '{src}'.")
            return env[src]
        return src

    @staticmethod
    def _apply_op(op: str, l, r):
        """Core operation evaluation dispatcher with dynamic safety checks."""
        if op == '+':   return l + r
        if op == '-':   return l - r
        if op == '*':   return l * r
        if op == '/':
            if r == 0:
                raise RuntimeError_("Division by zero.")
            return l // r          # Integer division (yields int)
        if op == '+.':  return l + r
        if op == '-.':  return l - r
        if op == '*.':  return l * r
        if op == '/.':
            if r == 0.0:
                raise RuntimeError_("Division by zero.")
            return l / r           # Float division (yields float)
        if op == '^':   return str(l) + str(r)
        if op == '=':   return l == r
        if op == '<>':  return l != r
        raise RuntimeError_(f"Unknown operator '{op}'.")

    # ------------------------------------------------------------------
    # Param-name side-table (Populated on construction)
    # ------------------------------------------------------------------
    # Maps function name -> list of formal parameter names.
    _param_names: dict[str, list[str]] = {}


def make_interpreter(instructions: list, program) -> Interpreter:
    """
    Convenience builder: constructs an interpreter and attaches parameter names
    extracted from the AST so arguments can be bound correctly.
    """
    interp = Interpreter(instructions)
    interp._param_names = {
        f.name: [p.name for p in f.params]
        for f in program.funcs
    }
    return interp

