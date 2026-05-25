# Knowledge - Reference - OSQuery Reference Index

_Governed routing index for the sharded OSQuery schema reference set_

**Summary:** Use this page to decide which OSQuery reference shard to consult first. The detailed shard pages preserve the exact table, field, type, and description content from the approved OSQuery source markdown.

---

## Core rules

- Return raw SQL only when planning `osquery` queries.
- Do not wrap OSQuery queries in CLI syntax.
- Do not invent table names or field names.
- Use the shard pages as the governed exact-name reference when current evidence does not already provide the correct table or field.

---

## Where to start

| Investigative need | Start with | Typical examples |
| --- | --- | --- |
| Current process state, process lineage, handles, PowerShell, execution artifacts | `Knowledge - Reference - OSQuery Process and Execution Tables` | `processes`, `process_open_sockets`, `powershell_events` |
| Files, hashes, filesystem locations, mounts, partitions, file-linked events | `Knowledge - Reference - OSQuery File and Filesystem Tables` | `file`, `hash`, `mounts`, `process_file_events` |
| Ports, DNS, interfaces, routes, sockets, connectivity, Wi-Fi | `Knowledge - Reference - OSQuery Network and Connection Tables` | `listening_ports`, `dns_cache`, `interface_details` |
| Users, logons, SSH keys, auth policy, groups, and account context | `Knowledge - Reference - OSQuery User, Auth, and Account Tables` | `users`, `logged_in_users`, `user_ssh_keys` |
| Persistence, startup, services, scheduled tasks, WMI consumers, and shims | `Knowledge - Reference - OSQuery Persistence and Startup Tables` | `scheduled_tasks`, `services`, `wmi_event_filters` |
| System, OS, hardware, memory, uptime, USB, and platform details | `Knowledge - Reference - OSQuery System, Hardware, and Platform Tables` | `system_info`, `os_version`, `usb_devices` |
| Security telemetry, event tables, firewall, YARA, Gatekeeper, and AppArmor | `Knowledge - Reference - OSQuery Security, Detection, and Event Tables` | `windows_eventlog`, `yara_process`, `apparmor_events` |
| Installed apps, packages, browser extensions, and program inventory | `Knowledge - Reference - OSQuery Application, Package, and Extension Tables` | `programs`, `deb_packages`, `chrome_extensions` |
| Containers, LXD, Docker, cloud metadata, and OSQuery self-state | `Knowledge - Reference - OSQuery Virtualization, Cloud, and Container Tables` | `docker_containers`, `ec2_instance_metadata`, `osquery_info` |

---

## Shard inventory
- `Knowledge - Reference - OSQuery Process and Execution Tables`: `bpf_process_events`, `bpf_socket_events`, `carves`, `es_process_events`, `es_process_file_events`, `powershell_events`, `prefetch`, `process_envs`, `process_etw_events`, `process_events`, `process_file_events`, `process_memory_map`, `process_namespaces`, `process_open_files`, `process_open_handles`, `process_open_pipes`, `process_open_sockets`, `processes`, `user_events`, `user_interaction_events`, `winbaseobj`
- `Knowledge - Reference - OSQuery File and Filesystem Tables`: `block_devices`, `deb_package_files`, `device_file`, `device_hash`, `device_partitions`, `deviceguard_status`, `disk_events`, `disk_info`, `extended_attributes`, `file`, `hash`, `magic`, `md_devices`, `md_drives`, `md_personalities`, `mdfind`, `mdls`, `mounts`, `nfs_shares`, `ntfs_acl_permissions`, `ntfs_journal_events`, `package_bom`, `package_install_history`, `plist`, `quicklook_cache`, `recent_files`, `rpm_package_files`, `shared_memory`, `shared_resources`, `smbios_tables`, `yara_file`
- `Knowledge - Reference - OSQuery Network and Connection Tables`: `arp_cache`, `connectivity`, `curl`, `curl_certificate`, `dns_cache`, `dns_lookup_events`, `dns_resolvers`, `etc_hosts`, `etc_protocols`, `etc_services`, `interface_addresses`, `interface_details`, `interface_ipv6`, `iptables`, `listening_ports`, `pipes`, `routes`, `socket_events`, `wifi_networks`, `wifi_status`, `wifi_survey`
- `Knowledge - Reference - OSQuery User, Auth, and Account Tables`: `account_policy_data`, `ad_config`, `authorization_mechanisms`, `authorizations`, `authorized_keys`, `default_environment`, `groups`, `known_hosts`, `last`, `location_services`, `logged_in_users`, `logon_sessions`, `managed_policies`, `ntdomains`, `office_mru`, `password_policy`, `preferences`, `screenlock`, `shadow`, `shared_folders`, `sharing_preferences`, `shell_history`, `shellbags`, `ssh_configs`, `sudoers`, `user_groups`, `user_ssh_keys`, `userassist`, `users`
- `Knowledge - Reference - OSQuery Persistence and Startup Tables`: `appcompat_shims`, `autoexec`, `background_activities_moderator`, `browser_plugins`, `chrome_extension_content_scripts`, `drivers`, `event_taps`, `kernel_extensions`, `kernel_modules`, `launchd`, `launchd_overrides`, `scheduled_tasks`, `services`, `shimcache`, `startup_items`, `system_extensions`, `systemd_units`, `wmi_cli_event_consumers`, `wmi_event_filters`, `wmi_filter_consumer_binding`, `wmi_script_event_consumers`
- `Knowledge - Reference - OSQuery System, Hardware, and Platform Tables`: `acpi_tables`, `augeas`, `battery`, `carbon_black_info`, `chassis_info`, `connected_displays`, `cpu_info`, `cpu_time`, `cpuid`, `crashes`, `crontab`, `device_firmware`, `fan_speed_sensors`, `hardware_events`, `ibridge_info`, `intel_me_info`, `iokit_devicetree`, `iokit_registry`, `kernel_info`, `kernel_panics`, `kva_speculative_info`, `load_average`, `logical_drives`, `memory_array_mapped_addresses`, `memory_arrays`, `memory_device_mapped_addresses`, `memory_devices`, `memory_error_info`, `memory_info`, `memory_map`, `msr`, `nvram`, `oem_strings`, `os_version`, `pci_devices`, `physical_disk_performance`, `platform_info`, `power_sensors`, `registry`, `secureboot`, `secureboot_certificates`, `smc_keys`, `suid_bin`, `system_controls`, `system_info`, `system_profiler`, `temperature_sensors`, `time`, `time_machine_backups`, `time_machine_destinations`, `tpm_info`, `ulimit_info`, `uptime`, `usb_devices`, `video_info`, `virtual_memory_info`, `windows_crashes`, `wmi_bios_info`
- `Knowledge - Reference - OSQuery Security, Detection, and Event Tables`: `alf`, `alf_exceptions`, `alf_explicit_auths`, `apparmor_events`, `apparmor_profiles`, `asl`, `authenticode`, `bitlocker_info`, `certificate_trust_settings`, `certificates`, `disk_encryption`, `file_events`, `gatekeeper`, `gatekeeper_approved_apps`, `kernel_keys`, `keychain_acls`, `keychain_items`, `sandboxes`, `seccomp_events`, `security_profile_info`, `selinux_events`, `selinux_settings`, `signature`, `sip_config`, `syslog_events`, `unified_log`, `windows_eventlog`, `windows_events`, `windows_firewall_rules`, `windows_security_center`, `windows_security_products`, `xprotect_entries`, `xprotect_meta`, `xprotect_reports`, `yara_events`, `yara_process`
- `Knowledge - Reference - OSQuery Application, Package, and Extension Tables`: `app_schemes`, `apps`, `apt_sources`, `chocolatey_packages`, `chrome_extensions`, `cups_destinations`, `cups_jobs`, `deb_packages`, `firefox_addons`, `homebrew_packages`, `ie_extensions`, `jetbrains_plugins`, `npm_packages`, `package_receipts`, `patches`, `portage_keywords`, `portage_packages`, `portage_use`, `programs`, `python_packages`, `rpm_packages`, `running_apps`, `safari_extensions`, `vscode_extensions`, `windows_optional_features`, `windows_search`, `windows_update_history`, `yum_sources`
- `Knowledge - Reference - OSQuery Virtualization, Cloud, and Container Tables`: `azure_instance_metadata`, `azure_instance_tags`, `docker_container_envs`, `docker_container_fs_changes`, `docker_container_labels`, `docker_container_mounts`, `docker_container_networks`, `docker_container_ports`, `docker_container_processes`, `docker_container_stats`, `docker_containers`, `docker_image_history`, `docker_image_labels`, `docker_image_layers`, `docker_images`, `docker_info`, `docker_network_labels`, `docker_networks`, `docker_version`, `docker_volume_labels`, `docker_volumes`, `ec2_instance_metadata`, `ec2_instance_tags`, `lxd_certificates`, `lxd_cluster`, `lxd_cluster_members`, `lxd_images`, `lxd_instance_config`, `lxd_instance_devices`, `lxd_instances`, `lxd_networks`, `lxd_storage_pools`, `osquery_events`, `osquery_extensions`, `osquery_flags`, `osquery_info`, `osquery_packs`, `osquery_registry`, `osquery_schedule`, `prometheus_metrics`, `ycloud_instance_metadata`
