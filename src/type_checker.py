"""
type_checker.py - Static type checker with monomorphic type inference.

Because the PL language has no explicit variable declarations (like "var x : int"),
the type of each variable is inferred on its *first assignment* and remains locked
thereafter. This is called static typing.

HOW THE TYPE-CHECKER WORKS:
1. Performs a first pass to record function signatures (name -> return_type, param_types).
2. Performs a second pass to walk the AST of each function body and the main statements.
3. Annotates each expression AST node with a `.type` attribute so the TAC Generator
   can know its type directly without re-inferring.
"""

from . import ast_nodes as A


class TypeErrorException(Exception):
    """Custom exception raised when a static type constraint is violated."""
    pass


class TypeChecker:
    def __init__(self):
        # Maps function name -> (return_type, [param_type_1, param_type_2, ...])
        self.func_env: dict[str, tuple[str, list[str]]] = {}
        
        # Scopes stack: each element is a dictionary mapping variable names to types.
        # This allows functions to have local scopes isolated from global variables.
        self.var_env: list[dict[str, str]] = [{}]

    # ------------------------------------------------------------------
    # Environment Scope Helpers
    # ------------------------------------------------------------------

    def _lookup(self, name: str) -> str | None:
        """Looks up a variable type starting from the local scope outward to global scope."""
        for scope in reversed(self.var_env):
            if name in scope:
                return scope[name]
        return None

    def _define(self, name: str, typ: str):
        """Locks a variable name to a specific type in the active (local) scope."""
        self.var_env[-1][name] = typ

    def _push(self):
        """Pushes a new local variable scope (used when entering a function)."""
        self.var_env.append({})

    def _pop(self):
        """Pops the current local scope (used when exiting a function)."""
        self.var_env.pop()

    # ------------------------------------------------------------------
    # Public Entry Point
    # ------------------------------------------------------------------

    def check(self, program: A.Program):
        """
        Validates the entire program AST.
        Raises TypeErrorException if any type-checking constraint fails.
        """
        # PASS 1: Populate function environment so functions can call each other mutually
        for f in program.funcs:
            param_types = [p.type for p in f.params]
            self.func_env[f.name] = (f.return_type, param_types)

        # PASS 2: Validate each function's inner body
        for f in program.funcs:
            self._check_func(f)

        # PASS 3: Validate all top-level statements in the main body
        for stmt in program.main:
            self._check_stmt(stmt)

    # ------------------------------------------------------------------
    # Function Verification
    # ------------------------------------------------------------------

    def _check_func(self, f: A.FuncDef):
        """Saves parameter types to a local scope, then verifies statements inside the function."""
        self._push()
        for p in f.params:
            self._define(p.name, p.type)
        for stmt in f.body:
            # Pass down the expected return type so we can verify Return statements match it
            self._check_stmt(stmt, expected_return=f.return_type)
        self._pop()

    # ------------------------------------------------------------------
    # Statement Verification
    # ------------------------------------------------------------------

    def _check_stmt(self, stmt, expected_return: str | None = None):
        """Checks statement constraints. Does not return any value."""
        
        # --- Assignment (e.g., x = 5) ---
        if isinstance(stmt, A.Assign):
            t = self._check_expr(stmt.expr)  # Infer type of expression
            existing = self._lookup(stmt.name)
            if existing is None:
                # Variable used for the first time: lock its type in the current scope
                self._define(stmt.name, t)
            elif existing != t:
                # Type mismatch on re-assignment
                raise TypeErrorException(
                    f"Type error: variable '{stmt.name}' already has type "
                    f"'{existing}' but is assigned a '{t}' value."
                )

        # --- If Statement ---
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

        # --- While Statement ---
        elif isinstance(stmt, A.While):
            ct = self._check_expr(stmt.cond)
            if ct != 'bool':
                raise TypeErrorException(
                    f"Type error: while-condition must be bool, got '{ct}'."
                )
            for s in stmt.body:
                self._check_stmt(s, expected_return)

        # --- Print Statement ---
        elif isinstance(stmt, A.Print):
            self._check_expr(stmt.expr)  # Print works with any valid type

        # --- Return Statement ---
        elif isinstance(stmt, A.Return):
            t = self._check_expr(stmt.expr)
            if expected_return is None:
                raise TypeErrorException(
                    "Type error: return statement used outside of function body."
                )
            if t != expected_return:
                raise TypeErrorException(
                    f"Type error: function declared to return '{expected_return}' "
                    f"but return expression has type '{t}'."
                )

        else:
            raise TypeErrorException(f"Unknown statement type: {type(stmt)}")

    # ------------------------------------------------------------------
    # Expression Inference & Annotation
    # ------------------------------------------------------------------

    def _check_expr(self, node) -> str:
        """Helper that infers type of node, stores it in node.type, and returns it."""
        t = self._infer(node)
        node.type = t  # Annotate the node for TAC Generator use!
        return t

    def _infer(self, node) -> str:
        """Core type-inference router."""
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

    # Defined operators categorizations
    _INT_OPS   = {'+', '-', '*', '/'}
    _FLOAT_OPS = {'+.', '-.', '*.', '/.'}
    _STR_OPS   = {'^'}

    def _infer_binop(self, node: A.BinOp) -> str:
        """Infers result types for binary operators and enforces static constraints."""
        lt = self._check_expr(node.left)
        rt = self._check_expr(node.right)
        op = node.op

        # Enforce that '+' / '-' / '*' / '/' only work on two integers
        if op in self._INT_OPS:
            if lt != 'int' or rt != 'int':
                raise TypeErrorException(
                    f"Type error: operator '{op}' requires int operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return 'int'

        # Enforce that '+.' / '-.' / '*.' / '/.' only work on two floats
        if op in self._FLOAT_OPS:
            if lt != 'float' or rt != 'float':
                raise TypeErrorException(
                    f"Type error: operator '{op}' requires float operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return 'float'

        # Enforce that '^' only works on two strings
        if op in self._STR_OPS:
            if lt != 'string' or rt != 'string':
                raise TypeErrorException(
                    f"Type error: operator '^' requires string operands, "
                    f"got '{lt}' and '{rt}'."
                )
            return 'string'

        raise TypeErrorException(f"Unknown operator '{op}'.")

    def _infer_compare(self, node: A.Compare) -> str:
        """Infers types for comparisons (=, <>), enforcing same types & arithmetic values."""
        lt = self._check_expr(node.left)
        rt = self._check_expr(node.right)
        
        if lt != rt:
            raise TypeErrorException(
                f"Type error: comparison '{node.op}' requires same type on both sides, "
                f"got '{lt}' and '{rt}'."
            )
        
        # In this language, comparisons are only defined for arithmetic types (int and float)
        if lt not in ('int', 'float'):
            raise TypeErrorException(
                f"Type error: comparison '{node.op}' is only defined for "
                f"arithmetic (int/float) types, got '{lt}'."
            )
        return 'bool'

    def _infer_call(self, node: A.Call) -> str:
        """Verifies that function call matches signature in function signatures map."""
        if node.name not in self.func_env:
            raise TypeErrorException(
                f"Type error: call to undefined function '{node.name}'."
            )
            
        ret_type, param_types = self.func_env[node.name]
        
        # Enforce exact argument count
        if len(node.args) != len(param_types):
            raise TypeErrorException(
                f"Type error: function '{node.name}' expects "
                f"{len(param_types)} argument(s), got {len(node.args)}."
            )
            
        # Verify type of each passed argument matches parameter expectations
        for i, (arg, expected) in enumerate(zip(node.args, param_types)):
            at = self._check_expr(arg)
            if at != expected:
                raise TypeErrorException(
                    f"Type error: argument {i+1} of '{node.name}' expected "
                    f"'{expected}', got '{at}'."
                )
        return ret_type
