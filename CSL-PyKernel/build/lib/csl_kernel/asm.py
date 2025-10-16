\
from .ir import *

def to_assembly(bc):
    out=[]
    for k,ins in enumerate(bc):
        if ins.op==OP_INIT and ins.i>0:
            out.append(f"{k:02d}: INIT p={ins.i}")
        elif ins.op==OP_INIT and ins.b>0:
            out.append(f"{k:02d}: INIT dim={int(ins.b)}")
        elif ins.op==OP_VMASK:
            hexmask = hex(ins.i)
            out.append(f"{k:02d}: VMASK nbits={ins.i.bit_length()} hex={hexmask[:18]}...")
        elif ins.op==OP_GRAD:
            out.append(f"{k:02d}: GRAD eta={ins.c}")
        else:
            name = {OP_SEED:'SEED',OP_PROJ:'PROJ',OP_METRICS:'METRICS',OP_HALT:'HALT'}.get(ins.op,'OP')
            out.append(f"{k:02d}: {name}")
    return "\\n".join(out)

def to_bytes(bc):
    import struct, binascii
    chunks=[]
    for ins in bc:
        blob = struct.pack('<BfffQ', ins.op, float(ins.a), float(ins.b), float(ins.c), int(ins.i) & ((1<<64)-1))
        chunks.append(binascii.hexlify(blob).decode())
    return "".join(chunks)
