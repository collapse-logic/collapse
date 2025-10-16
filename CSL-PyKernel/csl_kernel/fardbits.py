\
from typing import List, Tuple, Callable

def bitset_new(n: int) -> int: return 0
def bitset_set(bs: int, i: int) -> int: return bs | (1 << i)
def bitset_test(bs: int, i: int) -> bool: return ((bs >> i) & 1) == 1

def indices_from_bitset(bs: int, n: int) -> list[int]:
    return [i for i in range(n) if ((bs >> i) & 1)]

def build_mask(dim: int, p: int, cond: Callable[[tuple[int,...]], bool]) -> int:
    bs = bitset_new(p**dim)
    idx = 0
    coords = [0]*dim
    def rec(d: int):
        nonlocal bs, idx
        if d == dim:
            if cond(tuple(coords)): bs = bitset_set(bs, idx)
            idx += 1
            return
        for v in range(p):
            coords[d] = v
            rec(d+1)
    rec(0)
    return bs
