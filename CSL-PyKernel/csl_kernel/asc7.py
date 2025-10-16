\
_ASC7_MAP = {
    "“":"\"", "”":"\"", "‘":"'", "’":"'", "—":"-", "–":"-",
    "\u00A0":" ", "\t":" ", "\r":" ", "\f":" "
}

def canonicalize(source: str) -> str:
    s = []
    for ch in source:
        ch = _ASC7_MAP.get(ch, ch)
        s.append(ch.lower())
    s = "".join(s)
    lines = []
    for ln in s.split("\n"):
        ln = " ".join(ln.strip().split())
        if ln and not ln.startswith("//"):
            lines.append(ln)
    return "\n".join(lines)
