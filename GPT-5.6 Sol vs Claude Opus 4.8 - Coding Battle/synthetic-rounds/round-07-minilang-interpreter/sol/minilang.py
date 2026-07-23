"""A small, deliberately self-contained interpreter for MiniLang."""


class MiniSyntaxError(Exception):
    pass


class MiniRuntimeError(Exception):
    pass


class Token:
    __slots__ = ("kind", "value", "line")

    def __init__(self, kind, value, line):
        self.kind, self.value, self.line = kind, value, line


KEYWORDS = {
    "let", "print", "if", "else", "while", "fn", "return",
    "true", "false", "nil",
}


def _lex(source):
    out = []
    i, line, n = 0, 1, len(source)
    two_char = {"||", "&&", "==", "!=", "<=", ">="}
    one_char = set("+-*/%!=<>(){}[];,")
    while i < n:
        c = source[i]
        if c in " \t\r":
            i += 1
        elif c == "\n":
            line += 1
            i += 1
        elif c == "/" and i + 1 < n and source[i + 1] == "/":
            i += 2
            while i < n and source[i] != "\n":
                i += 1
        elif c.isdigit():
            start = i
            while i < n and source[i].isdigit():
                i += 1
            out.append(Token("int", int(source[start:i]), line))
        elif c.isalpha() or c == "_":
            start = i
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
            word = source[start:i]
            out.append(Token(word if word in KEYWORDS else "id", word, line))
        elif c == '"':
            start_line = line
            i += 1
            chars = []
            while i < n and source[i] != '"':
                if source[i] == "\n":
                    line += 1
                if source[i] == "\\":
                    if i + 1 >= n or source[i + 1] not in ('"', "\\"):
                        raise MiniSyntaxError(f"line {line}: invalid string escape")
                    chars.append(source[i + 1])
                    i += 2
                else:
                    chars.append(source[i])
                    i += 1
            if i >= n:
                raise MiniSyntaxError(f"line {start_line}: unterminated string")
            i += 1
            out.append(Token("string", "".join(chars), start_line))
        elif i + 1 < n and source[i:i + 2] in two_char:
            out.append(Token(source[i:i + 2], source[i:i + 2], line))
            i += 2
        elif c in one_char:
            out.append(Token(c, c, line))
            i += 1
        else:
            raise MiniSyntaxError(f"line {line}: unexpected character {c!r}")
    out.append(Token("eof", None, line))
    return out


class Parser:
    def __init__(self, tokens):
        self.t = tokens
        self.i = 0
        self.function_depth = 0

    def peek(self):
        return self.t[self.i]

    def previous(self):
        return self.t[self.i - 1]

    def match(self, *kinds):
        if self.peek().kind in kinds:
            self.i += 1
            return True
        return False

    def need(self, kind, message=None):
        if self.peek().kind != kind:
            tok = self.peek()
            raise MiniSyntaxError(f"line {tok.line}: {message or 'expected ' + kind}")
        self.i += 1
        return self.previous()

    def program(self):
        stmts = []
        while self.peek().kind != "eof":
            stmts.append(self.statement())
        return stmts

    def statement(self):
        if self.match("let"):
            line = self.previous().line
            name = self.need("id", "expected variable name")
            self.need("=")
            value = self.expression()
            self.need(";", "expected ';'")
            return ("let", name.value, value, line)
        if self.match("print"):
            line = self.previous().line
            self.need("(")
            value = self.expression()
            self.need(")")
            self.need(";", "expected ';'")
            return ("print", value, line)
        if self.match("if"):
            line = self.previous().line
            self.need("(")
            cond = self.expression()
            self.need(")")
            yes = self.block()
            no = self.block() if self.match("else") else None
            return ("if", cond, yes, no, line)
        if self.match("while"):
            line = self.previous().line
            self.need("(")
            cond = self.expression()
            self.need(")")
            return ("while", cond, self.block(), line)
        if (self.peek().kind == "fn" and self.i + 1 < len(self.t)
                and self.t[self.i + 1].kind == "id"):
            self.i += 1
            line = self.previous().line
            name = self.need("id").value
            params, body = self.function_tail()
            return ("fndecl", name, params, body, line)
        if self.match("return"):
            tok = self.previous()
            if self.function_depth == 0:
                raise MiniSyntaxError(f"line {tok.line}: return outside function")
            value = ("lit", None, tok.line) if self.peek().kind == ";" else self.expression()
            self.need(";", "expected ';'")
            return ("return", value, tok.line)
        expr = self.expression()
        if self.match("="):
            line = self.previous().line
            if expr[0] not in ("var", "index"):
                raise MiniSyntaxError(f"line {line}: invalid assignment target")
            value = self.expression()
            self.need(";", "expected ';'")
            return ("assign", expr, value, line)
        self.need(";", "expected ';'")
        return ("expr", expr, expr[-1])

    def block(self):
        self.need("{", "expected '{'")
        body = []
        while self.peek().kind not in ("}", "eof"):
            body.append(self.statement())
        self.need("}", "expected '}'")
        return body

    def function_tail(self):
        self.need("(")
        params = []
        if self.peek().kind != ")":
            while True:
                params.append(self.need("id", "expected parameter name").value)
                if not self.match(","):
                    break
        self.need(")")
        self.function_depth += 1
        try:
            body = self.block()
        finally:
            self.function_depth -= 1
        return params, body

    def expression(self):
        return self.binary(0)

    PRECEDENCE = {
        "||": 1, "&&": 2, "==": 3, "!=": 3,
        "<": 4, "<=": 4, ">": 4, ">=": 4,
        "+": 5, "-": 5, "*": 6, "/": 6, "%": 6,
    }

    def binary(self, minimum):
        left = self.unary()
        while self.peek().kind in self.PRECEDENCE and self.PRECEDENCE[self.peek().kind] >= minimum:
            op = self.peek()
            self.i += 1
            right = self.binary(self.PRECEDENCE[op.kind] + 1)
            left = ("binary", op.kind, left, right, op.line)
        return left

    def unary(self):
        if self.match("!", "-"):
            op = self.previous()
            return ("unary", op.kind, self.unary(), op.line)
        return self.postfix()

    def postfix(self):
        expr = self.primary()
        while True:
            if self.match("("):
                line = self.previous().line
                args = []
                if self.peek().kind != ")":
                    while True:
                        args.append(self.expression())
                        if not self.match(","):
                            break
                self.need(")")
                expr = ("call", expr, args, line)
            elif self.match("["):
                line = self.previous().line
                index = self.expression()
                self.need("]")
                expr = ("index", expr, index, line)
            else:
                return expr

    def primary(self):
        tok = self.peek()
        self.i += 1
        if tok.kind in ("int", "string"):
            return ("lit", tok.value, tok.line)
        if tok.kind == "true":
            return ("lit", True, tok.line)
        if tok.kind == "false":
            return ("lit", False, tok.line)
        if tok.kind == "nil":
            return ("lit", None, tok.line)
        if tok.kind == "id":
            return ("var", tok.value, tok.line)
        if tok.kind == "(":
            expr = self.expression()
            self.need(")")
            return expr
        if tok.kind == "[":
            items = []
            if self.peek().kind != "]":
                while True:
                    items.append(self.expression())
                    if not self.match(","):
                        break
            self.need("]")
            return ("array", items, tok.line)
        if tok.kind == "fn":
            params, body = self.function_tail()
            return ("fn", params, body, tok.line)
        raise MiniSyntaxError(f"line {tok.line}: expected expression")


class Env:
    __slots__ = ("parent", "values")

    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def declare(self, name, value):
        self.values[name] = value

    def get(self, name, line):
        env = self
        while env is not None:
            if name in env.values:
                return env.values[name]
            env = env.parent
        raise MiniRuntimeError(f"line {line}: undefined variable '{name}'")

    def assign(self, name, value, line):
        env = self
        while env is not None:
            if name in env.values:
                env.values[name] = value
                return
            env = env.parent
        raise MiniRuntimeError(f"line {line}: undefined variable '{name}'")


class Function:
    __slots__ = ("params", "body", "closure")

    def __init__(self, params, body, closure):
        self.params, self.body, self.closure = params, body, closure


class Builtin:
    __slots__ = ("name", "arity", "func")

    def __init__(self, name, arity, func):
        self.name, self.arity, self.func = name, arity, func


class ReturnSignal(Exception):
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value


class TailCall:
    __slots__ = ("callee", "args", "line")

    def __init__(self, callee, args, line):
        self.callee, self.args, self.line = callee, args, line


def _truth(value):
    return value is not False and value is not None


def _typename(value):
    if value is None:
        return "nil"
    if type(value) is bool:
        return "bool"
    if type(value) is int:
        return "int"
    if type(value) is str:
        return "string"
    if type(value) is list:
        return "array"
    if isinstance(value, (Function, Builtin)):
        return "function"
    return type(value).__name__


class Interpreter:
    def __init__(self):
        self.output = []
        self.globals = Env()
        self.globals.declare("len", Builtin("len", 1, self._builtin_len))
        self.globals.declare("push", Builtin("push", 2, self._builtin_push))

    def error(self, line, message):
        raise MiniRuntimeError(f"line {line}: {message}")

    def _builtin_len(self, args, line):
        value = args[0]
        if type(value) not in (str, list):
            self.error(line, "len expects a string or array")
        return len(value)

    def _builtin_push(self, args, line):
        if type(args[0]) is not list:
            self.error(line, "push expects an array")
        args[0].append(args[1])
        return None

    def format(self, value):
        if value is None:
            return "nil"
        if type(value) is bool:
            return "true" if value else "false"
        if type(value) is list:
            return "[" + ", ".join(self.format(x) for x in value) + "]"
        if isinstance(value, (Function, Builtin)):
            return "<fn>"
        return str(value)

    def eval(self, node, env):
        kind = node[0]
        if kind == "lit":
            return node[1]
        if kind == "var":
            return env.get(node[1], node[2])
        if kind == "array":
            return [self.eval(x, env) for x in node[1]]
        if kind == "fn":
            return Function(node[1], node[2], env)
        if kind == "unary":
            op, value, line = node[1], self.eval(node[2], env), node[3]
            if op == "!":
                return not _truth(value)
            if type(value) is not int:
                self.error(line, "unary '-' expects an int")
            return -value
        if kind == "binary":
            op, line = node[1], node[4]
            left = self.eval(node[2], env)
            if op == "&&":
                return False if not _truth(left) else bool(_truth(self.eval(node[3], env)))
            if op == "||":
                return True if _truth(left) else bool(_truth(self.eval(node[3], env)))
            right = self.eval(node[3], env)
            return self.binary(op, left, right, line)
        if kind == "call":
            callee = self.eval(node[1], env)
            args = [self.eval(x, env) for x in node[2]]
            return self.invoke(callee, args, node[3])
        if kind == "index":
            value = self.eval(node[1], env)
            index = self.eval(node[2], env)
            return self.index(value, index, node[3])
        raise AssertionError(kind)

    def binary(self, op, a, b, line):
        if op in ("==", "!="):
            if type(a) is list or type(b) is list:
                equal = type(a) is list and type(b) is list and a is b
            elif isinstance(a, (Function, Builtin)) or isinstance(b, (Function, Builtin)):
                equal = a is b
            elif type(a) is type(b) and type(a) in (int, str, bool):
                equal = a == b
            else:
                equal = a is None and b is None
            return equal if op == "==" else not equal
        if op == "+":
            if type(a) is int and type(b) is int:
                return a + b
            if type(a) is str and type(b) is str:
                return a + b
            self.error(line, "'+' expects two ints or two strings")
        if op in ("-", "*", "/", "%"):
            if type(a) is not int or type(b) is not int:
                self.error(line, f"'{op}' expects two ints")
            if op in ("/", "%") and b == 0:
                self.error(line, "division by zero")
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            q = abs(a) // abs(b)
            if (a < 0) != (b < 0):
                q = -q
            return q if op == "/" else a - q * b
        if op in ("<", "<=", ">", ">="):
            if type(a) is not int or type(b) is not int:
                self.error(line, f"'{op}' expects two ints")
            return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[op]
        raise AssertionError(op)

    def index(self, value, index, line):
        if type(value) is not list:
            self.error(line, "indexing expects an array")
        if type(index) is not int:
            self.error(line, "index must be an int")
        if index < 0 or index >= len(value):
            self.error(line, "index out of range")
        return value[index]

    def invoke(self, callee, args, line):
        while True:
            if isinstance(callee, Builtin):
                if len(args) != callee.arity:
                    self.error(line, f"wrong argument count for {callee.name}")
                return callee.func(args, line)
            if not isinstance(callee, Function):
                self.error(line, f"cannot call {_typename(callee)}")
            if len(args) != len(callee.params):
                self.error(line, "wrong argument count")
            call_env = Env(callee.closure)
            for name, value in zip(callee.params, args):
                call_env.declare(name, value)
            try:
                self.exec_statements(callee.body, call_env)
                return None
            except ReturnSignal as signal:
                result = signal.value
            if isinstance(result, TailCall):
                callee, args, line = result.callee, result.args, result.line
                continue
            return result

    def exec_block(self, statements, parent):
        self.exec_statements(statements, Env(parent))

    def exec_statements(self, statements, env):
        for stmt in statements:
            kind = stmt[0]
            if kind == "let":
                env.declare(stmt[1], self.eval(stmt[2], env))
            elif kind == "fndecl":
                # Installing the binding before constructing the closure makes
                # recursive declarations work, while still capturing by reference.
                env.declare(stmt[1], None)
                env.assign(stmt[1], Function(stmt[2], stmt[3], env), stmt[4])
            elif kind == "assign":
                target = stmt[1]
                if target[0] == "var":
                    value = self.eval(stmt[2], env)
                    env.assign(target[1], value, target[2])
                else:
                    collection = self.eval(target[1], env)
                    index = self.eval(target[2], env)
                    if type(collection) is not list:
                        self.error(target[3], "index assignment expects an array")
                    if type(index) is not int:
                        self.error(target[3], "index must be an int")
                    if index < 0 or index >= len(collection):
                        self.error(target[3], "index out of range")
                    value = self.eval(stmt[2], env)
                    collection[index] = value
            elif kind == "print":
                self.output.append(self.format(self.eval(stmt[1], env)))
            elif kind == "expr":
                self.eval(stmt[1], env)
            elif kind == "if":
                branch = stmt[2] if _truth(self.eval(stmt[1], env)) else stmt[3]
                if branch is not None:
                    self.exec_block(branch, env)
            elif kind == "while":
                while _truth(self.eval(stmt[1], env)):
                    self.exec_block(stmt[2], env)
            elif kind == "return":
                expr = stmt[1]
                if expr[0] == "call":
                    callee = self.eval(expr[1], env)
                    args = [self.eval(x, env) for x in expr[2]]
                    raise ReturnSignal(TailCall(callee, args, expr[3]))
                raise ReturnSignal(self.eval(expr, env))
            else:
                raise AssertionError(kind)

    def run(self, statements):
        self.exec_statements(statements, self.globals)
        return self.output


def run(source: str) -> list[str]:
    """Parse and execute *source*, returning the lines printed by the program."""
    return Interpreter().run(Parser(_lex(source)).program())
