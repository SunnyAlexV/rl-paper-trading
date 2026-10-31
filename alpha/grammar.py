"""Formula grammar for alpha discovery, in reverse Polish notation (RPN).

A formula is a token list such as ["close", "ts_mean_20", "close", "div"], meaning
close / mean(close over 20 days)... read as a stack machine. Every formula's output is
cross-sectionally ranked each day, so only its ordering of stocks matters.

Token kinds and arity (number of inputs popped from the stack):
  features (0): open high low close volume vwap ret
  unary    (1): neg abs slog sign, and time-series ops with a window w:
                ts_mean ts_std ts_delta ts_delay ts_rank ts_max ts_min ts_pct
  binary   (2): add sub mul div, and ts_corr with a window
"""
import numpy as np
import bottleneck as bn

FEATURES = ["open", "high", "low", "close", "volume", "vwap", "ret"]
WINDOWS = [5, 10, 20, 40, 60]
UNARY = ["neg", "abs", "slog", "sign"]
TS_UNARY = ["ts_mean", "ts_std", "ts_delta", "ts_delay", "ts_rank", "ts_max", "ts_min", "ts_pct"]
BINARY = ["add", "sub", "mul", "div"]
TS_BINARY = ["ts_corr"]

TOKENS = (FEATURES + UNARY + [f"{o}_{w}" for o in TS_UNARY for w in WINDOWS]
          + BINARY + [f"{o}_{w}" for o in TS_BINARY for w in WINDOWS])


def configure(features):
    """Give a researcher its own input set (the council's researchers see different data)."""
    global FEATURES, TOKENS
    FEATURES = list(features)
    TOKENS = (FEATURES + UNARY + [f"{o}_{w}" for o in TS_UNARY for w in WINDOWS]
              + BINARY + [f"{o}_{w}" for o in TS_BINARY for w in WINDOWS])
    return TOKENS


def arity(tok):
    if tok in FEATURES:
        return 0
    if tok in UNARY or tok.rsplit("_", 1)[0] in TS_UNARY:
        return 1
    return 2


def stack_effect(tok):
    return 1 - arity(tok)


def legal(seq, max_len):
    """Tokens that can extend `seq` and still allow a complete formula within max_len."""
    depth = sum(stack_effect(t) for t in seq)
    remaining = max_len - len(seq)
    out = []
    for t in TOKENS:
        a = arity(t)
        if a > depth:
            continue
        nd = depth + 1 - a
        if nd - 1 > remaining - 1:          # each binary op reduces depth by 1
            continue
        if seq and t == seq[-1] and a == 1 and t in ("neg", "abs", "sign"):
            continue                         # trivial repeats
        out.append(t)
    return out


def is_complete(seq):
    return len(seq) > 0 and sum(stack_effect(t) for t in seq) == 1


def to_str(seq):
    st = []
    for t in seq:
        a = arity(t)
        if a == 0:
            st.append(t)
        elif a == 1:
            x = st.pop(); st.append(f"{t}({x})")
        else:
            y = st.pop(); x = st.pop(); st.append(f"{t}({x}, {y})")
    return st[0] if len(st) == 1 else " ; ".join(st)


# ---------- evaluation on T x N panels (NaN-aware, strictly backward-looking) ----------

def _shift(x, w):
    out = np.full_like(x, np.nan); out[w:] = x[:-w]; return out


def _rolling_corr(x, y, w):
    mp = max(3, w // 2)
    mx, my = bn.move_mean(x, w, mp, axis=0), bn.move_mean(y, w, mp, axis=0)
    mxy = bn.move_mean(x * y, w, mp, axis=0)
    sx, sy = bn.move_std(x, w, mp, axis=0), bn.move_std(y, w, mp, axis=0)
    with np.errstate(all="ignore"):
        return (mxy - mx * my) / (sx * sy)


def apply(tok, args):
    with np.errstate(all="ignore"):
        if tok == "neg": return -args[0]
        if tok == "abs": return np.abs(args[0])
        if tok == "slog": return np.sign(args[0]) * np.log1p(np.abs(args[0]))
        if tok == "sign": return np.sign(args[0])
        if tok == "add": return args[0] + args[1]
        if tok == "sub": return args[0] - args[1]
        if tok == "mul": return args[0] * args[1]
        if tok == "div":
            d = args[1]; return np.where(np.abs(d) > 1e-12, args[0] / d, np.nan)
        op, w = tok.rsplit("_", 1); w = int(w); x = args[0]; mp = max(2, w // 2)
        if op == "ts_mean": return bn.move_mean(x, w, mp, axis=0)
        if op == "ts_std": return bn.move_std(x, w, mp, axis=0)
        if op == "ts_delta": return x - _shift(x, w)
        if op == "ts_delay": return _shift(x, w)
        if op == "ts_rank": return bn.move_rank(x, w, mp, axis=0)
        if op == "ts_max": return bn.move_max(x, w, mp, axis=0)
        if op == "ts_min": return bn.move_min(x, w, mp, axis=0)
        if op == "ts_pct":
            p = _shift(x, w); return np.where(np.abs(p) > 1e-12, x / p - 1, np.nan)
        if op == "ts_corr": return _rolling_corr(x, args[1], w)
    raise ValueError(tok)


def evaluate(seq, feat):
    st = []
    for t in seq:
        a = arity(t)
        if a == 0:
            st.append(feat[t])
        else:
            args = st[-a:]; del st[-a:]
            r = apply(t, args)
            r[~np.isfinite(r)] = np.nan
            st.append(r)
    assert len(st) == 1, "incomplete formula"
    return st[0]
