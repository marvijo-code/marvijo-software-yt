"""Hindley-Milner type inference (Algorithm W)."""


class HMTypeError(Exception):
    pass


# --- Types --------------------------------------------------------------

class TVar:
    __slots__ = ("instance",)

    def __init__(self):
        self.instance = None


class TCon:
    __slots__ = ("name",)

    def __init__(self, name):
        self.name = name


class TFun:
    __slots__ = ("arg", "res")

    def __init__(self, arg, res):
        self.arg = arg
        self.res = res


class TPair:
    __slots__ = ("a", "b")

    def __init__(self, a, b):
        self.a = a
        self.b = b


class Scheme:
    __slots__ = ("qvars", "typ")

    def __init__(self, qvars, typ):
        self.qvars = qvars
        self.typ = typ


# --- Core operations ----------------------------------------------------

def prune(t):
    if isinstance(t, TVar) and t.instance is not None:
        t.instance = prune(t.instance)
        return t.instance
    return t


def occurs(v, t):
    t = prune(t)
    if t is v:
        return True
    if isinstance(t, TFun):
        return occurs(v, t.arg) or occurs(v, t.res)
    if isinstance(t, TPair):
        return occurs(v, t.a) or occurs(v, t.b)
    return False


def unify(a, b):
    a = prune(a)
    b = prune(b)
    if isinstance(a, TVar):
        if a is not b:
            if occurs(a, b):
                raise HMTypeError("occurs check")
            a.instance = b
    elif isinstance(b, TVar):
        unify(b, a)
    elif isinstance(a, TCon) and isinstance(b, TCon):
        if a.name != b.name:
            raise HMTypeError("cannot unify %s and %s" % (a.name, b.name))
    elif isinstance(a, TFun) and isinstance(b, TFun):
        unify(a.arg, b.arg)
        unify(a.res, b.res)
    elif isinstance(a, TPair) and isinstance(b, TPair):
        unify(a.a, b.a)
        unify(a.b, b.b)
    else:
        raise HMTypeError("type mismatch")


def free_type_vars(t):
    t = prune(t)
    if isinstance(t, TVar):
        return {t}
    if isinstance(t, TFun):
        return free_type_vars(t.arg) | free_type_vars(t.res)
    if isinstance(t, TPair):
        return free_type_vars(t.a) | free_type_vars(t.b)
    return set()


def env_free_vars(env):
    result = set()
    for s in env.values():
        result |= (free_type_vars(s.typ) - set(s.qvars))
    return result


def instantiate(scheme):
    mapping = {v: TVar() for v in scheme.qvars}

    def copy(t):
        t = prune(t)
        if isinstance(t, TVar):
            return mapping.get(t, t)
        if isinstance(t, TFun):
            return TFun(copy(t.arg), copy(t.res))
        if isinstance(t, TPair):
            return TPair(copy(t.a), copy(t.b))
        return t

    return copy(scheme.typ)


def generalize(env, t):
    qvars = list(free_type_vars(t) - env_free_vars(env))
    return Scheme(qvars, t)


# --- Inference ----------------------------------------------------------

def analyze(node, env):
    if not isinstance(node, (list, tuple)) or not node:
        raise HMTypeError("malformed node")
    tag = node[0]

    if tag == "lit":
        v = node[1]
        if isinstance(v, bool):
            return TCon("bool")
        if isinstance(v, int):
            return TCon("int")
        raise HMTypeError("unknown literal")

    if tag == "var":
        name = node[1]
        s = env.get(name)
        if s is None:
            raise HMTypeError("unbound variable %r" % (name,))
        return instantiate(s)

    if tag == "lam":
        name = node[1]
        argt = TVar()
        new_env = dict(env)
        new_env[name] = Scheme([], argt)
        rest = analyze(node[2], new_env)
        return TFun(argt, rest)

    if tag == "app":
        f = analyze(node[1], env)
        x = analyze(node[2], env)
        rt = TVar()
        unify(f, TFun(x, rt))
        return rt

    if tag == "let":
        name = node[1]
        t1 = analyze(node[2], env)
        new_env = dict(env)
        new_env[name] = generalize(env, t1)
        return analyze(node[3], new_env)

    if tag == "letrec":
        name = node[1]
        argt = TVar()
        env1 = dict(env)
        env1[name] = Scheme([], argt)
        t1 = analyze(node[2], env1)
        unify(argt, t1)
        env2 = dict(env)
        env2[name] = generalize(env, argt)
        return analyze(node[3], env2)

    if tag == "if":
        c = analyze(node[1], env)
        unify(c, TCon("bool"))
        t = analyze(node[2], env)
        e = analyze(node[3], env)
        unify(t, e)
        return t

    if tag == "pair":
        return TPair(analyze(node[1], env), analyze(node[2], env))

    if tag == "fst":
        t = analyze(node[1], env)
        a = TVar()
        b = TVar()
        unify(t, TPair(a, b))
        return a

    if tag == "snd":
        t = analyze(node[1], env)
        a = TVar()
        b = TVar()
        unify(t, TPair(a, b))
        return b

    if tag == "binop":
        op = node[1]
        a = analyze(node[2], env)
        b = analyze(node[3], env)
        unify(a, TCon("int"))
        unify(b, TCon("int"))
        if op in ("+", "-"):
            return TCon("int")
        if op in ("<", "=="):
            return TCon("bool")
        raise HMTypeError("unknown operator %r" % (op,))

    raise HMTypeError("unknown node %r" % (tag,))


# --- Pretty printing ----------------------------------------------------

def _letter(n):
    if n < 26:
        return chr(ord("a") + n)
    return chr(ord("a") + n % 26) + str(n // 26)


def to_string(t):
    names = {}
    counter = [0]

    def name_of(v):
        if id(v) not in names:
            names[id(v)] = _letter(counter[0])
            counter[0] += 1
        return names[id(v)]

    def rec(t):
        t = prune(t)
        if isinstance(t, TVar):
            return name_of(t)
        if isinstance(t, TCon):
            return t.name
        if isinstance(t, TFun):
            left = rec(t.arg)
            if isinstance(prune(t.arg), TFun):
                left = "(" + left + ")"
            right = rec(t.res)
            return left + " -> " + right
        if isinstance(t, TPair):
            return "(" + rec(t.a) + " * " + rec(t.b) + ")"
        raise HMTypeError("cannot print type")

    return rec(t)


def infer(ast) -> str:
    t = analyze(ast, {})
    return to_string(t)
