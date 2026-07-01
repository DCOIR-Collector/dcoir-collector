## Controlled Cases

- `stale_checked_in_generated_output`: fails when a committed generated harness differs from deterministic assembly (`test_stale_checked_in_generated_output_fails`)
- `missing_source_part`: fails when the collector manifest references a missing source part (`test_missing_source_part_fails`)
- `missing_source_output_mapping`: fails when collector part mapping is absent and generated output cannot be mapped (`test_missing_source_output_mapping_fails`)
- `generated_output_parse_failure`: fails when regenerated runnable output has an unbalanced PowerShell structure (`test_generated_output_parse_failure_fails`)
- `unexpected_inventory_shrink`: fails when source/generated counts shrink below baseline without an exception record (`test_baseline_shrink_without_exception_fails`)
- `clean_control`: passes when source parts, generated outputs, parse status, parity status, and mappings are fresh (`test_clean_control_passes_and_maps_counts and test_real_repo_contract_passes`)

