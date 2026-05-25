# Knowledge - Reference - OSQuery Network and Connection Tables

_Exact OSQuery network, DNS, interface, route, and socket reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### arp_cache

**Platforms:** MacOS Linux Windows

Address resolution cache, both static and dynamic (from ARP, NDP).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| address | TEXT | IPv4 address target |
| mac | TEXT | MAC address of broadcasted address |
| interface | TEXT | Interface of the network for the MAC |
| permanent | TEXT | 1 for true, 0 for false |

### connectivity

**Platforms:** Windows

Provides the overall system's network state.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| disconnected | INTEGER | True if the all interfaces are not connected to any network |
| ipv4_no_traffic | INTEGER | True if any interface is connected via IPv4, but has seen no traffic |
| ipv6_no_traffic | INTEGER | True if any interface is connected via IPv6, but has seen no traffic |
| ipv4_subnet | INTEGER | True if any interface is connected to the local subnet via IPv4 |
| ipv4_local_network | INTEGER | True if any interface is connected to a routed network via IPv4 |
| ipv4_internet | INTEGER | True if any interface is connected to the Internet via IPv4 |
| ipv6_subnet | INTEGER | True if any interface is connected to the local subnet via IPv6 |
| ipv6_local_network | INTEGER | True if any interface is connected to a routed network via IPv6 |
| ipv6_internet | INTEGER | True if any interface is connected to the Internet via IPv6 |

### curl

**Platforms:** MacOS Linux Windows

Perform an http request and return stats about it.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| url | TEXT | The url for the request Required in WHERE clause |
| method | TEXT | The HTTP method for the request |
| user_agent | TEXT | The user-agent string to use for the request |
| response_code | INTEGER | The HTTP status code for the response |
| round_trip_time | BIGINT | Time taken to complete the request |
| bytes | BIGINT | Number of bytes in the response |
| result | TEXT | The HTTP response body |

### curl_certificate

**Platforms:** MacOS Linux Windows

Inspect TLS certificates by connecting to input hostnames.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| hostname | TEXT | Hostname to CURL (domain[:port], e.g. osquery.io) Required in WHERE clause |
| common_name | TEXT | Common name of company issued to |
| organization | TEXT | Organization issued to |
| organization_unit | TEXT | Organization unit issued to |
| serial_number | TEXT | Certificate serial number |
| issuer_common_name | TEXT | Issuer common name |
| issuer_organization | TEXT | Issuer organization |
| issuer_organization_unit | TEXT | Issuer organization unit |
| valid_from | TEXT | Period of validity start date |
| valid_to | TEXT | Period of validity end date |
| sha256_fingerprint | TEXT | SHA-256 fingerprint |
| sha1_fingerprint | TEXT | SHA1 fingerprint |
| version | INTEGER | Version Number |
| signature_algorithm | TEXT | Signature Algorithm |
| signature | TEXT | Signature |
| subject_key_identifier | TEXT | Subject Key Identifier |
| authority_key_identifier | TEXT | Authority Key Identifier |
| key_usage | TEXT | Usage of key in certificate |
| extended_key_usage | TEXT | Extended usage of key in certificate |
| policies | TEXT | Certificate Policies |
| subject_alternative_names | TEXT | Subject Alternative Name |
| issuer_alternative_names | TEXT | Issuer Alternative Name |
| info_access | TEXT | Authority Information Access |
| subject_info_access | TEXT | Subject Information Access |
| policy_mappings | TEXT | Policy Mappings |
| has_expired | INTEGER | 1 if the certificate has expired, 0 otherwise |
| basic_constraint | TEXT | Basic Constraints |
| name_constraints | TEXT | Name Constraints |
| policy_constraints | TEXT | Policy Constraints |
| dump_certificate | INTEGER | Set this value to '1' to dump certificate |
| timeout | INTEGER | Set this value to the timeout in seconds to complete the TLS handshake (default 4s, use 0 for no timeout) |
| pem | TEXT | Certificate PEM format |

### dns_cache

**Platforms:** Windows

Enumerate the DNS cache using the undocumented DnsGetCacheDataTable function in dnsapi.dll.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | DNS record name |
| type | TEXT | DNS record type |
| flags | INTEGER | DNS record flags |

### dns_lookup_events

**Platforms:** Windows

**Table Type:** EVENTED TABLE

DNS lookups performed through the Windows DNS stack.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| eid | INTEGER | Event ID |
| time | BIGINT | Event timestamp in Unix format |
| time_windows | BIGINT | Event timestamp in Windows format |
| datetime | TEXT | Event timestamp in DATETIME format |
| pid | BIGINT | Process ID of process making the lookup |
| path | TEXT | Path to binary of process making the lookup (sometimes unavailable for very short-lived processes) |
| username | TEXT | User rights - primary token username |
| name | TEXT | Name being queried in lookup |
| type | TEXT | DNS record type of lookup as string |
| type_id | INTEGER | Integer type ID for record type |
| status | INTEGER | Response status code |
| response | TEXT | Results returned by lookup |

### dns_resolvers

**Platforms:** MacOS Linux

Resolvers used by this host. Note: On Windows this data is available in the interface_details table.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Address type index or order |
| type | TEXT | Address type: sortlist, nameserver, search |
| address | TEXT | Resolver IP/IPv6 address |
| netmask | TEXT | Address (sortlist) netmask length |
| options | BIGINT | Resolver options |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### etc_hosts

**Platforms:** MacOS Linux Windows

Line-parsed /etc/hosts.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| address | TEXT | IP address mapping |
| hostnames | TEXT | Raw hosts mapping |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### etc_protocols

**Platforms:** MacOS Linux Windows

Line-parsed /etc/protocols.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Protocol name |
| number | INTEGER | Protocol number |
| alias | TEXT | Protocol alias |
| comment | TEXT | Comment with protocol description |

### etc_services

**Platforms:** MacOS Linux Windows

Line-parsed /etc/services.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Service name |
| port | INTEGER | Service port number |
| protocol | TEXT | Transport protocol (TCP/UDP) |
| aliases | TEXT | Optional space separated list of other names for a service |
| comment | TEXT | Optional comment for a service. |

### interface_addresses

**Platforms:** MacOS Linux Windows

Network interfaces and relevant metadata.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| interface | TEXT | Interface name |
| address | TEXT | Specific address for interface |
| mask | TEXT | Interface netmask |
| broadcast | TEXT | Broadcast address for the interface |
| point_to_point | TEXT | PtP address for the interface |
| type | TEXT | Type of address. One of dhcp, manual, auto, other, unknown |
| friendly_name | TEXT | The friendly display name of the interface. |

### interface_details

**Platforms:** MacOS Linux Windows

Detailed information and stats of network interfaces.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| interface | TEXT | Interface name |
| mac | TEXT | MAC of interface (optional) |
| type | INTEGER | Interface type (includes virtual) |
| mtu | INTEGER | Network MTU |
| metric | INTEGER | Metric based on the speed of the interface |
| flags | INTEGER | Flags (netdevice) for the device |
| ipackets | BIGINT | Input packets |
| opackets | BIGINT | Output packets |
| ibytes | BIGINT | Input bytes |
| obytes | BIGINT | Output bytes |
| ierrors | BIGINT | Input errors |
| oerrors | BIGINT | Output errors |
| idrops | BIGINT | Input drops |
| odrops | BIGINT | Output drops |
| collisions | BIGINT | Packet Collisions detected |
| last_change | BIGINT | Time of last device modification (optional) |
| link_speed | BIGINT | Interface speed in Mb/s |
| pci_slot | TEXT | PCI slot number |
| friendly_name | TEXT | The friendly display name of the interface. |
| description | TEXT | Short description of the object a one-line string. |
| manufacturer | TEXT | Name of the network adapter's manufacturer. |
| connection_id | TEXT | Name of the network connection as it appears in the Network Connections Control Panel program. |
| connection_status | TEXT | State of the network adapter connection to the network. |
| enabled | INTEGER | Indicates whether the adapter is enabled or not. |
| physical_adapter | INTEGER | Indicates whether the adapter is a physical or a logical adapter. |
| speed | INTEGER | Estimate of the current bandwidth in bits per second. |
| service | TEXT | The name of the service the network adapter uses. |
| dhcp_enabled | INTEGER | If TRUE, the dynamic host configuration protocol (DHCP) server automatically assigns an IP address to the computer system when establishing a network connection. |
| dhcp_lease_expires | TEXT | Expiration date and time for a leased IP address that was assigned to the computer by the dynamic host configuration protocol (DHCP) server. |
| dhcp_lease_obtained | TEXT | Date and time the lease was obtained for the IP address assigned to the computer by the dynamic host configuration protocol (DHCP) server. |
| dhcp_server | TEXT | IP address of the dynamic host configuration protocol (DHCP) server. |
| dns_domain | TEXT | Organization name followed by a period and an extension that indicates the type of organization, such as 'microsoft.com'. |
| dns_domain_suffix_search_order | TEXT | Array of DNS domain suffixes to be appended to the end of host names during name resolution. |
| dns_host_name | TEXT | Host name used to identify the local computer for authentication by some utilities. |
| dns_server_search_order | TEXT | Array of server IP addresses to be used in querying for DNS servers. |

### interface_ipv6

**Platforms:** MacOS Linux

IPv6 configuration and stats of network interfaces.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| interface | TEXT | Interface name |
| hop_limit | INTEGER | Current Hop Limit |
| forwarding_enabled | INTEGER | Enable IP forwarding |
| redirect_accept | INTEGER | Accept ICMP redirect messages |
| rtadv_accept | INTEGER | Accept ICMP Router Advertisement |

### iptables

**Platforms:** Linux

Linux IP packet filtering and NAT tool.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| filter_name | TEXT | Packet matching filter table name. |
| chain | TEXT | Size of module content. |
| policy | TEXT | Policy that applies for this rule. |
| target | TEXT | Target that applies for this rule. |
| protocol | INTEGER | Protocol number identification. |
| src_port | TEXT | Protocol source port(s). |
| dst_port | TEXT | Protocol destination port(s). |
| src_ip | TEXT | Source IP address. |
| src_mask | TEXT | Source IP address mask. |
| iniface | TEXT | Input interface for the rule. |
| iniface_mask | TEXT | Input interface mask for the rule. |
| dst_ip | TEXT | Destination IP address. |
| dst_mask | TEXT | Destination IP address mask. |
| outiface | TEXT | Output interface for the rule. |
| outiface_mask | TEXT | Output interface mask for the rule. |
| match | TEXT | Matching rule that applies. |
| packets | INTEGER | Number of matching packets for this rule. |
| bytes | INTEGER | Number of matching bytes for this rule. |

### listening_ports

**Platforms:** MacOS Linux Windows

Processes with listening (bound) network sockets/ports.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | Process (or thread) ID |
| port | INTEGER | Transport layer port |
| protocol | INTEGER | Transport protocol (TCP/UDP) |
| family | INTEGER | Network protocol (IPv4, IPv6) |
| address | TEXT | Specific address for bind |
| fd | BIGINT | Socket file descriptor number |
| socket | BIGINT | Socket handle or inode number |
| path | TEXT | Path for UNIX domain sockets |
| net_namespace | TEXT | The inode number of the network namespace |

### pipes

**Platforms:** Windows

Named and Anonymous pipes.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | BIGINT | Process ID of the process to which the pipe belongs |
| name | TEXT | Name of the pipe |
| instances | INTEGER | Number of instances of the named pipe |
| max_instances | INTEGER | The maximum number of instances creatable for this pipe |
| flags | TEXT | The flags indicating whether this pipe connection is a server or client end, and if the pipe for sending messages or bytes |

### routes

**Platforms:** MacOS Linux Windows

The active route table for the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| destination | TEXT | Destination IP address |
| netmask | INTEGER | Netmask length |
| gateway | TEXT | Route gateway |
| source | TEXT | Route source |
| flags | INTEGER | Flags to describe route |
| interface | TEXT | Route local interface |
| mtu | INTEGER | Maximum Transmission Unit for the route |
| metric | INTEGER | Cost of route. Lowest is preferred |
| type | TEXT | Type of route |
| hopcount | INTEGER | Max hops expected |

### socket_events

**Platforms:** MacOS Linux

**Table Type:** EVENTED TABLE

Track network socket bind, connect, and accepts.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| action | TEXT | The socket action (bind, connect, accept) |
| pid | BIGINT | Process (or thread) ID |
| path | TEXT | Path of executed file |
| fd | TEXT | The file description for the process socket |
| auid | BIGINT | Audit User ID |
| family | INTEGER | The Internet protocol family ID |
| protocol | INTEGER | The network protocol ID |
| local_address | TEXT | Local address associated with socket |
| remote_address | TEXT | Remote address associated with socket |
| local_port | INTEGER | Local network protocol port number |
| remote_port | INTEGER | Remote network protocol port number |
| socket | TEXT | The local path (UNIX domain socket only) |
| time | BIGINT | Time of execution in UNIX time |
| uptime | BIGINT | Time of execution in system uptime |
| eid | TEXT | Event ID |
| success | INTEGER | Deprecated. Use the 'status' column instead |
| status | TEXT | Either 'succeeded', 'failed', 'in_progress' (connect() on non-blocking socket) or 'no_client' (null accept() on non-blocking socket) |

### wifi_networks

**Platforms:** MacOS

macOS known/remembered Wi-Fi networks list.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| ssid | TEXT | SSID octets of the network |
| network_name | TEXT | Name of the network |
| security_type | TEXT | Type of security on this network |
| last_connected | INTEGER | Last time this network was connected to as a unix_time (max of last_connected_automatic and last_connected_manual, if available) |
| last_connected_automatic | INTEGER | Last time this network was automatically connected to by the system as a unix_time |
| last_connected_manual | INTEGER | Last time this network was manually connected to by the user as a unix_time |
| passpoint | INTEGER | 1 if Passpoint is supported, 0 otherwise |
| possibly_hidden | INTEGER | 1 if network is possibly a hidden network, 0 otherwise |
| roaming | INTEGER | 1 if roaming is supported, 0 otherwise |
| roaming_profile | TEXT | Describe the roaming profile, usually one of Single, Dual or Multi |
| auto_login | INTEGER | 1 if auto login is enabled, 0 otherwise |
| temporarily_disabled | INTEGER | 1 if this network is temporarily disabled, 0 otherwise |
| disabled | INTEGER | 1 if this network is disabled, 0 otherwise |
| add_reason | TEXT | Shows why this network was added, via menubar or command line or something else |
| added_at | INTEGER | Time this network was added as a unix_time |
| captive_portal | INTEGER | 1 if this network has a captive portal, 0 otherwise |
| captive_login_date | INTEGER | Time this network logged in to a captive portal as unix_time |
| was_captive_network | INTEGER | 1 if this network was previously a captive network, 0 otherwise |
| auto_join | INTEGER | 1 if this network set to join automatically, 0 otherwise |
| personal_hotspot | INTEGER | 1 if this network is a personal hotspot, 0 otherwise |

### wifi_status

**Platforms:** MacOS

macOS current WiFi status. This table requires Full Disk Access (FDA) permission to retrieve network_name.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| interface | TEXT | Name of the interface |
| ssid | TEXT | SSID octets of the network |
| bssid | TEXT | The current basic service set identifier |
| network_name | TEXT | Name of the network |
| country_code | TEXT | The country code (ISO/IEC 3166-1:1997) for the network |
| security_type | TEXT | Type of security on this network |
| rssi | INTEGER | The current received signal strength indication (dbm) |
| noise | INTEGER | The current noise measurement (dBm) |
| channel | INTEGER | Channel number |
| channel_width | INTEGER | Channel width |
| channel_band | INTEGER | Channel band |
| transmit_rate | TEXT | The current transmit rate |
| mode | TEXT | The current operating mode for the Wi-Fi interface |

### wifi_survey

**Platforms:** MacOS

Scan for nearby WiFi networks.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| interface | TEXT | Name of the interface |
| ssid | TEXT | SSID octets of the network |
| bssid | TEXT | The current basic service set identifier |
| network_name | TEXT | Name of the network |
| country_code | TEXT | The country code (ISO/IEC 3166-1:1997) for the network |
| rssi | INTEGER | The current received signal strength indication (dbm) |
| noise | INTEGER | The current noise measurement (dBm) |
| channel | INTEGER | Channel number |
| channel_width | INTEGER | Channel width |
| channel_band | INTEGER | Channel band |
