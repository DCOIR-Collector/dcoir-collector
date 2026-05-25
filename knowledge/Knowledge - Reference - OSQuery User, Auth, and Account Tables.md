# Knowledge - Reference - OSQuery User, Auth, and Account Tables

_Exact OSQuery user, account, login, SSH, and auth-policy reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### account_policy_data

**Platforms:** MacOS

Additional macOS user account data from the AccountPolicy section of OpenDirectory.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | User ID |
| creation_time | DOUBLE | When the account was first created |
| failed_login_count | BIGINT | The number of failed login attempts using an incorrect password. Count resets after a correct password is entered. |
| failed_login_timestamp | DOUBLE | The time of the last failed login attempt. Resets after a correct password is entered |
| password_last_set_time | DOUBLE | The time the password was last changed |

### ad_config

**Platforms:** MacOS

macOS Active Directory configuration.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The macOS-specific configuration name |
| domain | TEXT | Active Directory trust domain |
| option | TEXT | Canonical name of option |
| value | TEXT | Variable typed option value |

### authorization_mechanisms

**Platforms:** MacOS

macOS Authorization mechanisms database.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| label | TEXT | Label of the authorization right |
| plugin | TEXT | Authorization plugin name |
| mechanism | TEXT | Name of the mechanism that will be called |
| privileged | TEXT | If privileged it will run as root, else as an anonymous user |
| entry | TEXT | The whole string entry |

### authorizations

**Platforms:** MacOS

macOS Authorization rights database.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| label | TEXT | Item name, usually in reverse domain format |
| modified | TEXT | Label top-level key |
| allow_root | TEXT | Label top-level key |
| timeout | TEXT | Label top-level key |
| version | TEXT | Label top-level key |
| tries | TEXT | Label top-level key |
| authenticate_user | TEXT | Label top-level key |
| shared | TEXT | Label top-level key |
| comment | TEXT | Label top-level key |
| created | TEXT | Label top-level key |
| class | TEXT | Label top-level key |
| session_owner | TEXT | Label top-level key |

### authorized_keys

**Platforms:** MacOS Linux

A line-delimited authorized_keys table.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local owner of authorized_keys file |
| algorithm | TEXT | Key type |
| key | TEXT | Key encoded as base64 |
| options | TEXT | Optional list of login options |
| comment | TEXT | Optional comment |
| key_file | TEXT | Path to the authorized_keys file |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### default_environment

**Platforms:** Windows

Default environment variables and values.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| variable | TEXT | Name of the environment variable |
| value | TEXT | Value of the environment variable |
| expand | INTEGER | 1 if the variable needs expanding, 0 otherwise |

### groups

**Platforms:** MacOS Linux Windows

Local system groups.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| gid | BIGINT | Unsigned int64 group ID |
| gid_signed | BIGINT | A signed int64 version of gid |
| groupname | TEXT | Canonical local group name |
| group_sid | TEXT | Unique group ID |
| comment | TEXT | Remarks or comments associated with the group |
| is_hidden | INTEGER | IsHidden attribute set in OpenDirectory |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### known_hosts

**Platforms:** MacOS Linux

A line-delimited known_hosts table.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local user that owns the known_hosts file |
| key | TEXT | parsed authorized keys line |
| key_file | TEXT | Path to known_hosts file |

### last

**Platforms:** MacOS Linux

System logins and logouts.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| username | TEXT | Entry username |
| tty | TEXT | Entry terminal |
| pid | INTEGER | Process (or thread) ID |
| type | INTEGER | Entry type, according to ut_type types (utmp.h) |
| type_name | TEXT | Entry type name, according to ut_type types (utmp.h) |
| time | INTEGER | Entry timestamp |
| host | TEXT | Entry hostname |

### location_services

**Platforms:** MacOS

Reports the status of the Location Services feature of the OS.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| enabled | INTEGER | 1 if Location Services are enabled, else 0 |

### logged_in_users

**Platforms:** MacOS Linux Windows

Users with an active shell on the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Login type |
| user | TEXT | User login name |
| tty | TEXT | Device name |
| host | TEXT | Remote hostname |
| time | BIGINT | Time entry was made |
| pid | INTEGER | Process (or thread) ID |
| sid | TEXT | The user's unique security identifier |
| registry_hive | TEXT | HKEY_USERS registry hive |

### logon_sessions

**Platforms:** Windows

Windows Logon Session.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| logon_id | INTEGER | A locally unique identifier (LUID) that identifies a logon session. |
| user | TEXT | The account name of the security principal that owns the logon session. |
| logon_domain | TEXT | The name of the domain used to authenticate the owner of the logon session. |
| authentication_package | TEXT | The authentication package used to authenticate the owner of the logon session. |
| logon_type | TEXT | The logon method. |
| session_id | INTEGER | The Terminal Services session identifier. |
| logon_sid | TEXT | The user's security identifier (SID). |
| logon_time | BIGINT | The time the session owner logged on. |
| logon_server | TEXT | The name of the server used to authenticate the owner of the logon session. |
| dns_domain_name | TEXT | The DNS name for the owner of the logon session. |
| upn | TEXT | The user principal name (UPN) for the owner of the logon session. |
| logon_script | TEXT | The script used for logging on. |
| profile_path | TEXT | The home directory for the logon session. |
| home_directory | TEXT | The home directory for the logon session. |
| home_directory_drive | TEXT | The drive location of the home directory of the logon session. |

### managed_policies

**Platforms:** MacOS

The managed configuration policies from AD, MDM, MCX, etc.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| domain | TEXT | System or manager-chosen domain key |
| uuid | TEXT | Optional UUID assigned to policy set |
| name | TEXT | Policy key name |
| value | TEXT | Policy value |
| username | TEXT | Policy applies only this user |
| manual | INTEGER | 1 if policy was loaded manually, otherwise 0 |

### ntdomains

**Platforms:** Windows

Display basic NT domain information of a Windows machine.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The label by which the object is known. |
| client_site_name | TEXT | The name of the site where the domain controller is configured. |
| dc_site_name | TEXT | The name of the site where the domain controller is located. |
| dns_forest_name | TEXT | The name of the root of the DNS tree. |
| domain_controller_address | TEXT | The IP Address of the discovered domain controller.. |
| domain_controller_name | TEXT | The name of the discovered domain controller. |
| domain_name | TEXT | The name of the domain. |
| status | TEXT | The current status of the domain object. |

### office_mru

**Platforms:** Windows

View recently opened Office documents.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| application | TEXT | Associated Office application |
| version | TEXT | Office application version number |
| path | TEXT | File path |
| last_opened_time | BIGINT | Most recent opened time file was opened |
| sid | TEXT | User SID |

### password_policy

**Platforms:** MacOS

OpenDirectory account policies for macOS including password content, authentication, and password change policies.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | User ID for the policy, -1 for policies that are global |
| policy_identifier | TEXT | Policy Identifier |
| policy_content | TEXT | Policy content |
| policy_description | TEXT | Policy description |
| policy_category | TEXT | Policy category: passwordPolicyAuthentication, passwordPolicyPasswordChange, or passwordPolicyPasswordContent |
| policy_parameters | TEXT | Policy parameters serialized as JSON |

### preferences

**Platforms:** MacOS

macOS defaults and managed preferences.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| domain | TEXT | Application ID usually in com.name.product format |
| key | TEXT | Preference top-level key |
| subkey | TEXT | Intemediate key path, includes lists/dicts |
| value | TEXT | String value of most CF types |
| forced | INTEGER | 1 if the value is forced/managed, else 0 |
| username | TEXT | (optional) read preferences for a specific user |
| host | TEXT | 'current' or 'any' host, where 'current' takes precedence |

### screenlock

**Platforms:** MacOS

macOS screenlock status. Note: only fetches results for osquery's current logged-in user context. The user must also have recently logged in.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| enabled | INTEGER | 1 If a password is required after sleep or the screensaver begins; else 0 |
| grace_period | INTEGER | The amount of time in seconds the screen must be asleep or the screensaver on before a password is required on-wake. 0 = immediately; -1 = no password is required on-wake |

### shadow

**Platforms:** Linux

Local system users encrypted passwords and related information. Please note, that you usually need superuser rights to access `/etc/shadow`.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| password_status | TEXT | Password status |
| hash_alg | TEXT | Password hashing algorithm |
| last_change | BIGINT | Date of last password change (starting from UNIX epoch date) |
| min | BIGINT | Minimal number of days between password changes |
| max | BIGINT | Maximum number of days between password changes |
| warning | BIGINT | Number of days before password expires to warn user about it |
| inactive | BIGINT | Number of days after password expires until account is blocked |
| expire | BIGINT | Number of days since UNIX epoch date until account is disabled |
| flag | BIGINT | Reserved |
| username | TEXT | Username |

### shared_folders

**Platforms:** MacOS

Folders available to others via SMB or AFP.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The shared name of the folder as it appears to other users |
| path | TEXT | Absolute path of shared folder on the local system |

### sharing_preferences

**Platforms:** MacOS

macOS Sharing preferences.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| screen_sharing | INTEGER | 1 If screen sharing is enabled else 0 |
| file_sharing | INTEGER | 1 If file sharing is enabled else 0 |
| printer_sharing | INTEGER | 1 If printer sharing is enabled else 0 |
| remote_login | INTEGER | 1 If remote login is enabled else 0 |
| remote_management | INTEGER | 1 If remote management is enabled else 0 |
| remote_apple_events | INTEGER | 1 If remote apple events are enabled else 0 |
| internet_sharing | INTEGER | 1 If internet sharing is enabled else 0 |
| bluetooth_sharing | INTEGER | 1 If bluetooth sharing is enabled for any user else 0 |
| disc_sharing | INTEGER | 1 If CD or DVD sharing is enabled else 0 |
| content_caching | INTEGER | 1 If content caching is enabled else 0 |

### shell_history

**Platforms:** MacOS Linux

A line-delimited (command) table of per-user .*_history data.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | Shell history owner |
| time | INTEGER | Entry timestamp. It could be absent, default value is 0. |
| command | TEXT | Unparsed date/line/command history line |
| history_file | TEXT | Path to the .*_history for this user |

### shellbags

**Platforms:** Windows

Shows directories accessed via Windows Explorer.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| sid | TEXT | User SID |
| source | TEXT | Shellbags source Registry file |
| path | TEXT | Directory name. |
| modified_time | BIGINT | Directory Modified time. |
| created_time | BIGINT | Directory Created time. |
| accessed_time | BIGINT | Directory Accessed time. |
| mft_entry | BIGINT | Directory master file table entry. |
| mft_sequence | INTEGER | Directory master file table sequence. |

### ssh_configs

**Platforms:** MacOS Linux Windows

A table of parsed ssh_configs.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local owner of the ssh_config file |
| block | TEXT | The host or match block |
| option | TEXT | The option and value |
| ssh_config_file | TEXT | Path to the ssh_config file |

### sudoers

**Platforms:** MacOS Linux

Rules for running commands as other users via sudo.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| source | TEXT | Source file containing the given rule |
| header | TEXT | Symbol for given rule |
| rule_details | TEXT | Rule definition |

### user_groups

**Platforms:** MacOS Linux Windows

Local system user group relationships.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | User ID |
| gid | BIGINT | Group ID |

### user_ssh_keys

**Platforms:** MacOS Linux Windows

Returns the private keys in the users ~/.ssh directory and whether or not they are encrypted.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local user that owns the key file |
| path | TEXT | Path to key file |
| encrypted | INTEGER | 1 if key is encrypted, 0 otherwise |
| key_type | TEXT | The type of the private key. One of [rsa, dsa, dh, ec, hmac, cmac], or the empty string. |
| key_group_name | TEXT | The group of the private key. Supported for a subset of key_types implemented by OpenSSL |
| key_length | INTEGER | The cryptographic length of the cryptosystem to which the private key belongs, in bits. Definition of cryptographic length is specific to cryptosystem. -1 if unavailable |
| key_security_bits | INTEGER | The number of security bits of the private key, bits of security as defined in NIST SP800-57. -1 if unavailable |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### userassist

**Platforms:** Windows

UserAssist Registry Key tracks when a user executes an application from Windows Explorer.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Application file path. |
| last_execution_time | BIGINT | Most recent time application was executed. |
| count | INTEGER | Number of times the application has been executed. |
| sid | TEXT | User SID. |

### users

**Platforms:** MacOS Linux Windows

Local user accounts (including domain accounts that have logged on locally (Windows)).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | User ID |
| gid | BIGINT | Group ID (unsigned) |
| uid_signed | BIGINT | User ID as int64 signed (Apple) |
| gid_signed | BIGINT | Default group ID as int64 signed (Apple) |
| username | TEXT | Username |
| description | TEXT | Optional user description |
| directory | TEXT | User's home directory |
| shell | TEXT | User's configured default shell |
| uuid | TEXT | User's UUID (Apple) or SID (Windows) |
| type | TEXT | Whether the account is roaming (domain), local, or a system profile |
| is_hidden | INTEGER | IsHidden attribute set in OpenDirectory |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| include_remote | INTEGER | 1 to include remote (LDAP/AD) accounts (default 0). Warning: without any uid/username filtering it may list whole LDAP directories |
