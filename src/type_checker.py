"""
type_checker.py - Static type checker with type inference.

Since the language has no explicit variable declarations, the type of each
variable is inferred from its first assignment (Hindley-Milner flavour but
monomorphic). Once inferred the type is fixed -- this is static typing.

Type rules
----------
  int literal        -> int
  float literal      -> float
  string literal     -> string
  true / false       -> bool
  +  -  *  /         : int  × int   -> int
  +. -. *. /.        : float × float -> float
  ^                  : string × string -> string
  =  <>              : τ × τ -> bool   (τ must be int or float, same on both sides)
  if/while cond      : must be bool
  function call      : args must match declared param types; result = return type

The checker annotates every expression node with a `.type` attribute so the
TAC generator can emit correct code without re-deriving types.
"""

from . import ast_nodes as A


class TypeErrorException(Exception):
    pass


class TypeChecker:
    def __init__(self):
        # func_env: name -> (return_type, [param_type, ...])
        self.func_env: dict[str, tuple[str, list[str]]] = {}
        # var_env stack: list of dicts mapping name -> type
        self.var_env: list[dict[str, str]] = [{}]

    # ------------------------------------------------------------------
    # Environment helpers
    # ------------------------------------------------------------------

    def _lookup(self, name: str) -> str | None:
        for scope in reversed(self.var_env):
            if name in scope:
                return scope[name]
        return None

    def _define(self, name: str, typ: str):
        self.var_env[-1][name] = typ

    def _push(self):
        self.var_env.append({})

    def _pop(self):
        self.var_env.pop()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def check(self, program: A.Program):
        # First pass: register all function signatures so mutually recursive
        # calls are allowed.
        for f in program.funcs:
            param_types = [p.type for p in f.params]
            self.func_env[f.name] = (f.return_type, param_types)

        # Second pass: check each function body.
        for f in program.funcs:
            self._check_func(f)

        # Check top-level statements.
        for stmt in program.main:
            self._check_stmt(stmt)

    # ------------------------------------------------------------------
    # Functions
    # ------------------------------------------------------------------

    def _check_func(self, f: A.FuncDef):
        self._push()
        for p in f.params:
            self._define(p.name, p.type)
        for stmt in f.body:
            self._check_stmt(stmt, expected_return=f.return_type)
        self._pop()

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _check_stmt(self, stmt, expected_return: str | None = None):
        if isinstance(stmt, A.Assign):
            t = self._check_expr(stmt.expr)
            existing = self._lookup(stmt.name)
            if existing is None:
                self._define(stmt.name, t)
            elif existing != t:
                raise TypeErrorException(
                    f"Type error: variable '{stmt.name}' already has type "
                    f"'{existing}' but is assigned a '{t}' value."
                )

        elif isinstance(stmt, A.If):
            ct = self._check_expr(stmt.cond)
            if ct != 'bool':
                raise TypeErrorException(
                    f"Type error: if-condition must be bool, got '{ct}'."
                )
            for s in stmt.then_block:
                self._check_stmt(s, expected_return)
            for s in stmt.else_block:
                self._check_stmt(s, expected_return)

        elif isinstance(stmt, A.While):
            ct = self._check_expr(stmt.cond)
            if ct != 'bool':
                raise TypeErrorException(
                    f"Type error: while-condition must be bool, got '{ct}'."
                )
            for s in stmt.body:
                self._check_stmt(s, expected_return)

        elif isinstance(stmt, A.Print):
            self._check_expr(stmt.expr)

        elif isinstance(stmt, A.Return):
            t = self._check_expr(stmt.expr)
            if expected_return is not None and t != expected_return:
                raise TypeErrorException(
                    f"Type error: function declared to return '{expected_return}' "
                    f"but return expression has type '{t}'."
                )

        else:
            raise TypeErrorException(f"Unknown statement type: {type(stmt)}")

    # ------------------------------------------------------------------
    # Expressions  (each call annotates node.type and returns the type)
    # ------------------------------------------------------------------

    def _check_expr(self, node) -> str:
        t = self._infer(node)
        node.type = t
        return t

    def _infer(self, node) -> str:
        if isinstance(node, A.IntLit):
            return 'int'

        if isinstance(node, A.FloatLit):
            return 'float'

        if isinstance(node, A.StringLit):
            return 'string'

        if isinstance(node, A.BoolLit):
            return 'bool'

        if isinstance(node, A.Var):
            t = self._lookup(node.name)
            if t is None:
                raise TypeErrorException(
                    f"Type error: variable '{node.name}' used before assignment."
                )
            return t

        if isinstance(node, A.BinOp):
            return self._infer_binop(node)

        if isinstance(node, A.Compare):
            return self._infer_compare(node)

        if isinstance(node, A.Call):
            return self._infer_call(node)

        raise TypeErrorException(f"Unknown expression node: {type(node)}")

    # Integer operators
    _INT_OPS   = {'+', '-', '*', '/'}
    # Float operators
    _FLOAT_OPS = {'+.', '-.', '*.', '/.'}
    # String operator
    _STR_OPS   = {'^'}

    def _infer_binop(self, node: A.BinOp) -> str:
        lt = self._check_expr(node.left)
        rt = self._check_expr(node.right)
        op = node.op

        if op in self._INT_OPS:
            if lt != 'int' or rt != 'int':
                raise TypeErrorException(
                    f"Type error: operator '{op}' requires int operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return 'int'

        if op in self._FLOAT_OPS:
            if lt != 'float' or rt != 'float':
                raise TypeErrorException(
                    f"Type error: operator '{op}' requires float operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return 'float'

        if op in self._STR_OPS:
            if lt != 'string' or rt != 'string':
                raise TypeErrorException(
                    f"Type error: operator '^' requires string operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return 'string'

        raise TypeErrorException(f"Unknown operator '{op}'.")

    def _infer_compare(self, node: A.Compare) -> str:
        lt = self._check_expr(node.left)
        rt = self._check_expr(node.right)
        if lt != rt:
            raise TypeErrorException(
                f"Type error: comparison '{node.op}' requires same type on both sides, "
                f"got '{lt}' and '{rt}'."
            )
        if lt not in ('int', 'float'):
            raise TypeErrorException(
                f"Type error: comparison '{node.op}' is only defined for "
                f"arithmetic (int/float) types, got '{lt}'."
            )
        return 'bool'

    def _infer_call(self, node: A.Call) -> str:
        if node.name not in self.func_env:
            raise TypeErrorException(
                f"Type error: call to undefined function '{node.name}'."
            )
        ret_type, param_types = self.func_env[node.name]
        if len(node.args) != len(param_types):
            raise TypeErrorException(
                f"Type error: function '{node.name}' expects "
                f"{len(param_types)} argument(s), got {len(node.args)}."
            )
        for i, (arg, expected) in enumerate(zip(node.args, param_types)):
            at = self._check_expr(arg)
            if at != expected:
                raise TypeErrorException(
                    f"Type error: argument {i+1} of '{node.name}' expected "
                    f"'{expected}', got '{at}'."
                )
        return ret_type
