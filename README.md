# CSL-Core

The **Collapse System Logic (CSL)** core repository.  
This repo contains the operational Python kernel, certified `.csl` logic modules, and the proof system scaffolding used for CSL compression/expansion.

## Core Directories
- `CSL-PyKernel/` — Python kernel and proof driver.
- `.csl` files — minimal logic primitives (e.g., `mini_or.csl`, `mini_neq.csl`).
- `mathematical_proof_system.py` — primary proof orchestrator.

## Usage

### Proof Compression Flow

Each collapse in the CSL pipeline follows the canonical tri-map:
| Stage | Operation | Description |
|--------|------------|--------------|
| **E** | Expansion | Source code or proof text in its full expressive state. |
| **Z** | Zipped Canonical Form | Structured compression into `.cslx` (CSL-exchange) format via entropy-minimizing transformation. |
| **1** | Terminal Collapse | Final certification: a single hash (SHA256/32) validating proof integrity and terminal identity. |

### Typical Commands
### Notes
- Every `.cslx` file is verifiable and self-consistent.
- Collapse certificates are deterministic across systems.
- CSL aims for **entropy → zero** under valid proof collapse.

python -m py_compile mathematical_proof_system.py
python csl_any_collapse.py mathematical_proof_system.py --info
python csl_any_collapse.py mathematical_proof_system.py --pack
python csl_any_collapse.py mathematical_proof_system.py.cslx --unpack
/usr/bin/time -l python -u mathematical_proof_system.py

## CSL Kernel Architecture

The CSL system implements the canonical collapse triad:
### Implementation Mapping
| Symbol | Module / File | Functionality |
|---------|----------------|----------------|
| **Φ** | `CSL-PyKernel/csl_any_collapse.py` | Performs entropy-reducing collapse via zlib and canonical hashing. |
| **T** | `mathematical_proof_system.py` | Transforms proofs from expressive to canonical form (`E → Z`). |
| **Ψ** | `.csl` certified modules | Final verification and terminal identity (`Z → 1`). |

### Operational Flow
1. **Compile** — Validate syntax and structure (`E` form).  
2. **Pack** — Collapse to `.cslx` canonical (`Z` form).  
3. **Unpack** — Expand back for verification.  
4. **Execute** — Run the proof orchestrator; log results and emit terminal hash.  

Each phase is deterministic: no randomness, no recursion drift, and total entropy collapse to 0 under valid proofs.


## Verification and Certification

Every `.cslx` file produced by the kernel carries a **collapse certificate**:
This certificate encodes the **terminal state** of the proof:
- **Canonical Hash (CERT)** → irreversible identity of the proof content.
- **Zlib Compression (PACK)** → verified entropy reduction.
- **Re-expandable (UNPACK)** → structural integrity preserved through collapse.

Double-collapsing (e.g., `.cslx → .cslx.cslx`) yields identical hashes under valid CSL alignment, confirming deterministic closure.

---

### Validation Rule
A valid proof satisfies:
\[
\Phi^2 = 0,\quad T^2 = T,\quad \Psi^2 = \Psi,\quad \Psi \circ T = 1
\]

where entropy strictly decreases under Φ.  
This is the mathematical guarantee of **Collapse Logic Integrity**.

Thu Oct 16 14:51:10 CEST 2025
