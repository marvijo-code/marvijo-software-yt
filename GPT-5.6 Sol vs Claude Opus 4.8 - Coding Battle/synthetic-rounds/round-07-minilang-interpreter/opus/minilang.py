"""MiniLang - a small interpreter with closures and proper tail calls."""

import sys

sys.setrecursionlimit(20000)


class MiniSyntaxError(Exception):
    pass


class MiniRuntimeError(Exception):
    pass


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------

KEYWORDS = {'let', 'print', 'if', 'else', 'while', 'fn', 'return',
            'true', 'false', 'nil'}


def tokenize(src):
    tokens = []
    i = 0
    n = len(src)
    line = 1
    while i < n:
        c = src[i]
        if c == '\n':
            line += 1
            i += 1
            continue
        if c in ' \t\r':
            i += 1
            continue
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            continue
        if c.isdigit():
            j = i
            while j < n and src[j].isdigit():
                j += 1
            tokens.append(('int', int(src[i:j]), line))
            i = j
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (src[j].isalnum() or src[j] == '_'):
                j += 1
            word = src[i:j]
            i = j
            if word in KEYWORDS:
                tokens.append((word, word, line))
            else:
                tokens.append(('ident', word, line))
            continue
        if c == '"':
            j = i + 1
            buf = []
            start_line = line
            while j < n and src[j] != '"':
                ch = src[j]
                if ch == '\\':
                    if j + 1 < n:
                        nxt = src[j + 1]
                        if nxt == '"':
                            buf.append('"')
                        elif nxt == '\\':
                            buf.append('\\')
                        else:
                            buf.append(nxt)
                        j += 2
                        continue
                    else:
                        raise MiniSyntaxError(
                            f"line {start_line}: unterminated string")
                if ch == '\n':
                    line += 1
                buf.append(ch)
                j += 1
            if j >= n:
                raise MiniSyntaxError(f"line {start_line}: unterminated string")
            tokens.append(('str', ''.join(buf), start_line))
            i = j + 1
            continue
        two = src[i:i + 2]
        if two in ('||', '&&', '==', '!=', '<=', '>='):
            tokens.append((two, two, line))
            i += 2
            continue
        if c in '+-*/%!<>=(){}[],;':
            tokens.append((c, c, line))
            i += 1
            continue
        raise MiniSyntaxError(f"line {line}: unexpected character {c!r}")
    tokens.append(('eof', None, line))
    return tokens


# ---------------------------------------------------------------------------
# Parser (recursive descent)
# ---------------------------------------------------------------------------

class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peektype(self):
        return self.toks[self.i][0]

    def check(self, tp):
        return self.toks[self.i][0] == tp

    def advance(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def match(self, tp):
        if self.toks[self.i][0] == tp:
            self.i += 1
            return True
        return False

    def expect(self, tp, what=None):
        t = self.toks[self.i]
        if t[0] != tp:
            raise MiniSyntaxError(
                f"line {t[2]}: expected {what or tp!r}, got {t[1]!r}")
        self.i += 1
        return t

    # -- statements --

    def program(self):
        stmts = []
        while not self.check('eof'):
            stmts.append(self.statement())
        return stmts

    def statement(self):
        tp = self.peektype()
        if tp == 'let':
            return self.let_stmt()
        if tp == 'print':
            return self.print_stmt()
        if tp == 'if':
            return self.if_stmt()
        if tp == 'while':
            return self.while_stmt()
        if tp == 'return':
            return self.return_stmt()
        if tp == 'fn' and self.toks[self.i + 1][0] == 'ident':
            return self.fn_decl()
        return self.expr_or_assign()

    def block(self):
        self.expect('{')
        stmts = []
        while not self.check('}') and not self.check('eof'):
            stmts.append(self.statement())
        self.expect('}')
        return stmts

    def let_stmt(self):
        self.advance()
        name = self.expect('ident', 'variable name')[1]
        self.expect('=')
        e = self.expression()
        self.expect(';')
        return ('let', name, e)

    def print_stmt(self):
        self.advance()
        self.expect('(')
        e = self.expression()
        self.expect(')')
        self.expect(';')
        return ('print', e)

    def if_stmt(self):
        self.advance()
        self.expect('(')
        cond = self.expression()
        self.expect(')')
        then = self.block()
        els = None
        if self.match('else'):
            if self.check('if'):
                els = [self.if_stmt()]
            else:
                els = self.block()
        return ('if', cond, then, els)

    def while_stmt(self):
        self.advance()
        self.expect('(')
        cond = self.expression()
        self.expect(')')
        body = self.block()
        return ('while', cond, body)

    def return_stmt(self):
        line = self.advance()[2]
        if self.check(';'):
            self.advance()
            return ('return', None, line)
        e = self.expression()
        self.expect(';')
        return ('return', e, line)

    def param_list(self):
        self.expect('(')
        params = []
        if not self.check(')'):
            params.append(self.expect('ident', 'parameter')[1])
            while self.match(','):
                params.append(self.expect('ident', 'parameter')[1])
        self.expect(')')
        return params

    def fn_decl(self):
        line = self.advance()[2]
        name = self.expect('ident')[1]
        params = self.param_list()
        body = self.block()
        return ('fndecl', name, params, body, line)

    def expr_or_assign(self):
        e = self.expression()
        if self.check('='):
            line = self.advance()[2]
            val = self.expression()
            self.expect(';')
            if e[0] == 'var':
                return ('assignvar', e[1], val, line)
            if e[0] == 'index':
                return ('assignidx', e[1], e[2], val, e[3])
            raise MiniSyntaxError(f"line {line}: invalid assignment target")
        self.expect(';')
        return ('exprstmt', e)

    # -- expressions --

    def expression(self):
        return self.logic_or()

    def logic_or(self):
        left = self.logic_and()
        while self.check('||'):
            self.advance()
            right = self.logic_and()
            left = ('logic', '||', left, right)
        return left

    def logic_and(self):
        left = self.equality()
        while self.check('&&'):
            self.advance()
            right = self.equality()
            left = ('logic', '&&', left, right)
        return left

    def equality(self):
        left = self.comparison()
        while self.peektype() in ('==', '!='):
            op = self.advance()
            right = self.comparison()
            left = ('bin', op[0], left, right, op[2])
        return left

    def comparison(self):
        left = self.term()
        while self.peektype() in ('<', '<=', '>', '>='):
            op = self.advance()
            right = self.term()
            left = ('bin', op[0], left, right, op[2])
        return left

    def term(self):
        left = self.factor()
        while self.peektype() in ('+', '-'):
            op = self.advance()
            right = self.factor()
            left = ('bin', op[0], left, right, op[2])
        return left

    def factor(self):
        left = self.unary()
        while self.peektype() in ('*', '/', '%'):
            op = self.advance()
            right = self.unary()
            left = ('bin', op[0], left, right, op[2])
        return left

    def unary(self):
        tp = self.peektype()
        if tp == '!' or tp == '-':
            op = self.advance()
            operand = self.unary()
            return ('un', op[0], operand, op[2])
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            tp = self.peektype()
            if tp == '(':
                line = self.advance()[2]
                args = []
                if not self.check(')'):
                    args.append(self.expression())
                    while self.match(','):
                        args.append(self.expression())
                self.expect(')')
                e = ('call', e, args, line)
            elif tp == '[':
                line = self.advance()[2]
                idx = self.expression()
                self.expect(']')
                e = ('index', e, idx, line)
            else:
                break
        return e

    def primary(self):
        t = self.advance()
        tp = t[0]
        if tp == 'int':
            return ('int', t[1])
        if tp == 'str':
            return ('str', t[1])
        if tp == 'true':
            return ('bool', True)
        if tp == 'false':
            return ('bool', False)
        if tp == 'nil':
            return ('nil',)
        if tp == 'ident':
            return ('var', t[1], t[2])
        if tp == '(':
            e = self.expression()
            self.expect(')')
            return e
        if tp == '[':
            line = t[2]
            elems = []
            if not self.check(']'):
                elems.append(self.expression())
                while self.match(','):
                    elems.append(self.expression())
            self.expect(']')
            return ('array', elems, line)
        if tp == 'fn':
            line = t[2]
            params = self.param_list()
            body = self.block()
            return ('fn', params, body, line)
        raise MiniSyntaxError(f"line {t[2]}: unexpected token {t[1]!r}")


# ---------------------------------------------------------------------------
# Runtime values
# ---------------------------------------------------------------------------

class Env:
    __slots__ = ('vars', 'parent')

    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent


class Function:
    __slots__ = ('params', 'body', 'closure')

    def __init__(self, params, body, closure):
        self.params = params
        self.body = body
        self.closure = closure


class Builtin:
    __slots__ = ('name',)

    def __init__(self, name):
        self.name = name

    def call(self, args, line):
        if self.name == 'len':
            if len(args) != 1:
                raise MiniRuntimeError(f"line {line}: wrong arg count")
            v = args[0]
            if type(v) is str or type(v) is list:
                return len(v)
            raise MiniRuntimeError(
                f"line {line}: len expects string or array")
        if self.name == 'push':
            if len(args) != 2:
                raise MiniRuntimeError(f"line {line}: wrong arg count")
            a = args[0]
            if type(a) is not list:
                raise MiniRuntimeError(f"line {line}: push expects array")
            a.append(args[1])
            return None
        raise MiniRuntimeError(f"line {line}: unknown builtin")


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------

OUTPUT = []


def truthy(v):
    return not (v is False or v is None)


def format_val(v):
    if v is None:
        return "nil"
    t = type(v)
    if t is bool:
        return "true" if v else "false"
    if t is int:
        return str(v)
    if t is str:
        return v
    if t is list:
        return "[" + ", ".join(format_val(x) for x in v) + "]"
    return "<fn>"


def eq(a, b):
    ta, tb = type(a), type(b)
    if ta is list or tb is list:
        return a is b
    if ta is bool or tb is bool:
        return ta is tb and a == b
    if a is None or b is None:
        return a is None and b is None
    if ta is int and tb is int:
        return a == b
    if ta is str and tb is str:
        return a == b
    return False


def idiv(a, b):
    q = a // b
    if (a % b != 0) and ((a < 0) != (b < 0)):
        q += 1
    return q


def imod(a, b):
    return a - idiv(a, b) * b


def binop(op, a, b, line):
    if op == '+':
        ta, tb = type(a), type(b)
        if ta is int and tb is int:
            return a + b
        if ta is str and tb is str:
            return a + b
        raise MiniRuntimeError(f"line {line}: bad operands for +")
    if op == '-':
        if type(a) is int and type(b) is int:
            return a - b
        raise MiniRuntimeError(f"line {line}: bad operands for -")
    if op == '*':
        if type(a) is int and type(b) is int:
            return a * b
        raise MiniRuntimeError(f"line {line}: bad operands for *")
    if op == '/':
        if type(a) is int and type(b) is int:
            if b == 0:
                raise MiniRuntimeError(f"line {line}: division by zero")
            return idiv(a, b)
        raise MiniRuntimeError(f"line {line}: bad operands for /")
    if op == '%':
        if type(a) is int and type(b) is int:
            if b == 0:
                raise MiniRuntimeError(f"line {line}: division by zero")
            return imod(a, b)
        raise MiniRuntimeError(f"line {line}: bad operands for %")
    if op == '==':
        return eq(a, b)
    if op == '!=':
        return not eq(a, b)
    # < <= > >=
    ta, tb = type(a), type(b)
    if (ta is int and tb is int) or (ta is str and tb is str):
        if op == '<':
            return a < b
        if op == '<=':
            return a <= b
        if op == '>':
            return a > b
        return a >= b
    raise MiniRuntimeError(f"line {line}: bad operands for {op}")


def ev(node, env):
    k = node[0]
    if k == 'var':
        name = node[1]
        e = env
        while e is not None:
            d = e.vars
            if name in d:
                return d[name]
            e = e.parent
        raise MiniRuntimeError(
            f"line {node[2]}: undefined variable {name!r}")
    if k == 'int' or k == 'str' or k == 'bool':
        return node[1]
    if k == 'nil':
        return None
    if k == 'bin':
        return binop(node[1], ev(node[2], env), ev(node[3], env), node[4])
    if k == 'call':
        func = ev(node[1], env)
        args = [ev(a, env) for a in node[2]]
        return call_function(func, args, node[3])
    if k == 'logic':
        op = node[1]
        left = ev(node[2], env)
        if op == '&&':
            if not truthy(left):
                return False
            return truthy(ev(node[3], env))
        else:
            if truthy(left):
                return True
            return truthy(ev(node[3], env))
    if k == 'un':
        v = ev(node[2], env)
        if node[1] == '!':
            return not truthy(v)
        if type(v) is int:
            return -v
        raise MiniRuntimeError(f"line {node[3]}: bad operand for -")
    if k == 'index':
        arr = ev(node[1], env)
        idx = ev(node[2], env)
        line = node[3]
        t = type(arr)
        if t is list or t is str:
            if type(idx) is not int:
                raise MiniRuntimeError(f"line {line}: index must be an int")
            if idx < 0 or idx >= len(arr):
                raise MiniRuntimeError(f"line {line}: index out of range")
            return arr[idx]
        raise MiniRuntimeError(f"line {line}: cannot index this value")
    if k == 'array':
        return [ev(e, env) for e in node[1]]
    if k == 'fn':
        return Function(node[1], node[2], env)
    raise MiniRuntimeError(f"line ?: unknown expression {k}")


def exec_stmts(stmts, env):
    for s in stmts:
        sig = exec_stmt(s, env)
        if sig is not None:
            return sig
    return None


def exec_stmt(node, env):
    k = node[0]
    if k == 'exprstmt':
        ev(node[1], env)
        return None
    if k == 'let':
        env.vars[node[1]] = ev(node[2], env)
        return None
    if k == 'print':
        OUTPUT.append(format_val(ev(node[1], env)))
        return None
    if k == 'assignvar':
        name = node[1]
        val = ev(node[2], env)
        e = env
        while e is not None:
            if name in e.vars:
                e.vars[name] = val
                return None
            e = e.parent
        raise MiniRuntimeError(
            f"line {node[3]}: undefined variable {name!r}")
    if k == 'if':
        if truthy(ev(node[1], env)):
            return exec_stmts(node[2], env)
        elif node[3] is not None:
            return exec_stmts(node[3], env)
        return None
    if k == 'while':
        cond = node[1]
        body = node[2]
        while truthy(ev(cond, env)):
            sig = exec_stmts(body, env)
            if sig is not None:
                return sig
        return None
    if k == 'return':
        expr = node[1]
        if expr is None:
            return ('ret', None)
        if expr[0] == 'call':
            func = ev(expr[1], env)
            args = [ev(a, env) for a in expr[2]]
            return ('tail', func, args, expr[3])
        return ('ret', ev(expr, env))
    if k == 'fndecl':
        env.vars[node[1]] = Function(node[2], node[3], env)
        return None
    if k == 'assignidx':
        arr = ev(node[1], env)
        idx = ev(node[2], env)
        val = ev(node[3], env)
        line = node[4]
        if type(arr) is not list:
            raise MiniRuntimeError(
                f"line {line}: cannot index-assign this value")
        if type(idx) is not int:
            raise MiniRuntimeError(f"line {line}: index must be an int")
        if idx < 0 or idx >= len(arr):
            raise MiniRuntimeError(f"line {line}: index out of range")
        arr[idx] = val
        return None
    raise MiniRuntimeError(f"unknown statement {k}")


def call_function(func, args, line):
    while True:
        if isinstance(func, Function):
            if len(args) != len(func.params):
                raise MiniRuntimeError(f"line {line}: wrong arg count")
            env = Env(func.closure)
            d = env.vars
            for p, a in zip(func.params, args):
                d[p] = a
            sig = exec_stmts(func.body, env)
            if sig is None:
                return None
            t = sig[0]
            if t == 'ret':
                return sig[1]
            # tail call: loop with the new callee
            func = sig[1]
            args = sig[2]
            line = sig[3]
            continue
        if isinstance(func, Builtin):
            return func.call(args, line)
        raise MiniRuntimeError(f"line {line}: calling a non-function")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(source):
    global OUTPUT
    OUTPUT = []
    tokens = tokenize(source)
    prog = Parser(tokens).program()
    g = Env(None)
    g.vars['len'] = Builtin('len')
    g.vars['push'] = Builtin('push')
    exec_stmts(prog, g)
    return OUTPUT
