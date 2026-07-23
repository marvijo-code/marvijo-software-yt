import re
import math


class FormulaError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


_TOKEN_RE = re.compile(
    r'''
      (?P<WS>\s+)
    | (?P<NUM>(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)
    | (?P<NAME>[A-Za-z][A-Za-z0-9]*)
    | (?P<OP>[+\-*/])
    | (?P<LP>\()
    | (?P<RP>\))
    | (?P<COMMA>,)
    | (?P<COLON>:)
    ''',
    re.VERBOSE,
)

_CELL_RE = re.compile(r'([A-Za-z]+)([0-9]+)$')


def _norm(name):
    s = name.strip()
    m = _CELL_RE.fullmatch(s)
    if m:
        return m.group(1).upper() + str(int(m.group(2)))
    return s.upper()


def normalize_cell(name):
    m = _CELL_RE.fullmatch(name)
    if not m:
        raise FormulaError('#ERROR!')
    return m.group(1).upper() + str(int(m.group(2)))


def try_number(s):
    st = s.strip()
    if re.fullmatch(r'[+-]?\d+', st):
        return (True, int(st))
    try:
        f = float(st)
    except (ValueError, TypeError):
        return (False, None)
    if not math.isfinite(f):
        return (False, None)
    return (True, int(f) if f.is_integer() else f)


def norm_num(v):
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def parse_num_literal(s):
    if re.fullmatch(r'[0-9]+', s):
        return int(s)
    f = float(s)
    return int(f) if f.is_integer() else f


def tokenize(s):
    tokens = []
    pos = 0
    n = len(s)
    while pos < n:
        m = _TOKEN_RE.match(s, pos)
        if not m or m.end() == pos:
            raise FormulaError('#ERROR!')
        pos = m.end()
        kind = m.lastgroup
        val = m.group()
        if kind == 'WS':
            continue
        if kind == 'NAME':
            if re.fullmatch(r'[A-Za-z]+[0-9]+', val):
                tokens.append(('CELL', val))
            elif re.fullmatch(r'[A-Za-z]+', val):
                tokens.append(('NAME', val))
            else:
                raise FormulaError('#ERROR!')
        else:
            tokens.append((kind, val))
    return tokens


def col_to_num(letters):
    n = 0
    for ch in letters.upper():
        n = n * 26 + (ord(ch) - 64)
    return n


def num_to_col(n):
    s = ''
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def split_cell(key):
    m = _CELL_RE.fullmatch(key)
    return m.group(1), int(m.group(2))


def expand_range(k1, k2):
    c1, r1 = split_cell(k1)
    c2, r2 = split_cell(k2)
    a1, a2 = col_to_num(c1), col_to_num(c2)
    lo_c, hi_c = min(a1, a2), max(a1, a2)
    lo_r, hi_r = min(r1, r2), max(r1, r2)
    keys = []
    for col in range(lo_c, hi_c + 1):
        for row in range(lo_r, hi_r + 1):
            keys.append(num_to_col(col) + str(row))
    return keys


class Parser:
    def __init__(self, tokens):
        self.toks = tokens
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def advance(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, kind):
        if self.peek()[0] != kind:
            raise FormulaError('#ERROR!')
        return self.advance()

    def parse(self):
        node = self.parse_expr()
        if self.i != len(self.toks):
            raise FormulaError('#ERROR!')
        return node

    def parse_expr(self):
        node = self.parse_term()
        while self.peek()[0] == 'OP' and self.peek()[1] in '+-':
            op = self.advance()[1]
            node = ('binop', op, node, self.parse_term())
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.peek()[0] == 'OP' and self.peek()[1] in '*/':
            op = self.advance()[1]
            node = ('binop', op, node, self.parse_factor())
        return node

    def parse_factor(self):
        if self.peek()[0] == 'OP' and self.peek()[1] == '-':
            self.advance()
            return ('neg', self.parse_factor())
        if self.peek()[0] == 'OP' and self.peek()[1] == '+':
            self.advance()
            return self.parse_factor()
        return self.parse_primary()

    def parse_primary(self):
        t = self.peek()
        if t[0] == 'NUM':
            self.advance()
            return ('num', parse_num_literal(t[1]))
        if t[0] == 'CELL':
            self.advance()
            return ('cell', normalize_cell(t[1]))
        if t[0] == 'LP':
            self.advance()
            node = self.parse_expr()
            self.expect('RP')
            return node
        if t[0] == 'NAME':
            name = self.advance()[1]
            self.expect('LP')
            args = self.parse_args()
            self.expect('RP')
            return ('func', name.upper(), args)
        raise FormulaError('#ERROR!')

    def parse_args(self):
        args = []
        if self.peek()[0] == 'RP':
            return args
        args.append(self.parse_arg())
        while self.peek()[0] == 'COMMA':
            self.advance()
            args.append(self.parse_arg())
        return args

    def parse_arg(self):
        if (self.peek()[0] == 'CELL'
                and self.i + 1 < len(self.toks)
                and self.toks[self.i + 1][0] == 'COLON'):
            c1 = self.advance()[1]
            self.advance()  # colon
            if self.peek()[0] != 'CELL':
                raise FormulaError('#ERROR!')
            c2 = self.advance()[1]
            return ('range', normalize_cell(c1), normalize_cell(c2))
        return self.parse_expr()


class Sheet:
    def __init__(self):
        self.cells = {}

    def set(self, cell, raw):
        self.cells[_norm(cell)] = raw

    def get(self, cell):
        tag, val = self._resolve(_norm(cell), set(), {})
        if tag == 'empty':
            return ""
        return val

    def _resolve(self, key, stack, memo):
        if key in memo:
            return memo[key]
        if key in stack:
            return ('err', '#CYCLE!')
        if key not in self.cells:
            res = ('empty', None)
            memo[key] = res
            return res
        raw = self.cells[key]
        ok, num = try_number(raw)
        if ok:
            res = ('num', num)
        elif raw.startswith('='):
            stack.add(key)
            try:
                v = self._eval_formula(raw[1:], stack, memo)
            finally:
                stack.discard(key)
            res = ('err', v) if isinstance(v, str) else ('num', v)
        else:
            res = ('text', raw)
        memo[key] = res
        return res

    def _eval_formula(self, body, stack, memo):
        try:
            tokens = tokenize(body)
            node = Parser(tokens).parse()
            return norm_num(self._eval_node(node, stack, memo))
        except FormulaError as e:
            return e.msg

    def _eval_node(self, node, stack, memo):
        t = node[0]
        if t == 'num':
            return node[1]
        if t == 'cell':
            tag, val = self._resolve(node[1], stack, memo)
            if tag == 'num':
                return val
            if tag == 'empty':
                return 0
            if tag == 'text':
                raise FormulaError('#ERROR!')
            raise FormulaError(val)
        if t == 'neg':
            return -self._eval_node(node[1], stack, memo)
        if t == 'binop':
            l = self._eval_node(node[2], stack, memo)
            r = self._eval_node(node[3], stack, memo)
            op = node[1]
            if op == '+':
                return l + r
            if op == '-':
                return l - r
            if op == '*':
                return l * r
            if op == '/':
                if r == 0:
                    raise FormulaError('#DIV/0!')
                return l / r
        if t == 'func':
            return self._eval_func(node[1], node[2], stack, memo)
        raise FormulaError('#ERROR!')

    def _eval_func(self, name, args, stack, memo):
        if name == 'SUM':
            total = 0
            for a in args:
                if a[0] == 'range':
                    for key in expand_range(a[1], a[2]):
                        tag, val = self._resolve(key, stack, memo)
                        if tag == 'num':
                            total += val
                        elif tag == 'err':
                            raise FormulaError(val)
                else:
                    total += self._eval_node(a, stack, memo)
            return total
        if name in ('MIN', 'MAX'):
            vals = []
            for a in args:
                if a[0] == 'range':
                    for key in expand_range(a[1], a[2]):
                        tag, val = self._resolve(key, stack, memo)
                        if tag == 'num':
                            vals.append(val)
                        elif tag == 'err':
                            raise FormulaError(val)
                else:
                    vals.append(self._eval_node(a, stack, memo))
            if not vals:
                raise FormulaError('#ERROR!')
            return min(vals) if name == 'MIN' else max(vals)
        if name == 'COUNT':
            cnt = 0
            for a in args:
                if a[0] == 'range':
                    for key in expand_range(a[1], a[2]):
                        tag, val = self._resolve(key, stack, memo)
                        if tag == 'num':
                            cnt += 1
                        elif tag == 'err':
                            raise FormulaError(val)
                elif a[0] == 'cell':
                    tag, val = self._resolve(a[1], stack, memo)
                    if tag == 'num':
                        cnt += 1
                    elif tag == 'err':
                        raise FormulaError(val)
                else:
                    self._eval_node(a, stack, memo)
                    cnt += 1
            return cnt
        raise FormulaError('#ERROR!')
