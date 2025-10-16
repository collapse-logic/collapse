import sys, pathlib, ast
from csl_kernel.asc7 import canonicalize
from csl_kernel.parser import parse_minimal, PsiDecl, ValDecl, Step, Program
from csl_kernel.compiler import compile_to_ir
from csl_kernel.asm import to_assembly, to_bytes
from mini_cc import ZNode, ZOp, Runtime, add1, double

# ---------- Py → Z (subset: ints, + - * / // % **, parens, vars, calls, multiple assigns) ----------
BINOP_MAP = {
    ast.Add: ZOp.ADD, ast.Mult: ZOp.MUL
}
# Extend mini_cc with synthetic ops via lowering rules:
def _lower_bin(op, L, R):
    # For now: direct for +, * ; emulate -, /, //, %, ** using builtins if present
    if op is ast.Add: return ZNode(ZOp.ADD,[L,R])
    if op is ast.Mult: return ZNode(ZOp.MUL,[L,R])
    # Re-express others via calls to env helpers
    name = {ast.Sub:"sub", ast.Div:"div", ast.FloorDiv:"floordiv", ast.Mod:"mod", ast.Pow:"pow"}[op]
    f = ZNode(ZOp.VAR, [], {"name": name})
    return ZNode(ZOp.APPLY, [ZNode(ZOp.APPLY,[f,L]), R])

def _env():
    import operator, math
    return {
        "add1": add1, "double": double,
        "sub": lambda a: (lambda b: a - b),
        "div": lambda a: (lambda b: a / b),
        "floordiv": lambda a: (lambda b: a // b),
        "mod": lambda a: (lambda b: a % b),
        "pow": lambda a: (lambda b: a ** b),
    }

class PyToZ(ast.NodeVisitor):
    def _name_of(self,t):
        if isinstance(t, ast.Name): return t.id
        raise SyntaxError("only simple names supported in assignment")
    def visit_Module(self,node:ast.Module):
        if not node.body: raise SyntaxError("empty module")
        last = node.body[-1]
        if isinstance(last, ast.Expr):
            z = self.visit(last.value)
        elif isinstance(last, ast.Assign) and len(last.targets)==1:
            nm=self._name_of(last.targets[0]); val=self.visit(last.value)
            z = ZNode(ZOp.LET,[val,ZNode(ZOp.VAR,[],{"name":nm})],{"name":nm})
        else:
            raise SyntaxError("last stmt must be expr or single assignment")
        for st in reversed(node.body[:-1]):
            if isinstance(st, ast.Assign) and len(st.targets)==1:
                nm=self._name_of(st.targets[0]); val=self.visit(st.value)
                z = ZNode(ZOp.LET,[val,z],{"name":nm})
            elif isinstance(st, ast.Expr):
                continue
            else:
                raise SyntaxError("only simple assignments/expressions in this subset")
        return z
    def visit_Expr(self,n): return self.visit(n.value)
    def visit_Constant(self,n):
        if isinstance(n.value,int): return ZNode(ZOp.INT,[],{"value":n.value})
        raise SyntaxError(f"unsupported constant: {n.value!r}")
    def visit_Name(self,n): return ZNode(ZOp.VAR,[],{"name":n.id})
    def visit_BinOp(self,n):
        L,R=self.visit(n.left), self.visit(n.right)
        return _lower_bin(type(n.op), L, R)
    def visit_UnaryOp(self,n):
        import operator
        if isinstance(n.op, ast.USub):
            zero = ZNode(ZOp.INT,[],{"value":0})
            return _lower_bin(ast.Sub, zero, self.visit(n.operand))
        raise SyntaxError("only unary - supported")
    def visit_Call(self,n):
        if not isinstance(n.func, ast.Name): raise SyntaxError("only simple calls")
        f = ZNode(ZOp.VAR,[],{"name":n.func.id})
        out=f
        for a in n.args:
            out = ZNode(ZOp.APPLY,[out,self.visit(a)])
        return out

# ---------- Z → "CSL-like" backend (unified print) ----------
def z_to_csl_backend(z:ZNode):
    psi = PsiDecl(p=3, dim=3)
    val = ValDecl(kind="all_eq", args=(0,0))
    steps = [Step("grad",()), Step("project",()), Step("goal",(0.01,0.99))]
    prog = Program(psi,val,steps)
    bc = compile_to_ir(prog)
    return bc

def print_backend(bc):
    print("=== SHORTENED OPERATIONAL CODE ===")
    print(to_assembly(bc).replace("\\n","\n"))
    print("=== BYTECODE (hex) ===")
    print(to_bytes(bc))

# ---------- CSL path ----------
def run_csl(path:pathlib.Path):
    text = path.read_text(encoding="utf-8")
    canon = canonicalize(text)
    prog  = parse_minimal(canon)
    bc    = compile_to_ir(prog)
    print("=== CSL :: SHORTENED OPERATIONAL CODE ===")
    print(to_assembly(bc).replace("\\n","\n"))
    print("=== BYTECODE (hex) ===")
    print(to_bytes(bc))

# ---------- Python path ----------
def run_py(path:pathlib.Path, emit_backend=True):
    src = path.read_text(encoding="utf-8")
    z = PyToZ().visit(ast.parse(src, filename=str(path)))
    rt = Runtime(_env())
    val = rt.eval(z)
    last_line = next((l for l in reversed(src.strip().splitlines()) if l.strip()), "")
    print("=== PY :: E → Z → 1 ===")
    print("E:", last_line)
    print("Z root:", z.op.name, "collapse_id:", z.collapse_id)
    print("1:", val)
    if emit_backend:
        print_backend(z_to_csl_backend(z))

# ---------- JS path (tiny subset: let x=...; calls; +,*) ----------
def parse_js(src:str):
    # ultra-minimal: tokenize identifiers/ints/+,*, parentheses, commas, 'let', '=', ';'
    import re
    tokens = re.findall(r"[A-Za-z_]\w*|\d+|[+*,()=;]", src)
    i=0
    def peek(): return tokens[i] if i<len(tokens) else ""
    def eat(t=None):
        nonlocal i
        tok = tokens[i] if i<len(tokens) else ""
        if t and tok!=t: raise SyntaxError(f"expected {t}, got {tok}")
        i+=1; return tok
    env_assigns=[]
    def expr():
        def term():
            tok=peek()
            if tok.isdigit(): eat(); return ZNode(ZOp.INT,[],{"value":int(tok)})
            if re.match(r"[A-Za-z_]\w*", tok): # ident or call
                name=eat()
                node=ZNode(ZOp.VAR,[],{"name":name})
                if peek()=="(":
                    eat("(")
                    args=[]
                    if peek()!=")":
                        args.append(expr())
                        while peek()==",":
                            eat(","); args.append(expr())
                    eat(")")
                    for a in args:
                        node=ZNode(ZOp.APPLY,[node,a])
                return node
            if tok=="(":
                eat("("); e=expr(); eat(")"); return e
            raise SyntaxError("bad term")
        node=term()
        while peek() in ["+","*"]:
            op=eat()
            rhs=term()
            node = ZNode(ZOp.ADD,[node,rhs]) if op=="+" else ZNode(ZOp.MUL,[node,rhs])
        return node
    # parse sequence of statements; use last expr as program; assignments become LETs
    nodes=[]
    while i<len(tokens):
        if peek()=="let":
            eat("let")
            name=eat()
            eat("=")
            val=expr()
            if peek()==";": eat(";")
            nodes.append(("assign", name, val))
        else:
            val=expr()
            if peek()==";": eat(";")
            nodes.append(("expr", val))
    # build Z with nested LETs ending in last expr
    if not nodes: raise SyntaxError("empty js")
    last = nodes[-1][1] if nodes[-1][0]=="expr" else ZNode(ZOp.VAR,[],{"name":nodes[-1][1]})
    z = last
    for kind,name,val in reversed([n for n in nodes if n[0]=="assign"]):
        z = ZNode(ZOp.LET,[val,z],{"name":name})
    return z

def run_js(path:pathlib.Path, emit_backend=True):
    src = path.read_text(encoding="utf-8")
    z = parse_js(src)
    rt = Runtime(_env())
    val = rt.eval(z)
    last_line = next((l for l in reversed(src.strip().splitlines()) if l.strip().endswith(";")), "")
    print("=== JS :: E → Z → 1 ===")
    print("E:", last_line)
    print("Z root:", z.op.name, "collapse_id:", z.collapse_id)
    print("1:", val)
    if emit_backend:
        print_backend(z_to_csl_backend(z))

def main():
    if len(sys.argv)<2:
        print("usage: python collapse_run.py <file.csl|file.py|file.js>")
        sys.exit(2)
    path = pathlib.Path(sys.argv[1])
    ext = path.suffix.lower()
    if ext==".csl": run_csl(path)
    elif ext==".py": run_py(path)
    elif ext==".js": run_js(path)
    else:
        print(f"unsupported: {ext}"); sys.exit(2)

if __name__=="__main__": main()
