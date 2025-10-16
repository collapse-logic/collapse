from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from hashlib import sha256
import json
from typing import Any, Dict, List, Optional, Tuple

def _canon(x: Any) -> bytes:
    if hasattr(x, "to_canon"): return x.to_canon()
    if isinstance(x, (bytes, bytearray)): return bytes(x)
    return json.dumps(x, sort_keys=True, separators=(",", ":")).encode()

def collapse_hash(*parts: Any) -> str:
    h = sha256()
    for p in parts: h.update(_canon(p))
    return h.hexdigest()[:16]

class TokenType(Enum):
    INT=auto(); IDENT=auto(); PLUS=auto(); STAR=auto()
    LPAREN=auto(); RPAREN=auto(); LET=auto(); IN=auto()
    ARROW=auto(); COMMA=auto(); EOF=auto()

@dataclass
class Token:
    type: TokenType
    value: Any=None

class Tokenizer:
    def tokenize(self, s: str) -> List[Token]:
        i,n,ts=0,len(s),[]
        def pk(k=0): j=i+k; return s[j] if j<n else ""
        while i<n:
            c=s[i]
            if c.isspace(): i+=1; continue
            if c.isdigit():
                j=i
                while j<n and s[j].isdigit(): j+=1
                ts.append(Token(TokenType.INT,int(s[i:j]))); i=j; continue
            if c.isalpha() or c=="_":
                j=i
                while j<n and (s[j].isalnum() or s[j]=="_"): j+=1
                w=s[i:j]
                if w=="let": ts.append(Token(TokenType.LET))
                elif w=="in": ts.append(Token(TokenType.IN))
                else: ts.append(Token(TokenType.IDENT,w))
                i=j; continue
            if c=="-" and pk(1)==">": ts.append(Token(TokenType.ARROW)); i+=2; continue
            m={"+":TokenType.PLUS,"*":TokenType.STAR,"(":TokenType.LPAREN,")":TokenType.RPAREN,",":TokenType.COMMA}
            if c in m: ts.append(Token(m[c])); i+=1; continue
            raise SyntaxError(f"Unexpected {c}")
        ts.append(Token(TokenType.EOF)); return ts

class ZOp(Enum): INT=auto(); VAR=auto(); ADD=auto(); MUL=auto(); APPLY=auto(); LET=auto()

@dataclass
class ZNode:
    op: ZOp
    args: List["ZNode"]=field(default_factory=list)
    meta: Dict[str,Any]=field(default_factory=dict)
    collapse_id: str=field(init=False)
    def __post_init__(self):
        arg_json = [json.loads(a.to_canon()) for a in self.args]
        self.collapse_id = collapse_hash({"op":self.op.name,"meta":self.meta,"args":arg_json})
    def to_canon(self)->bytes:
        return _canon({"op":self.op.name,"args":[json.loads(a.to_canon()) for a in self.args],"meta":self.meta})

class Parser:
    def __init__(self,ts:List[Token]): self.ts=ts; self.i=0
    def cur(self): return self.ts[self.i]
    def adv(self):
        if self.i < len(self.ts)-1: self.i+=1
    def expect(self,t):
        tok=self.cur()
        if tok.type!=t: raise SyntaxError(f"Expected {t.name}, got {tok.type.name}")
        self.adv(); return tok
    def parse(self)->"ZNode":
        node=self.expr(); self.expect(TokenType.EOF); return node
    def expr(self)->"ZNode":
        if self.cur().type==TokenType.LET:
            self.adv()
            name=self.expect(TokenType.IDENT).value
            self.expect(TokenType.ARROW)
            val=self.expr()
            self.expect(TokenType.IN)
            body=self.expr()
            return ZNode(ZOp.LET,[val,body],{"name":name})
        return self.add()
    def add(self)->"ZNode":
        left=self.mul()
        while self.cur().type==TokenType.PLUS:
            self.adv(); right=self.mul()
            left=ZNode(ZOp.ADD,[left,right])
        return left
    def mul(self)->"ZNode":
        left=self.app()
        while self.cur().type==TokenType.STAR:
            self.adv(); right=self.app()
            left=ZNode(ZOp.MUL,[left,right])
        return left
    def app(self)->"ZNode":
        f=self.prim()
        if self.cur().type==TokenType.LPAREN:
            self.adv(); args=[]
            if self.cur().type!=TokenType.RPAREN:
                args.append(self.expr())
                while self.cur().type==TokenType.COMMA:
                    self.adv(); args.append(self.expr())
            self.expect(TokenType.RPAREN)
            for a in args: f=ZNode(ZOp.APPLY,[f,a])
        return f
    def prim(self)->"ZNode":
        t=self.cur()
        if t.type==TokenType.INT: self.adv(); return ZNode(ZOp.INT,[],{"value":t.value})
        if t.type==TokenType.IDENT: self.adv(); return ZNode(ZOp.VAR,[],{"name":t.value})
        if t.type==TokenType.LPAREN:
            self.adv(); e=self.expr(); self.expect(TokenType.RPAREN); return e
        raise SyntaxError(f"Unexpected token: {t.type.name}")

class Runtime:
    def __init__(self, env: Optional[Dict[str, Any]] = None): self.env=env or {}
    def eval(self, n: ZNode)->Any:
        if n.op==ZOp.INT: return n.meta["value"]
        if n.op==ZOp.VAR:
            name=n.meta["name"]
            if name not in self.env: raise NameError(f"Variable '{name}' not found")
            return self.env[name]
        if n.op==ZOp.ADD: return self.eval(n.args[0])+self.eval(n.args[1])
        if n.op==ZOp.MUL: return self.eval(n.args[0])*self.eval(n.args[1])
        if n.op==ZOp.APPLY:
            f=self.eval(n.args[0]); a=self.eval(n.args[1]); return f(a)
        if n.op==ZOp.LET:
            name=n.meta["name"]; val=self.eval(n.args[0]); old=self.env.get(name); self.env[name]=val
            try: return self.eval(n.args[1])
            finally:
                if old is None: del self.env[name]
                else: self.env[name]=old
        raise NotImplementedError(n.op)

def add1(x:int)->int: return x+1
def double(x:int)->int: return x*2

def compile_to_z(source:str)->ZNode:
    toks=Tokenizer().tokenize(source); return Parser(toks).parse()

def run(source:str, env:Optional[Dict[str,Any]]=None)->Tuple[Any,"ZNode"]:
    z=compile_to_z(source); val=Runtime(env or {"add1":add1,"double":double}).eval(z); return val,z
