# Knowledge - 99I - OSQuery Security, Detection, and Event Tables

_Exact OSQuery security, detection, audit, firewall, and event reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### alf

**Platforms:** MacOS

macOS application layer firewall (ALF) service details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| allow_signed_enabled | INTEGER | 1 If allow signed mode is enabled else 0 (not supported on macOS 15+) |
| firewall_unload | INTEGER | 1 If firewall unloading enabled else 0 (not supported on macOS 15+) |
| global_state | INTEGER | 1 If the firewall is enabled with exceptions, 2 if the firewall is configured to block all incoming connections, else 0 |
| logging_enabled | INTEGER | 1 If logging mode is enabled else 0 |
| logging_option | INTEGER | Firewall logging option (not supported on macOS 15+) |
| stealth_enabled | INTEGER | 1 If stealth mode is enabled else 0 |
| version | TEXT | Application Layer Firewall version |

### alf_exceptions

**Platforms:** MacOS

macOS application layer firewall (ALF) service exceptions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path to the executable that is excepted. On macOS 15+ this can also be a bundle identifier |
| state | INTEGER | Firewall exception state. 0 if the application is configured to allow incoming connections, 2 if the application is configured to block incoming connections and 3 if the application is configuted to allow incoming connections but with additional restrictions. |

### alf_explicit_auths

**Platforms:** MacOS

ALF services explicitly allowed to perform networking. Not supported on macOS 15+ (returns no results).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| process | TEXT | Process name that is explicitly allowed |

### apparmor_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

Track AppArmor events.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Event type |
| message | TEXT | Raw audit message |
| time | BIGINT | Time of execution in UNIX time |
| uptime | BIGINT | Time of execution in system uptime |
| eid | TEXT | Event ID |
| apparmor | TEXT | Apparmor Status like ALLOWED, DENIED etc. |
| operation | TEXT | Permission requested by the process |
| parent | UNSIGNED_BIGINT | Parent process PID |
| profile | TEXT | Apparmor profile name |
| name | TEXT | Process name |
| pid | UNSIGNED_BIGINT | Process ID |
| comm | TEXT | Command-line name of the command that was used to invoke the analyzed process |
| denied_mask | TEXT | Denied permissions for the process |
| capname | TEXT | Capability requested by the process |
| fsuid | UNSIGNED_BIGINT | Filesystem user ID |
| ouid | UNSIGNED_BIGINT | Object owner's user ID |
| capability | BIGINT | Capability number |
| requested_mask | TEXT | Requested access mask |
| info | TEXT | Additional information |
| error | TEXT | Error information |
| namespace | TEXT | AppArmor namespace |
| label | TEXT | AppArmor label |

### apparmor_profiles

**Platforms:** Linux

Track active AppArmor profiles.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Unique, aa-status compatible, policy identifier. |
| name | TEXT | Policy name. |
| attach | TEXT | Which executable(s) a profile will attach to. |
| mode | TEXT | How the policy is applied. |
| sha1 | TEXT | A unique hash that identifies this policy. |
| sha256 | TEXT | A unique hash that identifies this policy. |

### asl

**Platforms:** MacOS

Queries the Apple System Log data structure for system events.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | INTEGER | Unix timestamp. Set automatically |
| time_nano_sec | INTEGER | Nanosecond time. |
| host | TEXT | Sender's address (set by the server). |
| sender | TEXT | Sender's identification string. Default is process name. |
| facility | TEXT | Sender's facility. Default is 'user'. |
| pid | INTEGER | Sending process ID encoded as a string. Set automatically. |
| gid | BIGINT | GID that sent the log message (set by the server). |
| uid | BIGINT | UID that sent the log message (set by the server). |
| level | INTEGER | Log level number. See levels in asl.h. |
| message | TEXT | Message text. |
| ref_pid | INTEGER | Reference PID for messages proxied by launchd |
| ref_proc | TEXT | Reference process for messages proxied by launchd |
| extra | TEXT | Extra columns, in JSON format. Queries against this column are performed entirely in SQLite, so do not benefit from efficient querying via asl.h. |

### authenticode

**Platforms:** Windows

File (executable, bundle, installer, disk) code signing status.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Must provide a path or directory Required in WHERE clause |
| original_program_name | TEXT | The original program name that the publisher has signed |
| serial_number | TEXT | The certificate serial number |
| issuer_name | TEXT | The certificate issuer name |
| subject_name | TEXT | The certificate subject name |
| result | TEXT | The signature check result |

### bitlocker_info

**Platforms:** Windows

Retrieve bitlocker status of the machine.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device_id | TEXT | ID of the encrypted drive. |
| drive_letter | TEXT | Drive letter of the encrypted drive. |
| persistent_volume_id | TEXT | Persistent ID of the drive. |
| conversion_status | INTEGER | The bitlocker conversion status of the drive. |
| protection_status | INTEGER | The bitlocker protection status of the drive. |
| encryption_method | TEXT | The encryption type of the device. |
| version | INTEGER | The FVE metadata version of the drive. |
| percentage_encrypted | INTEGER | The percentage of the drive that is encrypted. |
| lock_status | INTEGER | The accessibility status of the drive from Windows. |

### certificate_trust_settings

**Platforms:** MacOS

Certificate Authorities trust settings installed in Keychains/ca-bundles.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| common_name | TEXT | Certificate common name |
| serial | TEXT | Certificate serial number |
| trust_domain | TEXT | Certificate trust settings domain |
| trust_policy_name | TEXT | Certificate trust policy name |
| trust_policy_data | TEXT | Certificate trust policy data |
| trust_allowed_error | TEXT | Certificate trust allowed error |
| trust_key_usage | TEXT | Certificate trust key usage |
| trust_result | TEXT | Certificate trust result |

### certificates

**Platforms:** MacOS Linux Windows

Certificate Authorities installed in Keychains/ca-bundles. NOTE: osquery limits frequent access to keychain files on macOS. This limit is controlled by keychain_access_interval flag. On macOS, 'path' may point to either a keychain file or a DER/PEM-encoded certificate file; non-keychain files are parsed as DER/PEM.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| common_name | TEXT | Certificate CommonName |
| subject | TEXT | Certificate distinguished name (deprecated, use subject2) |
| issuer | TEXT | Certificate issuer distinguished name (deprecated, use issuer2) |
| ca | INTEGER | 1 if CA: true (certificate is an authority) else 0 |
| self_signed | INTEGER | 1 if self-signed, else 0 |
| not_valid_before | TEXT | Lower bound of valid date |
| not_valid_after | TEXT | Certificate expiration data |
| signing_algorithm | TEXT | Signing algorithm used |
| key_algorithm | TEXT | Key algorithm used |
| key_strength | TEXT | Key size used for RSA/DSA, or curve name |
| key_usage | TEXT | Certificate key usage and extended key usage |
| subject_key_id | TEXT | SKID an optionally included SHA1 |
| authority_key_id | TEXT | AKID an optionally included SHA1 |
| sha1 | TEXT | SHA1 hash of the raw certificate contents |
| path | TEXT | Path to Keychain or PEM bundle |
| serial | TEXT | Certificate serial number |
| sid | TEXT | SID |
| store_location | TEXT | Certificate system store location |
| store | TEXT | Certificate system store |
| username | TEXT | Username |
| store_id | TEXT | Exists for service/user stores. Contains raw store id provided by WinAPI. |
| issuer2 | TEXT | Certificate issuer distinguished name |
| subject2 | TEXT | Certificate distinguished name |

### disk_encryption

**Platforms:** MacOS Linux

Disk encryption status and information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Disk name |
| uuid | TEXT | Disk Universally Unique Identifier |
| encrypted | INTEGER | 1 If encrypted: true (disk is encrypted), else 0 |
| type | TEXT | Description of cipher type and mode if available |
| encryption_status | TEXT | Disk encryption status with one of following values: encrypted \| not encrypted \| undefined |
| uid | TEXT | Currently authenticated user if available |
| user_uuid | TEXT | UUID of authenticated user if available |
| filevault_status | TEXT | FileVault status with one of following values: on \| off \| unknown |

### file_events

**Platforms:** MacOS Linux

**Table Type:** EVENTED TABLE

Track time/action changes to files specified in configuration data.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| target_path | TEXT | The path associated with the event |
| category | TEXT | The category of the file defined in the config |
| action | TEXT | Change action (UPDATE, REMOVE, etc) |
| transaction_id | BIGINT | ID used during bulk update |
| inode | BIGINT | Filesystem inode number |
| uid | BIGINT | Owning user ID |
| gid | BIGINT | Owning group ID |
| mode | TEXT | Permission bits |
| size | BIGINT | Size of file in bytes |
| atime | BIGINT | Last access time |
| mtime | BIGINT | Last modification time |
| ctime | BIGINT | Last status change time |
| md5 | TEXT | The MD5 of the file after change |
| sha1 | TEXT | The SHA1 of the file after change |
| sha256 | TEXT | The SHA256 of the file after change |
| hashed | INTEGER | 1 if the file was hashed, 0 if not, -1 if hashing failed |
| time | BIGINT | Time of file event |
| eid | TEXT | Event ID |

### gatekeeper

**Platforms:** MacOS

macOS Gatekeeper Details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| assessments_enabled | INTEGER | 1 If a Gatekeeper is enabled else 0 |
| dev_id_enabled | INTEGER | 1 If a Gatekeeper allows execution from identified developers else 0 |
| version | TEXT | Version of Gatekeeper's gke.bundle |
| opaque_version | TEXT | Version of Gatekeeper's gkopaque.bundle |

### gatekeeper_approved_apps

**Platforms:** MacOS

Gatekeeper apps a user has allowed to run.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path of executable allowed to run |
| requirement | TEXT | Code signing requirement language |
| ctime | DOUBLE | Last change time |
| mtime | DOUBLE | Last modification time |

### kernel_keys

**Platforms:** Linux

List of security data, authentication keys and encryption keys.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| serial_number | TEXT | The serial key of the key. |
| flags | TEXT | A set of flags describing the state of the key. |
| usage | BIGINT | the number of threads and open file references that refer to this key. |
| timeout | TEXT | The amount of time until the key will expire, expressed in human-readable form. The string perm here means that the key is permanent (no timeout). The string expd means that the key has already expired. |
| permissions | TEXT | The key permissions, expressed as four hexadecimal bytes containing, from left to right, the possessor, user, group, and other permissions. |
| uid | BIGINT | The user ID of the key owner. |
| gid | BIGINT | The group ID of the key. |
| type | TEXT | The key type. |
| description | TEXT | The key description. |

### keychain_acls

**Platforms:** MacOS

Applications that have ACL entries in the keychain. NOTE: osquery limits frequent access to keychain files. This limit is controlled by keychain_access_interval flag.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| keychain_path | TEXT | The path of the keychain |
| authorizations | TEXT | A space delimited set of authorization attributes |
| path | TEXT | The path of the authorized application |
| description | TEXT | The description included with the ACL entry |
| label | TEXT | An optional label tag that may be included with the keychain entry |

### keychain_items

**Platforms:** MacOS

Generic details about keychain items. NOTE: osquery limits frequent access to keychain files. This limit is controlled by keychain_access_interval flag.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| label | TEXT | Generic item name |
| description | TEXT | Optional item description |
| comment | TEXT | Optional keychain comment |
| account | TEXT | Optional item account |
| created | TEXT | Date item was created |
| modified | TEXT | Date of last modification |
| type | TEXT | Keychain item type (class) |
| pk_hash | TEXT | Hash of associated public key (SHA1 of subjectPublicKey, see RFC 8520 4.2.1.2) |
| path | TEXT | Path to keychain containing item |

### sandboxes

**Platforms:** MacOS

macOS application sandboxes container details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| label | TEXT | UTI-format bundle or label ID |
| user | TEXT | Sandbox owner |
| enabled | INTEGER | Application sandboxings enabled on container |
| build_id | TEXT | Sandbox-specific identifier |
| bundle_path | TEXT | Application bundle used by the sandbox |
| path | TEXT | Path to sandbox container directory |

### seccomp_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

A virtual table that tracks seccomp events.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | BIGINT | Time of execution in UNIX time |
| uptime | BIGINT | Time of execution in system uptime |
| auid | UNSIGNED_BIGINT | Audit user ID (loginuid) of the user who started the analyzed process |
| uid | UNSIGNED_BIGINT | User ID of the user who started the analyzed process |
| gid | UNSIGNED_BIGINT | Group ID of the user who started the analyzed process |
| ses | UNSIGNED_BIGINT | Session ID of the session from which the analyzed process was invoked |
| pid | UNSIGNED_BIGINT | Process ID |
| comm | TEXT | Command-line name of the command that was used to invoke the analyzed process |
| exe | TEXT | The path to the executable that was used to invoke the analyzed process |
| sig | BIGINT | Signal value sent to process by seccomp |
| arch | TEXT | Information about the CPU architecture |
| syscall | TEXT | Type of the system call |
| compat | BIGINT | Is system call in compatibility mode |
| ip | TEXT | Instruction pointer value |
| code | TEXT | The seccomp action |

### security_profile_info

**Platforms:** Windows

Information on the security profile of a given system by listing the system Account and Audit Policies. This table mimics the exported securitypolicy output from the secedit tool.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| minimum_password_age | INTEGER | Determines the minimum number of days that a password must be used before the user can change it |
| maximum_password_age | INTEGER | Determines the maximum number of days that a password can be used before the client requires the user to change it |
| minimum_password_length | INTEGER | Determines the least number of characters that can make up a password for a user account |
| password_complexity | INTEGER | Determines whether passwords must meet a series of strong-password guidelines |
| password_history_size | INTEGER | Number of unique new passwords that must be associated with a user account before an old password can be reused |
| lockout_bad_count | INTEGER | Number of failed logon attempts after which a user account MUST be locked out |
| logon_to_change_password | INTEGER | Determines if logon session is required to change the password |
| force_logoff_when_expire | INTEGER | Determines whether SMB client sessions with the SMB server will be forcibly disconnected when the client's logon hours expire |
| new_administrator_name | TEXT | Determines the name of the Administrator account on the local computer |
| new_guest_name | TEXT | Determines the name of the Guest account on the local computer |
| clear_text_password | INTEGER | Determines whether passwords MUST be stored by using reversible encryption |
| lsa_anonymous_name_lookup | INTEGER | Determines if an anonymous user is allowed to query the local LSA policy |
| enable_admin_account | INTEGER | Determines whether the Administrator account on the local computer is enabled |
| enable_guest_account | INTEGER | Determines whether the Guest account on the local computer is enabled |
| audit_system_events | INTEGER | Determines whether the operating system MUST audit System Change, System Startup, System Shutdown, Authentication Component Load, and Loss or Excess of Security events |
| audit_logon_events | INTEGER | Determines whether the operating system MUST audit each instance of a user attempt to log on or log off this computer |
| audit_object_access | INTEGER | Determines whether the operating system MUST audit each instance of user attempts to access a non-Active Directory object that has its own SACL specified |
| audit_privilege_use | INTEGER | Determines whether the operating system MUST audit each instance of user attempts to exercise a user right |
| audit_policy_change | INTEGER | Determines whether the operating system MUST audit each instance of user attempts to change user rights assignment policy, audit policy, account policy, or trust policy |
| audit_account_manage | INTEGER | Determines whether the operating system MUST audit each event of account management on a computer |
| audit_process_tracking | INTEGER | Determines whether the operating system MUST audit process-related events |
| audit_ds_access | INTEGER | Determines whether the operating system MUST audit each instance of user attempts to access an Active Directory object that has its own system access control list (SACL) specified |
| audit_account_logon | INTEGER | Determines whether the operating system MUST audit each time this computer validates the credentials of an account |

### selinux_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

Track SELinux events.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Event type |
| message | TEXT | Message |
| time | BIGINT | Time of execution in UNIX time |
| uptime | BIGINT | Time of execution in system uptime |
| eid | TEXT | Event ID |

### selinux_settings

**Platforms:** Linux

Track active SELinux settings.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| scope | TEXT | Where the key is located inside the SELinuxFS mount point. |
| key | TEXT | Key or class name. |
| value | TEXT | Active value. |

### signature

**Platforms:** MacOS

File (executable, bundle, installer, disk) code signing status.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Must provide a path or directory Required in WHERE clause |
| hash_resources | INTEGER | Set to 1 to also hash resources, or 0 otherwise. Default is 1 |
| hash_executable | INTEGER | Set to 1 to also hash the executable, or 0 otherwise. Default is 1 |
| arch | TEXT | If applicable, the arch of the signed code |
| signed | INTEGER | 1 If the file is signed else 0 |
| identifier | TEXT | The signing identifier sealed into the signature |
| cdhash | TEXT | Hash of the application Code Directory |
| team_identifier | TEXT | The team signing identifier sealed into the signature |
| authority | TEXT | Certificate Common Name |
| entitlements | TEXT | JSON representation of the code signing entitlements |

### sip_config

**Platforms:** MacOS

Apple's System Integrity Protection (rootless) status.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| config_flag | TEXT | The System Integrity Protection config flag |
| enabled | INTEGER | 1 if this configuration is enabled, otherwise 0 |
| enabled_nvram | INTEGER | 1 if this configuration is enabled, otherwise 0 |

### syslog_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | BIGINT | Current unix epoch time |
| datetime | TEXT | Time known to syslog |
| host | TEXT | Hostname configured for syslog |
| severity | INTEGER | Syslog severity |
| facility | TEXT | Syslog facility |
| tag | TEXT | The syslog tag |
| message | TEXT | The syslog message |
| eid | TEXT | Event ID |

### unified_log

**Platforms:** MacOS

Queries the OSLog framework for entries in the system log. The maximum number of rows returned is limited for performance issues. Use timestamp > or >= constraints to optimize query performance. This table introduces a new idiom for extracting sequential data in batches using multiple queries, ordered by timestamp. To trigger it, the user should include the condition "timestamp > -1", and the table will handle pagination. Note that the saved pagination counter is incremented globally across all queries and table invocations within a query. To avoid multiple table invocations within a query, use only AND and = constraints in WHERE clause.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| timestamp | BIGINT | unix timestamp associated with the entry |
| timestamp_double | TEXT | floating point timestamp associated with the entry |
| storage | INTEGER | the storage category for the entry |
| message | TEXT | composed message |
| activity | BIGINT | the activity ID associate with the entry |
| process | TEXT | the name of the process that made the entry |
| pid | BIGINT | the pid of the process that made the entry |
| sender | TEXT | the name of the binary image that made the entry |
| tid | BIGINT | the tid of the thread that made the entry |
| category | TEXT | the category of the os_log_t used |
| subsystem | TEXT | the subsystem of the os_log_t used |
| level | TEXT | the severity level of the entry (undefined, debug, info, default, error, fault) |
| max_rows | INTEGER | the max number of rows returned (defaults to 100) |
| predicate | TEXT | predicate to search (see `log help predicates`), note that this is merged into the predicate created from the column constraints |

### windows_eventlog

**Platforms:** Windows

Table for querying all recorded Windows event logs.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| channel | TEXT | Source or channel of the event Required in WHERE clause |
| datetime | TEXT | System time at which the event occurred |
| task | INTEGER | Task value associated with the event |
| level | INTEGER | Severity level associated with the event |
| provider_name | TEXT | Provider name of the event |
| provider_guid | TEXT | Provider guid of the event |
| computer_name | TEXT | Hostname of system where event was generated |
| eventid | INTEGER | Event ID of the event |
| keywords | TEXT | A bitmask of the keywords defined in the event |
| data | TEXT | Data associated with the event |
| pid | INTEGER | Process ID which emitted the event record |
| tid | INTEGER | Thread ID which emitted the event record |
| time_range | TEXT | System time to selectively filter the events |
| timestamp | TEXT | Timestamp to selectively filter the events |
| xpath | TEXT | The custom query to filter events Required in WHERE clause |

### windows_events

**Platforms:** Windows

**Table Type:** EVENTED TABLE

Windows Event logs.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | BIGINT | Timestamp the event was received |
| datetime | TEXT | System time at which the event occurred |
| source | TEXT | Source or channel of the event |
| provider_name | TEXT | Provider name of the event |
| provider_guid | TEXT | Provider guid of the event |
| computer_name | TEXT | Hostname of system where event was generated |
| eventid | INTEGER | Event ID of the event |
| task | INTEGER | Task value associated with the event |
| level | INTEGER | The severity level associated with the event |
| keywords | TEXT | A bitmask of the keywords defined in the event |
| data | TEXT | Data associated with the event |
| eid | TEXT | Event ID |

### windows_firewall_rules

**Platforms:** Windows

Provides the list of Windows firewall rules.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Friendly name of the rule |
| app_name | TEXT | Friendly name of the application to which the rule applies |
| action | TEXT | Action for the rule or default setting |
| enabled | INTEGER | 1 if the rule is enabled |
| grouping | TEXT | Group to which an individual rule belongs |
| direction | TEXT | Direction of traffic for which the rule applies |
| protocol | TEXT | IP protocol of the rule |
| local_addresses | TEXT | Local addresses for the rule |
| remote_addresses | TEXT | Remote addresses for the rule |
| local_ports | TEXT | Local ports for the rule |
| remote_ports | TEXT | Remote ports for the rule |
| icmp_types_codes | TEXT | ICMP types and codes for the rule |
| profile_domain | INTEGER | 1 if the rule profile type is domain |
| profile_private | INTEGER | 1 if the rule profile type is private |
| profile_public | INTEGER | 1 if the rule profile type is public |
| service_name | TEXT | Service name property of the application |

### windows_security_center

**Platforms:** Windows

The health status of Window Security features. Health values can be "Good", "Poor". "Snoozed", "Not Monitored", and "Error".

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| firewall | TEXT | The health of the monitored Firewall (see windows_security_products) |
| autoupdate | TEXT | The health of the Windows Autoupdate feature |
| antivirus | TEXT | The health of the monitored Antivirus solution (see windows_security_products) |
| antispyware | TEXT | Deprecated (always 'Good'). |
| internet_settings | TEXT | The health of the Internet Settings |
| windows_security_center_service | TEXT | The health of the Windows Security Center Service |
| user_account_control | TEXT | The health of the User Account Control (UAC) capability in Windows |

### windows_security_products

**Platforms:** Windows

Enumeration of registered Windows security products. Note: Not compatible with Windows Server.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Type of security product |
| name | TEXT | Name of product |
| state | TEXT | State of protection |
| state_timestamp | TEXT | Timestamp for the product state |
| remediation_path | TEXT | Remediation path |
| signatures_up_to_date | INTEGER | 1 if product signatures are up to date, else 0 |

### xprotect_entries

**Platforms:** MacOS

Database of the machine's XProtect signatures.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Description of XProtected malware |
| launch_type | TEXT | Launch services content type |
| identity | TEXT | XProtect identity (SHA1) of content |
| filename | TEXT | Use this file name to match |
| filetype | TEXT | Use this file type to match |
| optional | INTEGER | Match any of the identities/patterns for this XProtect name |
| uses_pattern | INTEGER | Uses a match pattern instead of identity |

### xprotect_meta

**Platforms:** MacOS

Database of the machine's XProtect browser-related signatures.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| identifier | TEXT | Browser plugin or extension identifier |
| type | TEXT | Either plugin or extension |
| developer_id | TEXT | Developer identity (SHA1) of extension |
| min_version | TEXT | The minimum allowed plugin version. |

### xprotect_reports

**Platforms:** MacOS

Database of XProtect matches (if user generated/sent an XProtect report).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Description of XProtected malware |
| user_action | TEXT | Action taken by user after prompted |
| time | TEXT | Quarantine alert time |

### yara_events

**Platforms:** MacOS Linux Windows

**Table Type:** EVENTED TABLE

Track YARA matches for files specified in configuration data.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| target_path | TEXT | The path scanned |
| category | TEXT | The category of the file |
| action | TEXT | Change action (UPDATE, REMOVE, etc) |
| matches | TEXT | List of YARA matches |
| count | INTEGER | Number of YARA matches |
| strings | TEXT | Matching strings |
| tags | TEXT | Matching tags |
| time | BIGINT | Time of the scan |
| eid | TEXT | Event ID |
| transaction_id | BIGINT | ID used during bulk update |

### yara_process

**Platforms:** MacOS Linux Windows

**Status:** New

Triggers one-off YARA query for process memory of the specified pid. Additionally requires one of `sig_group`, `sigfile`, or `sigrule`.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | The pid scanned (process memory) Required in WHERE clause |
| matches | TEXT | List of YARA matches |
| count | INTEGER | Number of YARA matches |
| sig_group | TEXT | Signature group used |
| sigfile | TEXT | Signature file used |
| sigrule | TEXT | Signature strings used |
| strings | TEXT | Matching strings |
| tags | TEXT | Matching tags |
| sigurl | TEXT | Signature url |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
