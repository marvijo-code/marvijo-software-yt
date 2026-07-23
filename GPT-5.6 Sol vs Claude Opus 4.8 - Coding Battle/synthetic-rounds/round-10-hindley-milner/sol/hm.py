"""Hindley--Milner type inference for the small AST described in task.md."""


class HMTypeError(Exception):
    """Raised when an expression has no Hindley--Milner type."""


class _Var:
    __slots__ = ("id", "instance")

    def __init__(self, ident):
        self.id = ident
        self.instance = None


class _Con:
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name


class _Fun:
    __slots__ = ("arg", "result")

    def __init__(self, arg, result):
        self.arg = arg
        self.result = result


class _Pair:
    __slots__ = ("left", "right")

    def __init__(self, left, right):
        self.left = left
        self.right = right


class _Scheme:
    __slots__ = ("variables", "type")

    def __init__(self, variables, typ):
        self.variables = tuple(variables)
        self.type = typ


_INT = _Con("int")
_BOOL = _Con("bool")


class _Inferencer:
    def __init__(self):
        self._next_id = 0

    def fresh(self):
        variable = _Var(self._next_id)
        self._next_id += 1
        return variable

    def prune(self, typ):
        if isinstance(typ, _Var) and typ.instance is not None:
            typ.instance = self.prune(typ.instance)
            return typ.instance
        return typ

    def occurs(self, variable, typ):
        typ = self.prune(typ)
        if typ is variable:
            return True
        if isinstance(typ, _Fun):
            return self.occurs(variable, typ.arg) or self.occurs(
                variable, typ.result
            )
        if isinstance(typ, _Pair):
            return self.occurs(variable, typ.left) or self.occurs(
                variable, typ.right
            )
        return False

    def unify(self, first, second):
        first = self.prune(first)
        second = self.prune(second)
        if first is second:
            return
        if isinstance(first, _Var):
            if self.occurs(first, second):
                raise HMTypeError("infinite type")
            first.instance = second
            return
        if isinstance(second, _Var):
            self.unify(second, first)
            return
        if isinstance(first, _Con) and isinstance(second, _Con):
            if first.name != second.name:
                raise HMTypeError("type mismatch")
            return
        if isinstance(first, _Fun) and isinstance(second, _Fun):
            self.unify(first.arg, second.arg)
            self.unify(first.result, second.result)
            return
        if isinstance(first, _Pair) and isinstance(second, _Pair):
            self.unify(first.left, second.left)
            self.unify(first.right, second.right)
            return
        raise HMTypeError("type mismatch")

    def free_type_vars(self, typ, result=None):
        if result is None:
            result = set()
        typ = self.prune(typ)
        if isinstance(typ, _Var):
            result.add(typ)
        elif isinstance(typ, _Fun):
            self.free_type_vars(typ.arg, result)
            self.free_type_vars(typ.result, result)
        elif isinstance(typ, _Pair):
            self.free_type_vars(typ.left, result)
            self.free_type_vars(typ.right, result)
        return result

    def free_scheme_vars(self, scheme):
        return self.free_type_vars(scheme.type) - set(scheme.variables)

    def free_env_vars(self, env):
        result = set()
        for scheme in env.values():
            result.update(self.free_scheme_vars(scheme))
        return result

    def generalize(self, env, typ):
        variables = self.free_type_vars(typ) - self.free_env_vars(env)
        return _Scheme(sorted(variables, key=lambda item: item.id), typ)

    def instantiate(self, scheme):
        replacements = {variable: self.fresh() for variable in scheme.variables}

        def copy(typ):
            typ = self.prune(typ)
            if isinstance(typ, _Var):
                return replacements.get(typ, typ)
            if isinstance(typ, _Fun):
                return _Fun(copy(typ.arg), copy(typ.result))
            if isinstance(typ, _Pair):
                return _Pair(copy(typ.left), copy(typ.right))
            return typ

        return copy(scheme.type)

    @staticmethod
    def _form(node, tag, length):
        if not isinstance(node, list) or len(node) != length or node[0] != tag:
            raise HMTypeError("malformed expression")

    def infer(self, node, env):
        if not isinstance(node, list) or not node:
            raise HMTypeError("malformed expression")
        tag = node[0]

        if tag == "lit":
            self._form(node, tag, 2)
            value = node[1]
            if isinstance(value, bool):
                return _BOOL
            if isinstance(value, int):
                return _INT
            raise HMTypeError("unsupported literal")

        if tag == "var":
            self._form(node, tag, 2)
            name = node[1]
            if name not in env:
                raise HMTypeError("unbound variable")
            return self.instantiate(env[name])

        if tag == "lam":
            self._form(node, tag, 3)
            name = node[1]
            argument = self.fresh()
            inner_env = env.copy()
            inner_env[name] = _Scheme((), argument)
            return _Fun(argument, self.infer(node[2], inner_env))

        if tag == "app":
            self._form(node, tag, 3)
            function = self.infer(node[1], env)
            argument = self.infer(node[2], env)
            result = self.fresh()
            self.unify(function, _Fun(argument, result))
            return result

        if tag == "let":
            self._form(node, tag, 4)
            name = node[1]
            value = self.infer(node[2], env)
            scheme = self.generalize(env, value)
            inner_env = env.copy()
            inner_env[name] = scheme
            return self.infer(node[3], inner_env)

        if tag == "letrec":
            self._form(node, tag, 4)
            name = node[1]
            assumed = self.fresh()
            recursive_env = env.copy()
            recursive_env[name] = _Scheme((), assumed)
            value = self.infer(node[2], recursive_env)
            self.unify(assumed, value)
            scheme = self.generalize(env, assumed)
            inner_env = env.copy()
            inner_env[name] = scheme
            return self.infer(node[3], inner_env)

        if tag == "if":
            self._form(node, tag, 4)
            condition = self.infer(node[1], env)
            self.unify(condition, _BOOL)
            then_type = self.infer(node[2], env)
            else_type = self.infer(node[3], env)
            self.unify(then_type, else_type)
            return then_type

        if tag == "pair":
            self._form(node, tag, 3)
            return _Pair(self.infer(node[1], env), self.infer(node[2], env))

        if tag in ("fst", "snd"):
            self._form(node, tag, 2)
            left = self.fresh()
            right = self.fresh()
            self.unify(self.infer(node[1], env), _Pair(left, right))
            return left if tag == "fst" else right

        if tag == "binop":
            self._form(node, tag, 4)
            op = node[1]
            if op not in ("+", "-", "<", "=="):
                raise HMTypeError("unknown binary operator")
            self.unify(self.infer(node[2], env), _INT)
            self.unify(self.infer(node[3], env), _INT)
            return _INT if op in ("+", "-") else _BOOL

        raise HMTypeError("unknown expression")

    def render(self, typ):
        names = {}

        def variable_name(variable):
            if variable not in names:
                index = len(names)
                # a..z, then aa..az, ba.. for unusually large types.
                name = ""
                while True:
                    name = chr(ord("a") + index % 26) + name
                    index = index // 26 - 1
                    if index < 0:
                        break
                names[variable] = name
            return names[variable]

        def format_type(current, argument_position=False):
            current = self.prune(current)
            if isinstance(current, _Var):
                return variable_name(current)
            if isinstance(current, _Con):
                return current.name
            if isinstance(current, _Pair):
                return (
                    "("
                    + format_type(current.left, True)
                    + " * "
                    + format_type(current.right, True)
                    + ")"
                )
            if isinstance(current, _Fun):
                rendered = (
                    format_type(current.arg, True)
                    + " -> "
                    + format_type(current.result)
                )
                return "(" + rendered + ")" if argument_position else rendered
            raise HMTypeError("invalid inferred type")

        return format_type(typ)


def infer(ast) -> str:
    """Return the canonical principal type of *ast*, or raise HMTypeError."""
    engine = _Inferencer()
    return engine.render(engine.infer(ast, {}))
