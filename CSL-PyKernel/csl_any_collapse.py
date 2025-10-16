import sys, pathlib, zlib, struct, hashlib, subprocess, os

MAGIC = b'CSLXRAW'
VER   = 1

def cert_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:32]

def shortened_listing(src: bytes, name: str):
    h = cert_hex(src)
    kb = len(src)
    print("=== CSL :: SHORTENED OPERATIONAL CODE ===")
    print("00: INIT mode=ANY")
    print(f"01: OPEN name={name}")
    print(f"02: CANON bytes={kb}")
    print("03: HASH algo=sha256")
    print(f"04: CERT {h}")
    print("05: PACK zlib")
    print("06: EMIT .cslx")
    print("07: HALT")
    print("=== CERT (sha256/32) ===")
    print(h)

def pack_any(in_path: pathlib.Path) -> pathlib.Path:
    raw = in_path.read_bytes()
    name = in_path.name.encode('utf-8')
    payload = MAGIC + struct.pack('>I', VER) + struct.pack('>I', len(name)) + name + zlib.compress(raw, 9)
    out = in_path.with_suffix(in_path.suffix + ".cslx")
    out.write_bytes(payload)
    return out

def unpack_any(pkg_path: pathlib.Path) -> pathlib.Path:
    pkg = pkg_path.read_bytes()
    assert pkg[:7] == MAGIC, "invalid CSLX magic"
    ver  = int.from_bytes(pkg[7:11], 'big')
    nlen = int.from_bytes(pkg[11:15], 'big')
    name = pkg[15:15+nlen].decode('utf-8')
    data = zlib.decompress(pkg[15+nlen:])
    out = pathlib.Path(name)  # restore original filename
    out.write_bytes(data)
    return out

def main():
    if len(sys.argv) < 2:
        print("usage: python csl_any_collapse.py <file> [--run]")
        sys.exit(2)
    path = pathlib.Path(sys.argv[1])
    do_run = ("--run" in sys.argv) and path.suffix == ".py"

    # 1) Shortened listing + cert
    shortened_listing(path.read_bytes(), path.name)

    # 2) Collapse → .cslx
    pkg = pack_any(path)
    print(f"out: {pkg.name}")

    # 3) Expand → original filename
    restored = unpack_any(pkg)
    print(f"expanded: {restored.name}")

    # 4) Optional run for Python sources
    if do_run:
        print("\n=== RUN (python) ===")
        try:
            subprocess.run([sys.executable, str(restored)], check=True)
        except subprocess.CalledProcessError as e:
            print(e)
            sys.exit(e.returncode)

if __name__ == "__main__":
    main()
