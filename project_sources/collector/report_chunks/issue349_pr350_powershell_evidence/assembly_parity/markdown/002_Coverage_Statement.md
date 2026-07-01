## Coverage Statement

| Surface | Analyzer wrapper reporting | Custom check reporting | Assembly parity reporting |
| --- | --- | --- | --- |
| `collector runtime source parts` | source-part paths when #262 analyzer targets #261 inventory entries | source-part paths when #264 checks target source-part risk classes | source input map, source hash, generated runtime hash, parse status, and line mapping |
| `collector compiled runtime generated output` | not invoked by this #265 runner; future workflow integration can pass generated output explicitly | not invoked by this #265 runner; parity and parse proof are reported here | generated output hash, parse status, deterministic regeneration status, and source line map |
| `harness source parts and generated harness` | source-part paths when #262 analyzer targets .ps1.txt surfaces; generated output when materialized and explicitly targeted | source-part drift risks through #264 fixtures plus #265 parity proof | ordered source input map, generated harness hash, optional checked-in comparison, parse status, and line map |

