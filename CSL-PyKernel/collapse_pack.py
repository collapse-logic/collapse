import sys, pathlib, ast, zlib, struct
from mini_cc import ZNode, ZOp, Runtime, add1, double
MAGIC=b'CSLX'; VER=1
class PyToZ(ast.NodeVisitor):
    def _name_of(self,t):
        import ast
        if isinstance(t, ast.Name): return t.id
        raise SyntaxError("only simple names supported in assignment")
    def visit_Module(self,node):
        import ast
        if not node.body: raise SyntaxError("empty module")
        last=node.body[-1]
        if isinstance(last, ast.Expr):
            z=self.visit(last.value)
        elif isinstance(last, ast.Assign) and len(last.targets)==1:
            nm=self._name_of(last.targets[0]); val=self.visit(last.value)
            z=ZNode(ZOp.LET,[val,ZNode(ZOp.VAR,[],{"name":nm})],{"name":nm})
        else:
            raise SyntaxError("last stmt must be expr or single assignment")
        for st in reversed(node.body[:-1]):
            if isinstance(st, ast.Assign) and len(st.targets)==1:
                nm=self._name_of(st.targets[0]); val=self.visit(st.value)
                z=ZNode(ZOp.LET,[val,z],{"name":nm})
        return z
    def visit_Constant(self,n):
        if isinstance(n.value,int): return ZNode(ZOp.INT,[],{"value":n.value})
        raise SyntaxError("const")
    def visit_Name(self,n): return ZNode(ZOp.VAR,[],{"name":n.id})
    def visit_BinOp(self,n):
        import ast
        L,R=self.visit(n.left), self.visit(n.right)
        if isinstance(n.op, ast.Add): return ZNode(ZOp.ADD,[L,R])
        if isinstance(n.op, ast.Mult): return ZNode(ZOp.MUL,[L,R])
        name={ast.Sub:"sub", ast.Div:"div", ast.FloorDiv:"floordiv", ast.Mod:"mod", ast.Pow:"pow"}[type(n.op)]
        f=ZNode(ZOp.VAR,[],{"name":name})
        return ZNode(ZOp.APPLY,[ZNode(ZOp.APPLY,[f,L]),R])
    def visit_Call(self,n):
        if not hasattr(n.func,"id"): raise SyntaxError("call")
        f=ZNode(ZOp.VAR,[],{"name":n.func.id}); out=f
        for a in n.args: out=ZNode(ZOp.APPLY,[out,self.visit(a)])
        return out

def pack_py(src: pathlib.Path, out: pathlib.Path|None=None):
    text=src.read_text(encoding="utf-8")
    z=PyToZ().visit(ast.parse(text, filename=str(src)))
    canon=z.to_canon()
    comp=zlib.compress(canon,9)
    payload = MAGIC + struct.pack(">I",VER) + comp
    out = out or src.with_suffix(".cslx")
    out.write_bytes(payload)
    print("packed:", out, "sizes:", len(text),"→",len(canon),"→",len(payload))

if __name__=="__main__":
    if len(sys.argv)<2:
        print("usage: python collapse_pack.py <file.py>")
        sys.exit(2)
    pack_py(pathlib.Path(sys.argv[1]))
