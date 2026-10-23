"""An LSL interpreter for the Take 12 scripts (7.1.3): runs the real .lsl files, not ports of them.

The scripts are parsed by LSL-PyOptimizer (the same one tools/lslcheck.sh fetches) and its lslbasefuncs gives the
pure built-ins and the operators with LSL's own semantics (32-bit integers, float32 maths, casts, list quirks, an
unset key being "" and not NULL_KEY). This file walks the syntax tree; the world-facing calls (chat, link messages,
timers, controls, the camera, permissions, Linkset Data, prims) are answered by tools/emu/world.py through
Script.world.

    from lsl_emu import compile_file
    prog = compile_file("hud/src/sync.lsl")           # parsed once, shared by every HUD that runs it
"""
import os, sys, math

OPT = os.environ.get("LSLOPT_DIR", os.path.expanduser("~/.cache/lsl-pyoptimizer"))
if not os.path.exists(os.path.join(OPT, "main.py")):
    raise SystemExit("LSL-PyOptimizer not found in %s (tools/lslcheck.sh fetches it)" % OPT)
sys.path.insert(0, OPT)
_cwd = os.getcwd()
os.chdir(OPT)                                           # its modules read data files relative to the cwd
try:
    from lslopt.lslparse import parser
    import lslopt.lslloadlib as _loadlib
    from lslopt import lslbasefuncs as B
    from lslopt.lslcommon import Key, Vector, Quaternion
    LIB = _loadlib.LoadLibrary(os.path.join(OPT, "builtins.txt"), os.path.join(OPT, "fndata.txt"))
finally:
    os.chdir(_cwd)

CONST = LIB[1]
FUNCS = LIB[2]
TYPES = {"integer": int, "float": float, "string": str, "key": Key, "vector": Vector, "rotation": Quaternion, "list": list}
DEFAULTS = {"integer": 0, "float": 0.0, "string": "", "key": Key(""), "vector": Vector((0.0, 0.0, 0.0)),
            "rotation": Quaternion((0.0, 0.0, 0.0, 1.0)), "list": []}
F = lambda x: B.F32(float(x))


class LSLError(Exception):
    """a run-time error the real server would also stop on (math error, a bad cast)"""


class _Return(Exception):
    def __init__(s, v): s.v = v


class _State(Exception):
    def __init__(s, name): s.name = name


def coerce(v, t):
    """the implicit conversions LSL makes on assignment, arguments and return: int to float, string to key and back"""
    if t is None or v is None: return v
    if t == "float" and type(v) == int: return F(v)
    if t == "key" and type(v) == str: return Key(v)
    if t == "string" and type(v) == Key: return str(v)
    if t == "list" and type(v) != list: return [v]
    return v


class Program:
    """one parsed script: its globals, functions and the events of each state"""
    def __init__(s, path):
        s.path, s.name = path, os.path.splitext(os.path.basename(path))[0]
        src = open(path, encoding="utf-8").read()
        p = parser(LIB)
        os.chdir(OPT)
        try:
            tree, s.symtab = p.parse(src, ())
        finally:
            os.chdir(_cwd)
        s.globals, s.funcs, s.states = [], {}, {}
        for n in tree:
            if n.nt == "DECL": s.globals.append(n)
            elif n.nt == "FNDEF": s.funcs[n.name] = n
            elif n.nt == "STDEF": s.states[n.name] = {e.name: e for e in n.ch}

_CACHE = {}
def compile_file(path):
    path = os.path.abspath(path)
    if path not in _CACHE: _CACHE[path] = Program(path)
    return _CACHE[path]


class Script:
    """a running instance of a Program inside one object; world is the object's host (world.Obj)"""
    STEP_LIMIT = 200000                                   # a runaway loop is a bug, not a hang

    def __init__(s, prog, world):
        s.prog, s.world, s.name = prog, world, prog.name
        s.reset_vars()

    def reset_vars(s):
        s.g = {}
        s.state = "default"
        s.detected = []
        for d in s.prog.globals:
            s.g[d.name] = coerce(s.eval(d.ch[0], None), d.t) if d.ch else _copy(DEFAULTS[d.t])

    def has(s, event): return event in s.prog.states[s.state]

    def run(s, event, args=(), detected=None):
        """runs one event to its end (LSL never interrupts an event); returns a new state's name or None"""
        h = s.prog.states[s.state].get(event)
        if h is None: return None
        s.detected = detected or []
        s.steps = 0
        frame = {}
        for nm, t, v in zip(h.pnames, h.ptypes, args): frame[(h.pscope, nm)] = coerce(v, t)
        try:
            s.block(h.ch[0], frame)
        except _Return:
            pass
        except _State as e:
            return e.name
        return None

    # ---- statements -----------------------------------------------------------------------------------------------
    def block(s, n, fr):
        nt = n.nt
        if nt == "{}":
            for c in n.ch: s.block(c, fr)
        elif nt == "EXPR": s.eval(n.ch[0], fr)
        elif nt == "DECL": fr[(n.scope, n.name)] = coerce(s.eval(n.ch[0], fr), n.t) if n.ch else _copy(DEFAULTS[n.t])
        elif nt == "IF":
            if B.cond(s.eval(n.ch[0], fr)): s.block(n.ch[1], fr)
            elif len(n.ch) > 2: s.block(n.ch[2], fr)
        elif nt == "FOR":
            for e in n.ch[0].ch: s.eval(e, fr)
            while B.cond(s.eval(n.ch[1], fr)):
                s.tick()
                s.block(n.ch[3], fr)
                for e in n.ch[2].ch: s.eval(e, fr)
        elif nt == "WHILE":
            while B.cond(s.eval(n.ch[0], fr)):
                s.tick()
                s.block(n.ch[1], fr)
        elif nt == "DO":
            while True:
                s.tick()
                s.block(n.ch[0], fr)
                if not B.cond(s.eval(n.ch[1], fr)): break
        elif nt == "RETURN": raise _Return(s.eval(n.ch[0], fr) if n.ch else None)
        elif nt == "STSW": raise _State(n.name)
        elif nt == ";": pass
        else: raise NotImplementedError("statement " + nt)

    def tick(s):
        s.steps += 1
        if s.steps > s.STEP_LIMIT: raise LSLError("%s: a loop ran %d times" % (s.name, s.STEP_LIMIT))

    # ---- expressions ----------------------------------------------------------------------------------------------
    def eval(s, n, fr):
        nt = n.nt
        if nt == "CONST": return _copy(n.value) if type(n.value) != str or n.t != "key" else Key(n.value)
        if nt == "IDENT": return s.get(n, fr)
        if nt == "FNCALL": return s.call(n, fr)
        if nt == "=": return s.set(n.ch[0], coerce(s.eval(n.ch[1], fr), n.ch[0].t), fr)
        if nt in ("+=", "-=", "*=", "/=", "%="):
            r = s.eval(n.ch[1], fr)
            v = _OPS[nt[0]](s.eval(n.ch[0], fr), r)
            return s.set(n.ch[0], coerce(v, n.ch[0].t), fr)
        if nt in ("V++", "V--", "++V", "--V"):
            old = s.eval(n.ch[0], fr)
            new = B.add(old, 1) if "+" in nt else B.sub(old, 1)
            s.set(n.ch[0], coerce(new, n.ch[0].t), fr)
            return old if nt[0] == "V" else new
        if nt == "CAST": return _cast(s.eval(n.ch[0], fr), n.t)
        if nt == "LIST": return [s.eval(c, fr) for c in n.ch]
        if nt == "VECTOR": return Vector(tuple(F(_num(s.eval(c, fr))) for c in n.ch))
        if nt == "ROTATION": return Quaternion(tuple(F(_num(s.eval(c, fr))) for c in n.ch))
        if nt == "FLD":
            v = s.eval(n.ch[0], fr)
            return v["xyzs".index(n.fld)]
        if nt == "NEG": return B.neg(s.eval(n.ch[0], fr))
        if nt == "!": return int(not B.cond(s.eval(n.ch[0], fr)))
        if nt == "~": return B.S32(~s.eval(n.ch[0], fr))
        if nt == "()": return s.eval(n.ch[0], fr)
        if nt in _OPS or nt in _CMP or nt in ("&&", "||"):
            b = s.eval(n.ch[1], fr)                     # Mono evaluates the right operand first
            a = s.eval(n.ch[0], fr)
            if nt == "&&": return int(B.cond(a) and B.cond(b))
            if nt == "||": return int(B.cond(a) or B.cond(b))
            if nt in _CMP: return _CMP[nt](a, b)
            try:
                return _OPS[nt](a, b)
            except B.ELSLMathError:
                raise LSLError("%s: Math Error" % s.name)
        raise NotImplementedError("expression " + nt)

    def get(s, n, fr):
        if fr is not None and (n.scope, n.name) in fr: return fr[(n.scope, n.name)]
        return s.g[n.name]

    def set(s, target, v, fr):
        if target.nt == "FLD":
            cur = list(s.eval(target.ch[0], fr))
            cur["xyzs".index(target.fld)] = F(_num(v))
            s.set(target.ch[0], type(s.eval(target.ch[0], fr))(tuple(cur)), fr)
            return v
        if fr is not None and (target.scope, target.name) in fr: fr[(target.scope, target.name)] = v
        else: s.g[target.name] = v
        return v

    def call(s, n, fr):
        args = [s.eval(c, fr) for c in n.ch]
        f = s.prog.funcs.get(n.name)
        if f is not None:
            frame = {}
            for nm, t, v in zip(f.pnames, f.ptypes, args): frame[(f.pscope, nm)] = coerce(v, t)
            try:
                s.block(f.ch[0], frame)
            except _Return as r:
                return coerce(r.v, f.t)
            return DEFAULTS[f.t] if f.t else None
        spec = FUNCS.get(n.name, {})
        args = [coerce(a, t) for a, t in zip(args, spec.get("ParamTypes", []))]
        w = getattr(s.world, n.name, None)
        if w is not None: return coerce(w(s, *args), spec.get("Type"))
        fn = spec.get("Fn")
        if fn is None: raise NotImplementedError("%s: %s is not emulated" % (s.name, n.name))
        try:
            return coerce(fn(*args), spec.get("Type"))
        except B.ELSLMathError:
            raise LSLError("%s: Math Error in %s" % (s.name, n.name))


def _copy(v): return list(v) if type(v) == list else v
def _num(v): return float(v) if type(v) in (int, float) else 0.0
def _cast(v, t):
    try:
        return B.typecast(v, TYPES[t])
    except Exception as e:
        raise LSLError("bad cast of %r to %s (%s)" % (v, t, e))

_OPS = {"+": B.add, "-": B.sub, "*": B.mul, "/": B.div, "%": B.mod,
        "&": lambda a, b: B.S32(a & b), "|": lambda a, b: B.S32(a | b), "^": lambda a, b: B.S32(a ^ b),
        "<<": lambda a, b: B.S32(a << (b & 31)), ">>": lambda a, b: B.S32(a >> (b & 31))}
_CMP = {"==": lambda a, b: B.compare(a, b, True), "!=": lambda a, b: B.compare(a, b, False),
        "<": B.less, ">": lambda a, b: B.less(b, a), "<=": lambda a, b: 1 - B.less(b, a), ">=": lambda a, b: 1 - B.less(a, b)}
