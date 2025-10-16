\
from dataclasses import dataclass

OP_INIT    = 1
OP_SEED    = 2
OP_VMASK   = 3
OP_GRAD    = 4
OP_PROJ    = 5
OP_METRICS = 6
OP_HALT    = 7

@dataclass
class Instr:
    op:int; a:float=0.0; b:float=0.0; c:float=0.0; i:int=0
