# Knowledge - 99C - OSQuery Process and Execution Tables

_Exact OSQuery process, execution, handle, and runtime-artifact reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### bpf_process_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

Track time/action process executions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| tid | BIGINT | Thread ID |
| pid | BIGINT | Process ID |
| parent | BIGINT | Parent process ID |
| uid | BIGINT | User ID |
| gid | BIGINT | Group ID |
| cid | INTEGER | Cgroup ID |
| exit_code | TEXT | Exit code of the system call |
| probe_error | INTEGER | Set to 1 if one or more buffers could not be captured |
| syscall | TEXT | System call name |
| path | TEXT | Binary path |
| cwd | TEXT | Current working directory |
| cmdline | TEXT | Command line arguments |
| duration | INTEGER | How much time was spent inside the syscall (nsecs) |
| json_cmdline | TEXT | Command line arguments, in JSON format |
| ntime | TEXT | The nsecs uptime timestamp as obtained from BPF |
| time | BIGINT | Time of execution in UNIX time |
| eid | INTEGER | Event ID |

### bpf_socket_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

Track network socket opens and closes.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| tid | BIGINT | Thread ID |
| pid | BIGINT | Process ID |
| parent | BIGINT | Parent process ID |
| uid | BIGINT | User ID |
| gid | BIGINT | Group ID |
| cid | INTEGER | Cgroup ID |
| exit_code | TEXT | Exit code of the system call |
| probe_error | INTEGER | Set to 1 if one or more buffers could not be captured |
| syscall | TEXT | System call name |
| path | TEXT | Path of executed file |
| fd | TEXT | The file description for the process socket |
| family | INTEGER | The Internet protocol family ID |
| type | INTEGER | The socket type |
| protocol | INTEGER | The network protocol ID |
| local_address | TEXT | Local address associated with socket |
| remote_address | TEXT | Remote address associated with socket |
| local_port | INTEGER | Local network protocol port number |
| remote_port | INTEGER | Remote network protocol port number |
| duration | INTEGER | How much time was spent inside the syscall (nsecs) |
| ntime | TEXT | The nsecs uptime timestamp as obtained from BPF |
| time | BIGINT | Time of execution in UNIX time |
| eid | INTEGER | Event ID |

### carves

**Platforms:** MacOS Linux Windows

List the set of completed and in-progress carves. If carve=1 then the query is treated as a new carve request.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | BIGINT | Time at which the carve was kicked off |
| sha256 | TEXT | A SHA256 sum of the carved archive |
| size | BIGINT | Size in bytes of the carved archive |
| path | TEXT | The path of the requested carve |
| status | TEXT | Status of the carve, can be STARTING, PENDING, SUCCESS, or FAILED |
| carve_guid | TEXT | Identifying value of the carve session |
| request_id | TEXT | Identifying value of the carve request (e.g., scheduled query name, distributed request, etc) |
| carve | INTEGER | Set this value to '1' to start a file carve |

### es_process_events

**Platforms:** MacOS

**Table Type:** EVENTED TABLE

Process execution events from EndpointSecurity.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| version | INTEGER | Version of EndpointSecurity event |
| seq_num | BIGINT | Per event sequence number |
| global_seq_num | BIGINT | Global sequence number |
| pid | BIGINT | Process (or thread) ID |
| pidversion | BIGINT | Process ID version |
| path | TEXT | Path of executed file |
| parent | BIGINT | Parent process ID |
| original_parent | BIGINT | Original parent process ID in case of reparenting |
| session_id | BIGINT | The identifier of the session that contains the process group. |
| responsible_pid | BIGINT | The pid of the process responsible for this process. |
| responsible_pidversion | BIGINT | The pidversion of the process responsible for this process. |
| parent_pidversion | BIGINT | The pidversion of the parent process. |
| cmdline | TEXT | Command line arguments (argv) |
| cmdline_count | BIGINT | Number of command line arguments |
| env | TEXT | Environment variables delimited by spaces |
| env_count | BIGINT | Number of environment variables |
| cwd | TEXT | The process current working directory |
| uid | BIGINT | User ID of the process |
| euid | BIGINT | Effective User ID of the process |
| gid | BIGINT | Group ID of the process |
| egid | BIGINT | Effective Group ID of the process |
| username | TEXT | Username |
| signing_id | TEXT | Signature identifier of the process |
| team_id | TEXT | Team identifier of the process |
| cdhash | TEXT | Codesigning hash of the process |
| platform_binary | INTEGER | Indicates if the binary is Apple signed binary (1) or not (0) |
| exit_code | INTEGER | Exit code of a process in case of an exit event |
| child_pid | BIGINT | Process ID of a child process in case of a fork event |
| time | BIGINT | Time of execution in UNIX time |
| event_type | TEXT | Type of EndpointSecurity event |
| eid | TEXT | Event ID |
| codesigning_flags | TEXT | Codesigning flags matching one of these options, in a comma separated list: NOT_VALID, ADHOC, NOT_RUNTIME, INSTALLER. See kern/cs_blobs.h in XNU for descriptions. |

### es_process_file_events

**Platforms:** MacOS

**Table Type:** EVENTED TABLE

File integrity monitoring events from EndpointSecurity including process context.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| version | INTEGER | Version of EndpointSecurity event |
| seq_num | BIGINT | Per event sequence number |
| global_seq_num | BIGINT | Global sequence number |
| pid | BIGINT | Process (or thread) ID |
| parent | BIGINT | Parent process ID |
| path | TEXT | Path of executed file |
| filename | TEXT | The source or target filename for the event |
| dest_filename | TEXT | Destination filename for the event |
| event_type | TEXT | Type of EndpointSecurity event |
| time | BIGINT | Time of execution in UNIX time |
| eid | TEXT | Event ID |

### powershell_events

**Platforms:** Windows

**Table Type:** EVENTED TABLE

Powershell script blocks reconstructed to their full script content, this table requires script block logging to be enabled.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | BIGINT | Timestamp the event was received by the osquery event publisher |
| datetime | TEXT | System time at which the Powershell script event occurred |
| script_block_id | TEXT | The unique GUID of the powershell script to which this block belongs |
| script_block_count | INTEGER | The total number of script blocks for this script |
| script_text | TEXT | The text content of the Powershell script |
| script_name | TEXT | The name of the Powershell script |
| script_path | TEXT | The path for the Powershell script |
| cosine_similarity | DOUBLE | How similar the Powershell script is to a provided 'normal' character frequency |

### prefetch

**Platforms:** Windows

Prefetch files show metadata related to file execution.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Prefetch file path. |
| filename | TEXT | Executable filename. |
| hash | TEXT | Prefetch CRC hash. |
| last_run_time | INTEGER | Most recent time application was run. |
| other_run_times | TEXT | Other execution times in prefetch file. |
| run_count | INTEGER | Number of times the application has been run. |
| size | INTEGER | Application file size. |
| volume_serial | TEXT | Volume serial number. |
| volume_creation | TEXT | Volume creation time. |
| accessed_files_count | INTEGER | Number of files accessed. |
| accessed_directories_count | INTEGER | Number of directories accessed. |
| accessed_files | TEXT | Files accessed by application within ten seconds of launch. |
| accessed_directories | TEXT | Directories accessed by application within ten seconds of launch. |

### process_envs

**Platforms:** MacOS Linux

A key/value table of environment variables for each process.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | Process (or thread) ID |
| key | TEXT | Environment variable name |
| value | TEXT | Environment variable value |

### process_etw_events

**Platforms:** Windows

**Table Type:** EVENTED TABLE

Windows process execution events.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Event Type (ProcessStart, ProcessStop) |
| pid | BIGINT | Process ID |
| ppid | BIGINT | Parent Process ID |
| session_id | INTEGER | Session ID |
| flags | INTEGER | Process Flags |
| exit_code | INTEGER | Exit Code - Present only on ProcessStop events |
| path | TEXT | Path of executed binary |
| cmdline | TEXT | Command Line |
| username | TEXT | User rights - primary token username |
| token_elevation_type | TEXT | Primary token elevation type - Present only on ProcessStart events |
| token_elevation_status | INTEGER | Primary token elevation status - Present only on ProcessStart events |
| mandatory_label | TEXT | Primary token mandatory label sid - Present only on ProcessStart events |
| datetime | TEXT | Event timestamp in DATETIME format |
| time_windows | BIGINT | Event timestamp in Windows format |
| time | BIGINT | Event timestamp in Unix format |
| eid | INTEGER | Event ID |
| header_pid | BIGINT | Process ID of the process reporting the event |
| process_sequence_number | BIGINT | Process Sequence Number - Present only on ProcessStart events |
| parent_process_sequence_number | BIGINT | Parent Process Sequence Number - Present only on ProcessStart events |

### process_events

**Platforms:** MacOS Linux

**Table Type:** EVENTED TABLE

Track time/action process executions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | BIGINT | Process (or thread) ID |
| path | TEXT | Path of executed file |
| mode | TEXT | File mode permissions |
| cmdline | TEXT | Command line arguments (argv) |
| cmdline_size | BIGINT | Actual size (bytes) of command line arguments |
| env | TEXT | Environment variables delimited by spaces |
| env_count | BIGINT | Number of environment variables |
| env_size | BIGINT | Actual size (bytes) of environment list |
| cwd | TEXT | The process current working directory |
| auid | BIGINT | Audit User ID at process start |
| uid | BIGINT | User ID at process start |
| euid | BIGINT | Effective user ID at process start |
| gid | BIGINT | Group ID at process start |
| egid | BIGINT | Effective group ID at process start |
| owner_uid | BIGINT | File owner user ID |
| owner_gid | BIGINT | File owner group ID |
| atime | BIGINT | File last access in UNIX time |
| mtime | BIGINT | File modification in UNIX time |
| ctime | BIGINT | File last metadata change in UNIX time |
| btime | BIGINT | File creation in UNIX time |
| overflows | TEXT | List of structures that overflowed |
| parent | BIGINT | Process parent's PID, or -1 if cannot be determined. |
| time | BIGINT | Time of execution in UNIX time |
| uptime | BIGINT | Time of execution in system uptime |
| eid | TEXT | Event ID |
| status | BIGINT | OpenBSM Attribute: Status of the process |
| fsuid | BIGINT | Filesystem user ID at process start |
| suid | BIGINT | Saved user ID at process start |
| fsgid | BIGINT | Filesystem group ID at process start |
| sgid | BIGINT | Saved group ID at process start |
| syscall | TEXT | Syscall name: fork, vfork, clone, execve, execveat |

### process_file_events

**Platforms:** Linux

**Table Type:** EVENTED TABLE

A File Integrity Monitor implementation using the audit service.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| operation | TEXT | Operation type |
| pid | BIGINT | Process ID |
| ppid | BIGINT | Parent process ID |
| time | BIGINT | Time of execution in UNIX time |
| executable | TEXT | The executable path |
| partial | TEXT | True if this is a partial event (i.e.: this process existed before we started osquery) |
| cwd | TEXT | The current working directory of the process |
| path | TEXT | The path associated with the event |
| dest_path | TEXT | The canonical path associated with the event |
| uid | TEXT | The uid of the process performing the action |
| gid | TEXT | The gid of the process performing the action |
| auid | TEXT | Audit user ID of the process using the file |
| euid | TEXT | Effective user ID of the process using the file |
| egid | TEXT | Effective group ID of the process using the file |
| fsuid | TEXT | Filesystem user ID of the process using the file |
| fsgid | TEXT | Filesystem group ID of the process using the file |
| suid | TEXT | Saved user ID of the process using the file |
| sgid | TEXT | Saved group ID of the process using the file |
| uptime | BIGINT | Time of execution in system uptime |
| eid | TEXT | Event ID |

### process_memory_map

**Platforms:** MacOS Linux Windows

Process memory mapped files and pseudo device/regions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | Process (or thread) ID |
| start | TEXT | Virtual start address (hex) |
| end | TEXT | Virtual end address (hex) |
| permissions | TEXT | r=read, w=write, x=execute, p=private (cow) |
| offset | BIGINT | Offset into mapped path |
| device | TEXT | MA:MI Major/minor device ID |
| inode | INTEGER | Mapped path inode, 0 means uninitialized (BSS) |
| path | TEXT | Path to mapped file or mapped type |
| pseudo | INTEGER | 1 If path is a pseudo path, else 0 |

### process_namespaces

**Platforms:** Linux

Linux namespaces for processes running on the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | Process (or thread) ID |
| cgroup_namespace | TEXT | cgroup namespace inode |
| ipc_namespace | TEXT | ipc namespace inode |
| mnt_namespace | TEXT | mnt namespace inode |
| net_namespace | TEXT | net namespace inode |
| pid_namespace | TEXT | pid namespace inode |
| user_namespace | TEXT | user namespace inode |
| uts_namespace | TEXT | uts namespace inode |

### process_open_files

**Platforms:** MacOS Linux

File descriptors for each process.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | BIGINT | Process (or thread) ID |
| fd | BIGINT | Process-specific file descriptor number |
| path | TEXT | Filesystem path of descriptor |

### process_open_handles

**Platforms:** Windows

**Status:** New

Enumerate open handles for a specified process. Defaults to the osquery process if no pid constraint is provided.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | BIGINT | The process identifier that owns the handle. Required in WHERE clause |
| value | BIGINT | The handle value |
| type | TEXT | The type of object referenced by the handle. |
| access | TEXT | The access permissions of the object referenced by the handle. |
| name | TEXT | The value of the object referenced by the handle. |
| attributes | TEXT | Object handle attributes. |
| count | BIGINT | Handle Count. |
| raw_pointer_count | BIGINT | Raw Pointer/Reference Count. Meaning varies, consult Windows docs. |
| error_stage | TEXT | Error Stage. |
| error_code | BIGINT | Error Code. |

### process_open_pipes

**Platforms:** Linux

Pipes and partner processes for each process.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | BIGINT | Process ID |
| fd | BIGINT | File descriptor |
| mode | TEXT | Pipe open mode (r/w) |
| inode | BIGINT | Pipe inode number |
| type | TEXT | Pipe Type: named vs unnamed/anonymous |
| partner_pid | BIGINT | Process ID of partner process sharing a particular pipe |
| partner_fd | BIGINT | File descriptor of shared pipe at partner's end |
| partner_mode | TEXT | Mode of shared pipe at partner's end |

### process_open_sockets

**Platforms:** MacOS Linux Windows

Processes which have open network sockets on the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | Process (or thread) ID |
| fd | BIGINT | Socket file descriptor number |
| socket | BIGINT | Socket handle or inode number |
| family | INTEGER | Network protocol (IPv4, IPv6) |
| protocol | INTEGER | Transport protocol (TCP/UDP) |
| local_address | TEXT | Socket local address |
| remote_address | TEXT | Socket remote address |
| local_port | INTEGER | Socket local port |
| remote_port | INTEGER | Socket remote port |
| path | TEXT | For UNIX sockets (family=AF_UNIX), the domain path |
| state | TEXT | TCP socket state |
| net_namespace | TEXT | The inode number of the network namespace |

### processes

**Platforms:** MacOS Linux Windows

All running processes on the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | BIGINT | Process (or thread) ID |
| name | TEXT | The process path or shorthand argv[0] |
| path | TEXT | Path to executed binary |
| cmdline | TEXT | Complete argv |
| state | TEXT | Process state |
| cwd | TEXT | Process current working directory |
| root | TEXT | Process virtual root directory |
| uid | BIGINT | Unsigned user ID |
| gid | BIGINT | Unsigned group ID |
| euid | BIGINT | Unsigned effective user ID |
| egid | BIGINT | Unsigned effective group ID |
| suid | BIGINT | Unsigned saved user ID |
| sgid | BIGINT | Unsigned saved group ID |
| on_disk | INTEGER | The process path exists yes=1, no=0, unknown=-1 |
| wired_size | BIGINT | Bytes of unpageable memory used by process |
| resident_size | BIGINT | Bytes of private memory used by process |
| total_size | BIGINT | Total virtual memory size (Linux, Windows) or 'footprint' (macOS) |
| user_time | BIGINT | CPU time in milliseconds spent in user space |
| system_time | BIGINT | CPU time in milliseconds spent in kernel space |
| disk_bytes_read | BIGINT | Bytes read from disk |
| disk_bytes_written | BIGINT | Bytes written to disk |
| start_time | BIGINT | Process start time in seconds since Epoch, in case of error -1 |
| parent | BIGINT | Process parent's PID |
| pgroup | BIGINT | Process group |
| threads | INTEGER | Number of threads used by process |
| nice | INTEGER | Process nice level (-20 to 20, default 0) |
| elevated_token | INTEGER | Process uses elevated token yes=1, no=0 |
| secure_process | INTEGER | Process is secure (IUM) yes=1, no=0 |
| protection_type | TEXT | The protection type of the process |
| virtual_process | INTEGER | Process is virtual (e.g. System, Registry, vmmem) yes=1, no=0 |
| elapsed_time | BIGINT | Elapsed time in seconds this process has been running. |
| handle_count | BIGINT | Total number of handles that the process has open. This number is the sum of the handles currently opened by each thread in the process. |
| percent_processor_time | BIGINT | Returns elapsed time that all of the threads of this process used the processor to execute instructions in 100 nanoseconds ticks. |
| upid | BIGINT | A 64bit pid that is never reused. Returns -1 if we couldn't gather them from the system. |
| uppid | BIGINT | The 64bit parent pid that is never reused. Returns -1 if we couldn't gather them from the system. |
| cpu_type | INTEGER | Indicates the specific processor designed for installation. |
| cpu_subtype | INTEGER | Indicates the specific processor on which an entry may be used. |
| translated | INTEGER | Indicates whether the process is running under the Rosetta Translation Environment, yes=1, no=0, error=-1. |
| cgroup_path | TEXT | The full hierarchical path of the process's control group |

### user_events

**Platforms:** MacOS Linux

**Table Type:** EVENTED TABLE

Track user events from the audit framework.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | User ID |
| auid | BIGINT | Audit User ID |
| pid | BIGINT | Process (or thread) ID |
| message | TEXT | Message from the event |
| type | INTEGER | The file description for the process socket |
| path | TEXT | Supplied path from event |
| address | TEXT | The Internet protocol address or family ID |
| terminal | TEXT | The network protocol ID |
| time | BIGINT | Time of execution in UNIX time |
| uptime | BIGINT | Time of execution in system uptime |
| eid | TEXT | Event ID |

### user_interaction_events

**Platforms:** MacOS

**Table Type:** EVENTED TABLE

Track user interaction events from macOS' event tapping framework.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| time | BIGINT | Time |

### winbaseobj

**Platforms:** Windows

Lists named Windows objects in the default object directories, across all terminal services sessions. Example Windows object types include Mutexes, Events, Jobs and Semaphors.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| session_id | INTEGER | Terminal Services Session Id |
| object_name | TEXT | Object Name |
| object_type | TEXT | Object Type |
