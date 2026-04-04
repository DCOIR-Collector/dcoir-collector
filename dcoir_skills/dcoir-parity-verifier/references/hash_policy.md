# Hash policy

## Default hash choices
- per-file hash: `sha256`
- tree hash: `sha256` over sorted `path<TAB>sha256` lines
- zip hash: `sha256`

## Why tree hash is primary
Zip hashes can change when packaging metadata changes even if file contents do not.
The normalized tree hash is therefore the primary parity value.

## Exclusions
Ignore runtime residue such as:
- `__pycache__/`
- `*.pyc`
- `.DS_Store`
- empty temporary directories
