\
import sys
from pathlib import Path
from .asc7 import canonicalize
from .parser import parse_minimal
from .compiler import compile_to_ir
from .asm import to_assembly, to_bytes

def main():
    if len(sys.argv)<2:
        print("usage: csl <program.csl> [--preview]")
        raise SystemExit(2)
    src = Path(sys.argv[1]).read_text(encoding='utf-8')
    canon = canonicalize(src)
    prog  = parse_minimal(canon)
    bc    = compile_to_ir(prog)
    print("=== CSL :: SHORTENED OPERATIONAL CODE ===")
    print(to_assembly(bc))
    print("=== BYTECODE (hex) ===")
    print(to_bytes(bc))

    if "--preview" in sys.argv:
        try:
            import numpy as np  # optional
        except Exception:
            print("[preview] NumPy not installed. Install with: pip install .[preview]")
            return
        # Minimal preview: compute one H,γ from a random seed (matches spec expectations)
        from .fardbits import bitset_test
        import numpy as _np
        # seed
        p,dim = prog.psi.p, prog.psi.dim
        n = p**dim
        v = _np.random.rand(n).astype(float)
        v /= (_np.linalg.norm(v) + 1e-12)
        # gamma
        vmask = bc[3].i  # from VMASK
        g=0.0
        for i in range(n):
            if bitset_test(vmask, i):
                g += v[i]*v[i]
        probs = v*v
        import math
        H = float(-(probs * _np.log2(probs + 1e-300)).sum())
        print(f"[preview] step 0: H={H:.4f} gamma={g:.4f}")
