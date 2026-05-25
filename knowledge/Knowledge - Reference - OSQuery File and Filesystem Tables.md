# Knowledge - Reference - OSQuery File and Filesystem Tables

_Exact OSQuery file, hash, filesystem, mount, and file-event reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### block_devices

**Platforms:** MacOS Linux

Block (buffered access) device file nodes: disks, ramdisks, and DMG containers.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Block device name |
| parent | TEXT | Block device parent name |
| vendor | TEXT | Block device vendor string |
| model | TEXT | Block device model string identifier |
| serial | TEXT | Disk serial number |
| size | BIGINT | Block device size in blocks |
| block_size | INTEGER | Block size in bytes |
| uuid | TEXT | Block device Universally Unique Identifier |
| type | TEXT | Block device type string |
| label | TEXT | Block device label string |

### deb_package_files

**Platforms:** Linux

Installed files from DEB packages that are currently installed on the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package | TEXT | DEB package name |
| path | TEXT | File path within the package |
| admindir | TEXT | libdpkg admindir. Defaults to /var/lib/dpkg |

### device_file

**Platforms:** MacOS Linux

Similar to the file table, but use TSK and allow block address access.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device | TEXT | Absolute file path to device node Required in WHERE clause |
| partition | TEXT | A partition number Required in WHERE clause |
| path | TEXT | A logical path within the device node |
| filename | TEXT | Name portion of file path |
| inode | BIGINT | Filesystem inode number |
| uid | BIGINT | Owning user ID |
| gid | BIGINT | Owning group ID |
| mode | TEXT | Permission bits |
| size | BIGINT | Size of file in bytes |
| block_size | INTEGER | Block size of filesystem |
| atime | BIGINT | Last access time |
| mtime | BIGINT | Last modification time |
| ctime | BIGINT | Creation time |
| hard_links | INTEGER | Number of hard links |
| type | TEXT | File status |

### device_hash

**Platforms:** MacOS Linux

Similar to the hash table, but use TSK and allow block address access.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device | TEXT | Absolute file path to device node Required in WHERE clause |
| partition | TEXT | A partition number Required in WHERE clause |
| inode | BIGINT | Filesystem inode number Required in WHERE clause |
| md5 | TEXT | MD5 hash of provided inode data |
| sha1 | TEXT | SHA1 hash of provided inode data |
| sha256 | TEXT | SHA256 hash of provided inode data |

### device_partitions

**Platforms:** MacOS Linux

Use TSK to enumerate details about partitions on a disk device.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device | TEXT | Absolute file path to device node Required in WHERE clause |
| partition | INTEGER | A partition number or description |
| label | TEXT | The partition name as stored in the partition table |
| type | TEXT | Filesystem type if recognized, otherwise, 'meta', 'normal', or 'unallocated' |
| offset | BIGINT | Byte offset from the start of the volume |
| blocks_size | BIGINT | Byte size of each block |
| blocks | BIGINT | Number of blocks |
| inodes | BIGINT | Number of meta nodes |
| flags | INTEGER | Value that describes the partition (TSK_VS_PART_FLAG_ENUM) |

### deviceguard_status

**Platforms:** Windows

Retrieve DeviceGuard info of the machine.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| version | TEXT | The version number of the Device Guard build. |
| instance_identifier | TEXT | The instance ID of Device Guard. |
| vbs_status | TEXT | The status of the virtualization based security settings. Returns UNKNOWN if an error is encountered. |
| code_integrity_policy_enforcement_status | TEXT | The status of the code integrity policy enforcement settings. Returns UNKNOWN if an error is encountered. |
| configured_security_services | TEXT | The list of configured Device Guard services. Returns UNKNOWN if an error is encountered. |
| running_security_services | TEXT | The list of running Device Guard services. Returns UNKNOWN if an error is encountered. |
| umci_policy_status | TEXT | The status of the User Mode Code Integrity security settings. Returns UNKNOWN if an error is encountered. |

### disk_events

**Platforms:** MacOS

**Table Type:** EVENTED TABLE

Track DMG disk image events (appearance/disappearance) when opened.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| action | TEXT | Appear or disappear |
| path | TEXT | Path of the DMG file accessed |
| name | TEXT | Disk event name |
| device | TEXT | Disk event BSD name |
| uuid | TEXT | UUID of the volume inside DMG if available |
| size | BIGINT | Size of partition in bytes |
| ejectable | INTEGER | 1 if ejectable, 0 if not |
| mountable | INTEGER | 1 if mountable, 0 if not |
| writable | INTEGER | 1 if writable, 0 if not |
| content | TEXT | Disk event content |
| media_name | TEXT | Disk event media name string |
| vendor | TEXT | Disk event vendor string |
| filesystem | TEXT | Filesystem if available |
| checksum | TEXT | UDIF Master checksum if available (CRC32) |
| time | BIGINT | Time of appearance/disappearance in UNIX time |
| eid | TEXT | Event ID |

### disk_info

**Platforms:** Windows

Retrieve basic information about the physical disks of a system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| partitions | INTEGER | Number of detected partitions on disk. |
| disk_index | INTEGER | Physical drive number of the disk. |
| type | TEXT | The interface type of the disk. |
| id | TEXT | The unique identifier of the drive on the system. |
| pnp_device_id | TEXT | The unique identifier of the drive on the system. |
| disk_size | BIGINT | Size of the disk. |
| manufacturer | TEXT | The manufacturer of the disk. |
| hardware_model | TEXT | Hard drive model. |
| name | TEXT | The label of the disk object. |
| serial | TEXT | The serial number of the disk. |
| description | TEXT | The OS's description of the disk. |

### extended_attributes

**Platforms:** MacOS Linux

Returns the extended attributes for files (similar to Windows ADS).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Absolute file path Required in WHERE clause |
| directory | TEXT | Directory of file(s) Required in WHERE clause |
| key | TEXT | Name of the value generated from the extended attribute |
| value | TEXT | The parsed information from the attribute |
| base64 | INTEGER | 1 if the value is base64 encoded else 0 |

### file

**Platforms:** MacOS Linux Windows

Interactive filesystem attributes and metadata.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Absolute file path Required in WHERE clause |
| directory | TEXT | Directory of file(s) Required in WHERE clause |
| filename | TEXT | Name portion of file path |
| inode | BIGINT | Filesystem inode number |
| uid | BIGINT | Owning user ID |
| gid | BIGINT | Owning group ID |
| mode | TEXT | Permission bits |
| device | BIGINT | Device ID (optional) |
| size | BIGINT | Size of file in bytes |
| block_size | INTEGER | Block size of filesystem |
| atime | BIGINT | Last access time |
| mtime | BIGINT | Last modification time |
| ctime | BIGINT | Last status change time |
| btime | BIGINT | (B)irth or (cr)eate time |
| hard_links | INTEGER | Number of hard links |
| symlink | INTEGER | 1 if the path is a symlink, otherwise 0 |
| type | TEXT | File status |
| symlink_target_path | TEXT | Full path of the symlink target if any |
| attributes | TEXT | File attrib string. See: https://ss64.com/nt/attrib.html |
| volume_serial | TEXT | Volume serial number |
| file_id | TEXT | file ID |
| file_version | TEXT | File version |
| product_version | TEXT | File product version |
| original_filename | TEXT | (Executable files only) Original filename |
| shortcut_target_path | TEXT | Full path to the file the shortcut points to |
| shortcut_target_type | TEXT | Display name for the target type |
| shortcut_target_location | TEXT | Folder name where the shortcut target resides |
| shortcut_start_in | TEXT | Full path to the working directory to use when executing the shortcut target |
| shortcut_run | TEXT | Window mode the target of the shortcut should be run in |
| shortcut_comment | TEXT | Comment on the shortcut |
| bsd_flags | TEXT | The BSD file flags (chflags). Possible values: NODUMP, UF_IMMUTABLE, UF_APPEND, OPAQUE, HIDDEN, ARCHIVED, SF_IMMUTABLE, SF_APPEND |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| mount_namespace_id | TEXT | Mount namespace id |

### hash

**Platforms:** MacOS Linux Windows

Filesystem hash data.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Must provide a path or directory Required in WHERE clause |
| directory | TEXT | Must provide a path or directory Required in WHERE clause |
| md5 | TEXT | MD5 hash of provided filesystem data |
| sha1 | TEXT | SHA1 hash of provided filesystem data |
| sha256 | TEXT | SHA256 hash of provided filesystem data |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| mount_namespace_id | TEXT | Mount namespace id |

### magic

**Platforms:** MacOS Linux

Magic number recognition library table.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Absolute path to target file Required in WHERE clause |
| magic_db_files | TEXT | Colon(:) separated list of files where the magic db file can be found. By default one of the following is used: /usr/share/file/magic/magic, /usr/share/misc/magic or /usr/share/misc/magic.mgc |
| data | TEXT | Magic number data from libmagic |
| mime_type | TEXT | MIME type data from libmagic |
| mime_encoding | TEXT | MIME encoding data from libmagic |

### md_devices

**Platforms:** Linux

Software RAID array settings.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device_name | TEXT | md device name |
| status | TEXT | Current state of the array |
| raid_level | INTEGER | Current raid level of the array |
| size | BIGINT | size of the array in blocks |
| chunk_size | BIGINT | chunk size in bytes |
| raid_disks | INTEGER | Number of configured RAID disks in array |
| nr_raid_disks | INTEGER | Number of partitions or disk devices to comprise the array |
| working_disks | INTEGER | Number of working disks in array |
| active_disks | INTEGER | Number of active disks in array |
| failed_disks | INTEGER | Number of failed disks in array |
| spare_disks | INTEGER | Number of idle disks in array |
| superblock_state | TEXT | State of the superblock |
| superblock_version | TEXT | Version of the superblock |
| superblock_update_time | BIGINT | Unix timestamp of last update |
| bitmap_on_mem | TEXT | Pages allocated in in-memory bitmap, if enabled |
| bitmap_chunk_size | TEXT | Bitmap chunk size |
| bitmap_external_file | TEXT | External referenced bitmap file |
| recovery_progress | TEXT | Progress of the recovery activity |
| recovery_finish | TEXT | Estimated duration of recovery activity |
| recovery_speed | TEXT | Speed of recovery activity |
| resync_progress | TEXT | Progress of the resync activity |
| resync_finish | TEXT | Estimated duration of resync activity |
| resync_speed | TEXT | Speed of resync activity |
| reshape_progress | TEXT | Progress of the reshape activity |
| reshape_finish | TEXT | Estimated duration of reshape activity |
| reshape_speed | TEXT | Speed of reshape activity |
| check_array_progress | TEXT | Progress of the check array activity |
| check_array_finish | TEXT | Estimated duration of the check array activity |
| check_array_speed | TEXT | Speed of the check array activity |
| unused_devices | TEXT | Unused devices |
| other | TEXT | Other information associated with array from /proc/mdstat |

### md_drives

**Platforms:** Linux

Drive devices used for Software RAID.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| md_device_name | TEXT | md device name |
| drive_name | TEXT | Drive device name |
| slot | INTEGER | Slot position of disk |
| state | TEXT | State of the drive |

### md_personalities

**Platforms:** Linux

Software RAID setting supported by the kernel.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of personality supported by kernel |

### mdfind

**Platforms:** MacOS

Run searches against the spotlight database.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path of the file returned from spotlight |
| query | TEXT | The query that was run to find the file Required in WHERE clause |

### mdls

**Platforms:** MacOS

Query file metadata in the Spotlight database.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path of the file Required in WHERE clause |
| key | TEXT | Name of the metadata key |
| value | TEXT | Value stored in the metadata key |
| valuetype | TEXT | CoreFoundation type of data stored in value |

### mounts

**Platforms:** MacOS Linux

System mounted devices and filesystems (not process specific).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device | TEXT | Mounted device |
| device_alias | TEXT | Mounted device alias |
| path | TEXT | Mounted device path |
| type | TEXT | Mounted device type |
| blocks_size | BIGINT | Block size in bytes |
| blocks | BIGINT | Mounted device used blocks |
| blocks_free | BIGINT | Mounted device blocks available to root users, a superset of blocks_available |
| blocks_available | BIGINT | Mounted device blocks available to non-root users |
| inodes | BIGINT | Mounted device used inodes |
| inodes_free | BIGINT | Mounted device free inodes |
| flags | TEXT | Mounted device flags |

### nfs_shares

**Platforms:** MacOS

NFS shares exported by the host.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| share | TEXT | Filesystem path to the share |
| options | TEXT | Options string set on the export share |
| readonly | INTEGER | 1 if the share is exported readonly else 0 |

### ntfs_acl_permissions

**Platforms:** Windows

Retrieve NTFS ACL permission information for files and directories.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path to the file or directory. Required in WHERE clause |
| type | TEXT | Type of access mode for the access control entry. |
| principal | TEXT | User or group to which the ACE applies. |
| access | TEXT | Specific permissions that indicate the rights described by the ACE. |
| inherited_from | TEXT | The inheritance policy of the ACE. |

### ntfs_journal_events

**Platforms:** Windows

**Table Type:** EVENTED TABLE

Track time/action changes to files specified in configuration data.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| action | TEXT | Change action (Write, Delete, etc) |
| category | TEXT | The category that the event originated from |
| old_path | TEXT | Old path (renames only) |
| path | TEXT | Path |
| record_timestamp | TEXT | Journal record timestamp |
| record_usn | TEXT | The update sequence number that identifies the journal record |
| node_ref_number | TEXT | The ordinal that associates a journal record with a filename |
| parent_ref_number | TEXT | The ordinal that associates a journal record with a filename's parent directory |
| drive_letter | TEXT | The drive letter identifying the source journal |
| file_attributes | TEXT | File attributes |
| partial | BIGINT | Set to 1 if either path or old_path only contains the file or folder name |
| time | BIGINT | Time of file event |
| eid | TEXT | Event ID |

### package_bom

**Platforms:** MacOS

macOS package bill of materials (BOM) file list.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| filepath | TEXT | Package file or directory |
| uid | INTEGER | Expected user of file or directory |
| gid | INTEGER | Expected group of file or directory |
| mode | INTEGER | Expected permissions |
| size | BIGINT | Expected file size |
| modified_time | INTEGER | Timestamp the file was installed |
| path | TEXT | Path of package bom Required in WHERE clause |

### package_install_history

**Platforms:** MacOS

macOS package install history.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package_id | TEXT | Label packageIdentifiers |
| time | INTEGER | Label date as UNIX timestamp |
| name | TEXT | Package display name |
| version | TEXT | Package display version |
| source | TEXT | Install source: usually the installer process name |
| content_type | TEXT | Package content_type (optional) |

### plist

**Platforms:** MacOS

Read and parse a plist file.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| key | TEXT | Preference top-level key |
| subkey | TEXT | Intermediate key path, includes lists/dicts |
| value | TEXT | String value of most CF types |
| path | TEXT | (required) read preferences from a plist Required in WHERE clause |

### quicklook_cache

**Platforms:** MacOS

Files and thumbnails within macOS's Quicklook Cache.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path of file |
| rowid | INTEGER | Quicklook file rowid key |
| fs_id | TEXT | Quicklook file fs_id key |
| volume_id | INTEGER | Parsed volume ID from fs_id |
| inode | INTEGER | Parsed file ID (inode) from fs_id |
| mtime | INTEGER | Parsed version date field |
| size | BIGINT | Parsed version size field |
| label | TEXT | Parsed version 'gen' field |
| last_hit_date | INTEGER | Apple date format for last thumbnail cache hit |
| hit_count | TEXT | Number of cache hits on thumbnail |
| icon_mode | BIGINT | Thumbnail icon mode |
| cache_path | TEXT | Path to cache data |

### recent_files

**Platforms:** Windows

Recently files (as displayed in Start Menu or File Explorer).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local user ID |
| filename | TEXT | The name of the file |
| path | TEXT | The full path of the file |
| type | TEXT | Display type for the file |
| mtime | BIGINT | Last modification time of the shortcut (usually corresponds to last opened time for the file) |
| shortcut_path | TEXT | Path to the shortcut where Windows stores the recent file data |

### rpm_package_files

**Platforms:** Linux

Installed files from RPM packages that are currently installed on the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package | TEXT | RPM package name |
| path | TEXT | File path within the package |
| username | TEXT | File default username from info DB |
| groupname | TEXT | File default groupname from info DB |
| mode | TEXT | File permissions mode from info DB |
| size | BIGINT | Expected file size in bytes from RPM info DB |
| sha256 | TEXT | SHA256 file digest from RPM info DB |

### shared_memory

**Platforms:** Linux

OS shared memory regions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| shmid | INTEGER | Shared memory segment ID |
| owner_uid | BIGINT | User ID of owning process |
| creator_uid | BIGINT | User ID of creator process |
| pid | BIGINT | Process ID to last use the segment |
| creator_pid | BIGINT | Process ID that created the segment |
| atime | BIGINT | Attached time |
| dtime | BIGINT | Detached time |
| ctime | BIGINT | Changed time |
| permissions | TEXT | Memory segment permissions |
| size | BIGINT | Size in bytes |
| attached | INTEGER | Number of attached processes |
| status | TEXT | Destination/attach status |
| locked | INTEGER | 1 if segment is locked else 0 |

### shared_resources

**Platforms:** Windows

Displays shared resources on a computer system running Windows. This may be a disk drive, printer, interprocess communication, or other sharable device.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| description | TEXT | A textual description of the object |
| install_date | TEXT | Indicates when the object was installed. Lack of a value does not indicate that the object is not installed. |
| status | TEXT | String that indicates the current status of the object. |
| allow_maximum | INTEGER | Number of concurrent users for this resource has been limited. If True, the value in the MaximumAllowed property is ignored. |
| maximum_allowed | BIGINT | Limit on the maximum number of users allowed to use this resource concurrently. The value is only valid if the AllowMaximum property is set to FALSE. |
| name | TEXT | Alias given to a path set up as a share on a computer system running Windows. |
| path | TEXT | Local path of the Windows share. |
| type | BIGINT | Type of resource being shared. Types include: disk drives, print queues, interprocess communications (IPC), and general devices. |
| type_name | TEXT | Human readable value for the 'type' column |

### smbios_tables

**Platforms:** MacOS Linux

BIOS (DMI) structure common details and content.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| number | INTEGER | Table entry number |
| type | INTEGER | Table entry type |
| description | TEXT | Table entry description |
| handle | INTEGER | Table entry handle |
| header_size | INTEGER | Header size in bytes |
| size | INTEGER | Table entry size in bytes |
| md5 | TEXT | MD5 hash of table entry |

### yara_file

**Platforms:** MacOS Linux Windows

**Status:** New

Triggers one-off YARA query for files at the specified path. Additionally requires one of `sig_group`, `sigfile`, or `sigrule`.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | The path scanned Required in WHERE clause |
| matches | TEXT | List of YARA matches |
| count | INTEGER | Number of YARA matches |
| sig_group | TEXT | Signature group used |
| sigfile | TEXT | Signature file used |
| sigrule | TEXT | Signature strings used |
| strings | TEXT | Matching strings |
| tags | TEXT | Matching tags |
| sigurl | TEXT | Signature url |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
