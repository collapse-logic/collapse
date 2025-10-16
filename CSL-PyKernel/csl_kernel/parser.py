from dataclasses import dataclass
import re

@dataclass
class PsiDecl: p:int; dim:int
@dataclass
class ValDecl: kind:str; args:tuple
@dataclass
class Step: op:str; args:tuple=()
@dataclass
class Program: psi:PsiDecl; val:ValDecl; steps:list

_val_re = re.compile(r"x\s*(\d+)\s*=\s*(-?\d+)")

def parse_minimal(canon_text: str) -> Program:
    lines = [ln for ln in canon_text.split("\n") if ln]
    if len(lines) < 2:
        raise ValueError("program too short")

    # line 1: ψ :: f<p>^<dim>
    L1 = lines[0].split()
    if "::" not in L1:
        raise ValueError("line 1 must contain '::'")
    layout = L1[-1]  # e.g., f3^3 or f11^4
    if not layout.startswith("f"):
        raise ValueError("expecting f<p>^<dim> in line 1")
    after_f = layout[1:]
    if "^" not in after_f:
        raise ValueError(f"expecting caret (^) in field spec, got '{layout}'")
    p_str, dim_str = after_f.split("^", 1)
    p = int(p_str); dim = int(dim_str)
    psi = PsiDecl(p, dim)

    # line 2: v :: { x in f... : xk = c }
    L2 = lines[1]
    if ":" not in L2 or "}" not in L2:
        raise ValueError("line 2 must define validator like '{ x in f3^3 : x1 = 0 }'")
    constraint_region = L2.split(":", 1)[1].rsplit("}", 1)[0]
    m = _val_re.search(constraint_region)
    if not m:
        raise ValueError("could not parse validator; expected pattern like 'x1 = 0'")
    axis_idx = int(m.group(1)) - 1
    cval = int(m.group(2))
    val = ValDecl("x_eq_const", (axis_idx, cval))

    steps = []
    for ln in lines[2:]:
        l = ln.lower()
        if "∇l" in l or "grad" in l:
            steps.append(Step("grad", ()))
        elif "p_v" in l:
            steps.append(Step("project", ()))
        elif "⊢" in l or "vdash" in l:
            steps.append(Step("goal", (0.01, 0.99)))
    return Program(psi, val, steps)
