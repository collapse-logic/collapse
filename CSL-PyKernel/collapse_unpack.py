import sys, pathlib, zlib, struct, json
from mini_cc import ZNode, ZOp, Runtime, add1, double
MAGIC=b'CSLX'
def z_from_dict(d):
    op=getattr(ZOp,d["op"])
    return ZNode(op,[z_from_dict(a) for a in d.get("args",[])], d.get("meta",{}))
def z_to_py(z):
    assigns=[]
    def t(n):
        from mini_cc import ZOp
        if n.op==ZOp.INT: return str(n.meta["value"])
        if n.op==ZOp.VAR: return n.meta["name"]
        if n.op==ZOp.ADD: return f"({t(n.args[0])} + {t(n.args[1])})"
        if n.op==ZOp.MUL: return f"({t(n.args[0])} * {t(n.args[1])})"
        if n.op==ZOp.APPLY: return f"{t(n.args[0])}({t(n.args[1])})"
        if n.op==ZOp.LET:
            name=n.meta["name"]; assigns.append(f"{name} = {t(n.args[0])}"); return t(n.args[1])
        raise NotImplementedError(n.op)
    final=t(z); return assigns, final
def unpack(in_path:pathlib.Path, out:pathlib.Path|None=None, eval_now=False):
    raw=in_path.read_bytes()
    if raw[:4]!=MAGIC: raise ValueError("bad magic")
    ver=struct.unpack(">I", raw[4:8])[0]
    comp=raw[8:]
    canon=zlib.decompress(comp)
    d=json.loads(canon)
    z=z_from_dict(d)
    assigns, final = z_to_py(z)
    text="# expanded by CSL\n" + "\n".join(assigns+[final]) + "\n"
    out = out or in_path.with_suffix(".py")
    out.write_text(text, encoding="utf-8")
    print("unpacked:", out)
    if eval_now:
        val=Runtime({"add1":add1,"double":double,
                     "sub":lambda a:(lambda b:a-b),
                     "div":lambda a:(lambda b:a/b),
                     "floordiv":lambda a:(lambda b:a//b),
                     "mod":lambda a:(lambda b:a%b),
                     "pow":lambda a:(lambda b:a**b)}).eval(z)
        print("run:", val)
if __name__=="__main__":
    if len(sys.argv)<2:
        print("usage: python collapse_unpack.py <file.cslx> [--eval]")
        sys.exit(2)
    unpack(pathlib.Path(sys.argv[1]), None, "--eval" in sys.argv)
