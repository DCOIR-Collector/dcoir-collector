# Verification workflow

## Repo-source refresh
1. point the scripts at a governed skills root
2. build or refresh `skill_parity_manifest.json`
3. render `skill_parity_summary.md`
4. package or refresh skill zips if needed
5. record release zip hashes after packaging

## Installed-skill verification
1. hash the installed skill zip when present
2. extract the installed zip or inspect the installed skill tree
3. compare file hashes against the canonical manifest
4. compare the normalized tree hash against the canonical manifest
5. inspect the packaged zip for runtime residue such as `__pycache__/`, `*.pyc`, or equivalent contamination
6. treat zip hash as secondary evidence only and report package cleanliness separately

## README / summary verification
- verify that the summary matches the canonical manifest
- do not treat hand-edited summary markdown as source truth

## Removal workflow
1. remove the governed skill source folder
2. remove the manifest entry
3. regenerate the summary markdown
4. remove the installed skill package
5. verify absence on both sides
