from csl_kernel.asc7 import canonicalize
from csl_kernel.parser import parse_minimal
from csl_kernel.compiler import compile_to_ir
from csl_kernel.asm import to_assembly, to_bytes
from mini_cc import compile_to_z, Runtime

def run_csl(path: str):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    canon = canonicalize(src)
    prog  = parse_minimal(canon)
    bc    = compile_to_ir(prog)

    print("=== CSL :: SHORTENED OPERATIONAL CODE ===")
    print(to_assembly(bc))
    print("=== BYTECODE (hex) ===")
    print(to_bytes(bc))

    # bonus: E → Z → 1 demo using mini_cc
    expr = "double(add1(9))"
    z = compile_to_z(expr)
    val = Runtime().eval(z)
    print("\n=== E → Z → 1 demo ===")
    print("E:", expr)
    print("Z root:", z.op.name, "collapse_id:", z.collapse_id)
    print("1:", val)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python csl_native.py <program.csl>")
        raise SystemExit(2)
    run_csl(sys.argv[1])
