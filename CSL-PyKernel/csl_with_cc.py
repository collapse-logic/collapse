from csl_kernel.asc7 import canonicalize
from csl_kernel.parser import parse_minimal
from csl_kernel.compiler import compile_to_ir
from csl_kernel.asm import to_assembly, to_bytes

try:
    from mini_cc import compile_to_z, Runtime, add1, double
except Exception:
    compile_to_z = Runtime = add1 = double = None

def run(path: str, expr: str | None = None):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    canon = canonicalize(src)
    prog  = parse_minimal(canon)
    bc    = compile_to_ir(prog)

    print("=== CSL :: SHORTENED OPERATIONAL CODE ===")
    asm = to_assembly(bc)
    print(asm.replace("\\n", "\n"))
    print("=== BYTECODE (hex) ===")
    print(to_bytes(bc))

    if expr and compile_to_z and Runtime and add1 and double:
        z = compile_to_z(expr)
        rt = Runtime({"add1": add1, "double": double})
        val = rt.eval(z)
        print("\n=== E → Z → 1 ===")
        print("E:", expr)
        print("Z root:", z.op.name, "collapse_id:", z.collapse_id)
        print("1:", val)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python csl_with_cc.py <program.csl> [expr]")
        raise SystemExit(2)
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
