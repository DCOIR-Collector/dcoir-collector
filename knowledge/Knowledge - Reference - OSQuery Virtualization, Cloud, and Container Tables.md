# Knowledge - Reference - OSQuery Virtualization, Cloud, and Container Tables

_Exact OSQuery container, virtualization, cloud-metadata, and OSQuery self-state reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### azure_instance_metadata

**Platforms:** MacOS Linux Windows

Azure instance metadata.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| location | TEXT | Azure Region the VM is running in |
| name | TEXT | Name of the VM |
| offer | TEXT | Offer information for the VM image (Azure image gallery VMs only) |
| publisher | TEXT | Publisher of the VM image |
| sku | TEXT | SKU for the VM image |
| version | TEXT | Version of the VM image |
| os_type | TEXT | Linux or Windows |
| platform_update_domain | TEXT | Update domain the VM is running in |
| platform_fault_domain | TEXT | Fault domain the VM is running in |
| vm_id | TEXT | Unique identifier for the VM |
| vm_size | TEXT | VM size |
| subscription_id | TEXT | Azure subscription for the VM |
| resource_group_name | TEXT | Resource group for the VM |
| placement_group_id | TEXT | Placement group for the VM scale set |
| vm_scale_set_name | TEXT | VM scale set name |
| zone | TEXT | Availability zone of the VM |

### azure_instance_tags

**Platforms:** MacOS Linux Windows

Azure instance tags.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| vm_id | TEXT | Unique identifier for the VM |
| key | TEXT | The tag key |
| value | TEXT | The tag value |

### docker_container_envs

**Platforms:** MacOS Linux

Docker container environment variables.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID |
| key | TEXT | Environment variable name |
| value | TEXT | Environment variable value |

### docker_container_fs_changes

**Platforms:** MacOS Linux

Changes to files or directories on container's filesystem.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID Required in WHERE clause |
| path | TEXT | FIle or directory path relative to rootfs |
| change_type | TEXT | Type of change: C:Modified, A:Added, D:Deleted |

### docker_container_labels

**Platforms:** MacOS Linux

Docker container labels.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID |
| key | TEXT | Label key |
| value | TEXT | Optional label value |

### docker_container_mounts

**Platforms:** MacOS Linux

Docker container mounts.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID |
| type | TEXT | Type of mount (bind, volume) |
| name | TEXT | Optional mount name |
| source | TEXT | Source path on host |
| destination | TEXT | Destination path inside container |
| driver | TEXT | Driver providing the mount |
| mode | TEXT | Mount options (rw, ro) |
| rw | INTEGER | 1 if read/write. 0 otherwise |
| propagation | TEXT | Mount propagation |

### docker_container_networks

**Platforms:** MacOS Linux

Docker container networks.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID |
| name | TEXT | Network name |
| network_id | TEXT | Network ID |
| endpoint_id | TEXT | Endpoint ID |
| gateway | TEXT | Gateway |
| ip_address | TEXT | IP address |
| ip_prefix_len | INTEGER | IP subnet prefix length |
| ipv6_gateway | TEXT | IPv6 gateway |
| ipv6_address | TEXT | IPv6 address |
| ipv6_prefix_len | INTEGER | IPv6 subnet prefix length |
| mac_address | TEXT | MAC address |

### docker_container_ports

**Platforms:** MacOS Linux

Docker container ports.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID |
| type | TEXT | Protocol (tcp, udp) |
| port | INTEGER | Port inside the container |
| host_ip | TEXT | Host IP address on which public port is listening |
| host_port | INTEGER | Host port |

### docker_container_processes

**Platforms:** MacOS Linux

Docker container processes.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID Required in WHERE clause |
| pid | BIGINT | Process ID |
| name | TEXT | The process path or shorthand argv[0] |
| cmdline | TEXT | Complete argv |
| state | TEXT | Process state |
| uid | BIGINT | User ID |
| gid | BIGINT | Group ID |
| euid | BIGINT | Effective user ID |
| egid | BIGINT | Effective group ID |
| suid | BIGINT | Saved user ID |
| sgid | BIGINT | Saved group ID |
| wired_size | BIGINT | Bytes of unpageable memory used by process |
| resident_size | BIGINT | Bytes of private memory used by process |
| total_size | BIGINT | Total virtual memory size |
| start_time | BIGINT | Process start in seconds since boot (non-sleeping) |
| parent | BIGINT | Process parent's PID |
| pgroup | BIGINT | Process group |
| threads | INTEGER | Number of threads used by process |
| nice | INTEGER | Process nice level (-20 to 20, default 0) |
| user | TEXT | User name |
| time | TEXT | Cumulative CPU time. [DD-]HH:MM:SS format |
| cpu | DOUBLE | CPU utilization as percentage |
| mem | DOUBLE | Memory utilization as percentage |

### docker_container_stats

**Platforms:** MacOS Linux

Docker container statistics. Queries on this table take at least one second.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID Required in WHERE clause |
| name | TEXT | Container name |
| pids | INTEGER | Number of processes |
| read | BIGINT | UNIX time when stats were read |
| preread | BIGINT | UNIX time when stats were last read |
| interval | BIGINT | Difference between read and preread in nano-seconds |
| disk_read | BIGINT | Total disk read bytes |
| disk_write | BIGINT | Total disk write bytes |
| num_procs | INTEGER | Number of processors |
| cpu_total_usage | BIGINT | Total CPU usage |
| cpu_kernelmode_usage | BIGINT | CPU kernel mode usage |
| cpu_usermode_usage | BIGINT | CPU user mode usage |
| system_cpu_usage | BIGINT | CPU system usage |
| online_cpus | INTEGER | Online CPUs |
| pre_cpu_total_usage | BIGINT | Last read total CPU usage |
| pre_cpu_kernelmode_usage | BIGINT | Last read CPU kernel mode usage |
| pre_cpu_usermode_usage | BIGINT | Last read CPU user mode usage |
| pre_system_cpu_usage | BIGINT | Last read CPU system usage |
| pre_online_cpus | INTEGER | Last read online CPUs |
| memory_usage | BIGINT | Memory usage |
| memory_cached | BIGINT | Memory cached |
| memory_inactive_file | BIGINT | Memory inactive file |
| memory_total_inactive_file | BIGINT | Memory total inactive file |
| memory_max_usage | BIGINT | Memory maximum usage |
| memory_limit | BIGINT | Memory limit |
| network_rx_bytes | BIGINT | Total network bytes read |
| network_tx_bytes | BIGINT | Total network bytes transmitted |

### docker_containers

**Platforms:** MacOS Linux

Docker containers information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Container ID |
| name | TEXT | Container name |
| image | TEXT | Docker image (name) used to launch this container |
| image_id | TEXT | Docker image ID |
| command | TEXT | Command with arguments |
| created | BIGINT | Time of creation as UNIX time |
| state | TEXT | Container state (created, restarting, running, removing, paused, exited, dead) |
| status | TEXT | Container status information |
| pid | BIGINT | Identifier of the initial process |
| path | TEXT | Container path |
| config_entrypoint | TEXT | Container entrypoint(s) |
| started_at | TEXT | Container start time as string |
| finished_at | TEXT | Container finish time as string |
| privileged | INTEGER | Is the container privileged |
| security_options | TEXT | List of container security options |
| env_variables | TEXT | Container environmental variables |
| readonly_rootfs | INTEGER | Is the root filesystem mounted as read only |
| cgroup_namespace | TEXT | cgroup namespace |
| ipc_namespace | TEXT | IPC namespace |
| mnt_namespace | TEXT | Mount namespace |
| net_namespace | TEXT | Network namespace |
| pid_namespace | TEXT | PID namespace |
| user_namespace | TEXT | User namespace |
| uts_namespace | TEXT | UTS namespace |

### docker_image_history

**Platforms:** MacOS Linux

Docker image history information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Image ID |
| created | BIGINT | Time of creation as UNIX time |
| size | BIGINT | Size of instruction in bytes |
| created_by | TEXT | Created by instruction |
| tags | TEXT | Comma-separated list of tags |
| comment | TEXT | Instruction comment |

### docker_image_labels

**Platforms:** MacOS Linux

Docker image labels.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Image ID |
| key | TEXT | Label key |
| value | TEXT | Optional label value |

### docker_image_layers

**Platforms:** MacOS Linux

Docker image layers information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Image ID |
| layer_id | TEXT | Layer ID |
| layer_order | INTEGER | Layer Order (1 = base layer) |

### docker_images

**Platforms:** MacOS Linux

Docker images information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Image ID |
| created | BIGINT | Time of creation as UNIX time |
| size_bytes | BIGINT | Size of image in bytes |
| tags | TEXT | Comma-separated list of repository tags |

### docker_info

**Platforms:** MacOS Linux

Docker system information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Docker system ID |
| containers | INTEGER | Total number of containers |
| containers_running | INTEGER | Number of containers currently running |
| containers_paused | INTEGER | Number of containers in paused state |
| containers_stopped | INTEGER | Number of containers in stopped state |
| images | INTEGER | Number of images |
| storage_driver | TEXT | Storage driver |
| memory_limit | INTEGER | 1 if memory limit support is enabled. 0 otherwise |
| swap_limit | INTEGER | 1 if swap limit support is enabled. 0 otherwise |
| kernel_memory | INTEGER | 1 if kernel memory limit support is enabled. 0 otherwise |
| cpu_cfs_period | INTEGER | 1 if CPU Completely Fair Scheduler (CFS) period support is enabled. 0 otherwise |
| cpu_cfs_quota | INTEGER | 1 if CPU Completely Fair Scheduler (CFS) quota support is enabled. 0 otherwise |
| cpu_shares | INTEGER | 1 if CPU share weighting support is enabled. 0 otherwise |
| cpu_set | INTEGER | 1 if CPU set selection support is enabled. 0 otherwise |
| ipv4_forwarding | INTEGER | 1 if IPv4 forwarding is enabled. 0 otherwise |
| bridge_nf_iptables | INTEGER | 1 if bridge netfilter iptables is enabled. 0 otherwise |
| bridge_nf_ip6tables | INTEGER | 1 if bridge netfilter ip6tables is enabled. 0 otherwise |
| oom_kill_disable | INTEGER | 1 if Out-of-memory kill is disabled. 0 otherwise |
| logging_driver | TEXT | Logging driver |
| cgroup_driver | TEXT | Control groups driver |
| kernel_version | TEXT | Kernel version |
| os | TEXT | Operating system |
| os_type | TEXT | Operating system type |
| architecture | TEXT | Hardware architecture |
| cpus | INTEGER | Number of CPUs |
| memory | BIGINT | Total memory |
| http_proxy | TEXT | HTTP proxy |
| https_proxy | TEXT | HTTPS proxy |
| no_proxy | TEXT | Comma-separated list of domain extensions proxy should not be used for |
| name | TEXT | Name of the docker host |
| server_version | TEXT | Server version |
| root_dir | TEXT | Docker root directory |

### docker_network_labels

**Platforms:** MacOS Linux

Docker network labels.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Network ID |
| key | TEXT | Label key |
| value | TEXT | Optional label value |

### docker_networks

**Platforms:** MacOS Linux

Docker networks information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Network ID |
| name | TEXT | Network name |
| driver | TEXT | Network driver |
| created | BIGINT | Time of creation as UNIX time |
| enable_ipv6 | INTEGER | 1 if IPv6 is enabled on this network. 0 otherwise |
| subnet | TEXT | Network subnet |
| gateway | TEXT | Network gateway |

### docker_version

**Platforms:** MacOS Linux

Docker version information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| version | TEXT | Docker version |
| api_version | TEXT | API version |
| min_api_version | TEXT | Minimum API version supported |
| git_commit | TEXT | Docker build git commit |
| go_version | TEXT | Go version |
| os | TEXT | Operating system |
| arch | TEXT | Hardware architecture |
| kernel_version | TEXT | Kernel version |
| build_time | TEXT | Build time |

### docker_volume_labels

**Platforms:** MacOS Linux

Docker volume labels.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Volume name |
| key | TEXT | Label key |
| value | TEXT | Optional label value |

### docker_volumes

**Platforms:** MacOS Linux

Docker volumes information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Volume name |
| driver | TEXT | Volume driver |
| mount_point | TEXT | Mount point |
| type | TEXT | Volume type |

### ec2_instance_metadata

**Platforms:** MacOS Linux Windows

EC2 instance metadata.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| instance_id | TEXT | EC2 instance ID |
| instance_type | TEXT | EC2 instance type |
| architecture | TEXT | Hardware architecture of this EC2 instance |
| region | TEXT | AWS region in which this instance launched |
| availability_zone | TEXT | Availability zone in which this instance launched |
| local_hostname | TEXT | Private IPv4 DNS hostname of the first interface of this instance |
| local_ipv4 | TEXT | Private IPv4 address of the first interface of this instance |
| mac | TEXT | MAC address for the first network interface of this EC2 instance |
| security_groups | TEXT | Comma separated list of security group names |
| iam_arn | TEXT | If there is an IAM role associated with the instance, contains instance profile ARN |
| ami_id | TEXT | AMI ID used to launch this EC2 instance |
| reservation_id | TEXT | ID of the reservation |
| account_id | TEXT | AWS account ID which owns this EC2 instance |
| ssh_public_key | TEXT | SSH public key. Only available if supplied at instance launch time |

### ec2_instance_tags

**Platforms:** MacOS Linux Windows

EC2 instance tag key value pairs.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| instance_id | TEXT | EC2 instance ID |
| key | TEXT | Tag key |
| value | TEXT | Tag value |

### lxd_certificates

**Platforms:** Linux

LXD certificates information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the certificate |
| type | TEXT | Type of the certificate |
| fingerprint | TEXT | SHA256 hash of the certificate |
| certificate | TEXT | Certificate content |

### lxd_cluster

**Platforms:** Linux

LXD cluster information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| server_name | TEXT | Name of the LXD server node |
| enabled | INTEGER | Whether clustering enabled (1) or not (0) on this node |
| member_config_entity | TEXT | Type of configuration parameter for this node |
| member_config_name | TEXT | Name of configuration parameter |
| member_config_key | TEXT | Config key |
| member_config_value | TEXT | Config value |
| member_config_description | TEXT | Config description |

### lxd_cluster_members

**Platforms:** Linux

LXD cluster members information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| server_name | TEXT | Name of the LXD server node |
| url | TEXT | URL of the node |
| database | INTEGER | Whether the server is a database node (1) or not (0) |
| status | TEXT | Status of the node (Online/Offline) |
| message | TEXT | Message from the node (Online/Offline) |

### lxd_images

**Platforms:** Linux

LXD images information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Image ID |
| architecture | TEXT | Target architecture for the image |
| os | TEXT | OS on which image is based |
| release | TEXT | OS release version on which the image is based |
| description | TEXT | Image description |
| aliases | TEXT | Comma-separated list of image aliases |
| filename | TEXT | Filename of the image file |
| size | BIGINT | Size of image in bytes |
| auto_update | INTEGER | Whether the image auto-updates (1) or not (0) |
| cached | INTEGER | Whether image is cached (1) or not (0) |
| public | INTEGER | Whether image is public (1) or not (0) |
| created_at | TEXT | ISO time of image creation |
| expires_at | TEXT | ISO time of image expiration |
| uploaded_at | TEXT | ISO time of image upload |
| last_used_at | TEXT | ISO time for the most recent use of this image in terms of container spawn |
| update_source_server | TEXT | Server for image update |
| update_source_protocol | TEXT | Protocol used for image information update and image import from source server |
| update_source_certificate | TEXT | Certificate for update source server |
| update_source_alias | TEXT | Alias of image at update source server |

### lxd_instance_config

**Platforms:** Linux

LXD instance configuration information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Instance name Required in WHERE clause |
| key | TEXT | Configuration parameter name |
| value | TEXT | Configuration parameter value |

### lxd_instance_devices

**Platforms:** Linux

LXD instance devices information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Instance name Required in WHERE clause |
| device | TEXT | Name of the device |
| device_type | TEXT | Device type |
| key | TEXT | Device info param name |
| value | TEXT | Device info param value |

### lxd_instances

**Platforms:** Linux

LXD instances information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Instance name |
| status | TEXT | Instance state (running, stopped, etc.) |
| stateful | INTEGER | Whether the instance is stateful(1) or not(0) |
| ephemeral | INTEGER | Whether the instance is ephemeral(1) or not(0) |
| created_at | TEXT | ISO time of creation |
| base_image | TEXT | ID of image used to launch this instance |
| architecture | TEXT | Instance architecture |
| os | TEXT | The OS of this instance |
| description | TEXT | Instance description |
| pid | INTEGER | Instance's process ID |
| processes | INTEGER | Number of processes running inside this instance |

### lxd_networks

**Platforms:** Linux

LXD network information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the network |
| type | TEXT | Type of network |
| managed | INTEGER | 1 if network created by LXD, 0 otherwise |
| ipv4_address | TEXT | IPv4 address |
| ipv6_address | TEXT | IPv6 address |
| used_by | TEXT | URLs for containers using this network |
| bytes_received | BIGINT | Number of bytes received on this network |
| bytes_sent | BIGINT | Number of bytes sent on this network |
| packets_received | BIGINT | Number of packets received on this network |
| packets_sent | BIGINT | Number of packets sent on this network |
| hwaddr | TEXT | Hardware address for this network |
| state | TEXT | Network status |
| mtu | INTEGER | MTU size |

### lxd_storage_pools

**Platforms:** Linux

LXD storage pool information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the storage pool |
| driver | TEXT | Storage driver |
| source | TEXT | Storage pool source |
| size | TEXT | Size of the storage pool |
| space_used | BIGINT | Storage space used in bytes |
| space_total | BIGINT | Total available storage space in bytes for this storage pool |
| inodes_used | BIGINT | Number of inodes used |
| inodes_total | BIGINT | Total number of inodes available in this storage pool |

### osquery_events

**Platforms:** MacOS Linux Windows

Information about the event publishers and subscribers.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Event publisher or subscriber name |
| publisher | TEXT | Name of the associated publisher |
| type | TEXT | Either publisher or subscriber |
| subscriptions | INTEGER | Number of subscriptions the publisher received or subscriber used |
| events | INTEGER | Number of events emitted or received since osquery started |
| refreshes | INTEGER | Publisher only: number of runloop restarts |
| active | INTEGER | 1 if the publisher or subscriber is active else 0 |

### osquery_extensions

**Platforms:** MacOS Linux Windows

List of active osquery extensions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uuid | BIGINT | The transient ID assigned for communication |
| name | TEXT | Extension's name |
| version | TEXT | Extension's version |
| sdk_version | TEXT | osquery SDK version used to build the extension |
| path | TEXT | Path of the extension's Thrift connection or library path |
| type | TEXT | SDK extension type: core, extension, or module |

### osquery_flags

**Platforms:** MacOS Linux Windows

Configurable flags that modify osquery's behavior.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Flag name |
| type | TEXT | Flag type |
| description | TEXT | Flag description |
| default_value | TEXT | Flag default value |
| value | TEXT | Flag value |
| shell_only | INTEGER | Is the flag shell only? |

### osquery_info

**Platforms:** MacOS Linux Windows

Top level information about the running version of osquery.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | Process (or thread/handle) ID |
| uuid | TEXT | Unique ID provided by the system |
| instance_id | TEXT | Unique, long-lived ID per instance of osquery |
| version | TEXT | osquery toolkit version |
| config_hash | TEXT | Hash of the working configuration state |
| config_valid | INTEGER | 1 if the config was loaded and considered valid, else 0 |
| extensions | TEXT | osquery extensions status |
| build_platform | TEXT | osquery toolkit build platform |
| build_distro | TEXT | osquery toolkit platform distribution name (os version) |
| start_time | INTEGER | UNIX time in seconds when the process started |
| watcher | INTEGER | Process (or thread/handle) ID of optional watcher process |
| platform_mask | INTEGER | The osquery platform bitmask |

### osquery_packs

**Platforms:** MacOS Linux Windows

Information about the current query packs that are loaded in osquery.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The given name for this query pack |
| platform | TEXT | Platforms this query is supported on |
| version | TEXT | Minimum osquery version that this query will run on |
| shard | INTEGER | Shard restriction limit, 1-100, 0 meaning no restriction |
| discovery_cache_hits | INTEGER | The number of times that the discovery query used cached values since the last time the config was reloaded |
| discovery_executions | INTEGER | The number of times that the discovery queries have been executed since the last time the config was reloaded |
| active | INTEGER | Whether this pack is active (the version, platform and discovery queries match) yes=1, no=0. |

### osquery_registry

**Platforms:** MacOS Linux Windows

List the osquery registry plugins.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| registry | TEXT | Name of the osquery registry |
| name | TEXT | Name of the plugin item |
| owner_uuid | INTEGER | Extension route UUID (0 for core) |
| internal | INTEGER | 1 If the plugin is internal else 0 |
| active | INTEGER | 1 If this plugin is active else 0 |

### osquery_schedule

**Platforms:** MacOS Linux Windows

Information about the current queries that are scheduled in osquery.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The given name for this query |
| query | TEXT | The exact query to run |
| interval | INTEGER | The interval in seconds to run this query, not an exact interval |
| executions | BIGINT | Number of times the query was executed |
| last_executed | BIGINT | UNIX time stamp in seconds of the last completed execution |
| denylisted | INTEGER | 1 if the query is denylisted else 0 |
| output_size | BIGINT | Cumulative total number of bytes generated by the resultant rows of the query |
| wall_time | BIGINT | Total wall time in seconds spent executing (deprecated), hidden=True |
| wall_time_ms | BIGINT | Total wall time in milliseconds spent executing |
| last_wall_time_ms | BIGINT | Wall time in milliseconds of the latest execution |
| user_time | BIGINT | Total user time in milliseconds spent executing |
| last_user_time | BIGINT | User time in milliseconds of the latest execution |
| system_time | BIGINT | Total system time in milliseconds spent executing |
| last_system_time | BIGINT | System time in milliseconds of the latest execution |
| average_memory | BIGINT | Average of the bytes of resident memory left allocated after collecting results |
| last_memory | BIGINT | Resident memory in bytes left allocated after collecting results of the latest execution |

### prometheus_metrics

**Platforms:** MacOS Linux

Retrieve metrics from a Prometheus server.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| target_name | TEXT | Address of prometheus target |
| metric_name | TEXT | Name of collected Prometheus metric |
| metric_value | DOUBLE | Value of collected Prometheus metric |
| timestamp_ms | BIGINT | Unix timestamp of collected data in MS |

### ycloud_instance_metadata

**Platforms:** MacOS Linux Windows

Yandex.Cloud instance metadata.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| instance_id | TEXT | Unique identifier for the VM |
| folder_id | TEXT | Folder identifier for the VM |
| cloud_id | TEXT | Cloud identifier for the VM |
| name | TEXT | Name of the VM |
| description | TEXT | Description of the VM |
| hostname | TEXT | Hostname of the VM |
| zone | TEXT | Availability zone of the VM |
| ssh_public_key | TEXT | SSH public key. Only available if supplied at instance launch time |
| serial_port_enabled | TEXT | Indicates if serial port is enabled for the VM |
| metadata_endpoint | TEXT | Endpoint used to fetch VM metadata |
