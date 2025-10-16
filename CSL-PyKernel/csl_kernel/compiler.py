\
from .parser import Program
from .ir import *
from .fardbits import build_mask

def compile_to_ir(prog: Program):
    bc=[]
    p,dim = prog.psi.p, prog.psi.dim
    bc.append(Instr(OP_INIT, i=p))
    bc.append(Instr(OP_INIT, b=dim))
    bc.append(Instr(OP_SEED))
    # validator (Phase-1: x_axis == const)
    axis, cval = prog.val.args
    vmask = build_mask(dim, p, lambda x: x[axis]==cval)
    bc.append(Instr(OP_VMASK, i=vmask))
    for st in prog.steps:
        if st.op=="grad":    bc.append(Instr(OP_GRAD, a=1.0, b=1.0, c=0.1))
        elif st.op=="project": bc.append(Instr(OP_PROJ))
        elif st.op=="goal":
            bc.append(Instr(OP_METRICS)); bc.append(Instr(OP_HALT))
    return bc
