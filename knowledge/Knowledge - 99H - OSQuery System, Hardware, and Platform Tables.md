# Knowledge - 99H - OSQuery System, Hardware, and Platform Tables

_Exact OSQuery system, OS, hardware, memory, uptime, and platform reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### acpi_tables

**Platforms:** MacOS Linux

Firmware ACPI functional table common metadata and content.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | ACPI table name |
| size | INTEGER | Size of compiled table data |
| md5 | TEXT | MD5 hash of table content |

### augeas

**Platforms:** MacOS Linux

Configuration files parsed by augeas.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| node | TEXT | The node path of the configuration item |
| value | TEXT | The value of the configuration item |
| label | TEXT | The label of the configuration item |
| path | TEXT | The path to the configuration file |

### battery

**Platforms:** MacOS Windows

Provides information about the internal battery of a laptop. Note: On Windows, columns with Ah or mAh units assume that the battery is 12V.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| manufacturer | TEXT | The battery manufacturer's name |
| model | TEXT | The battery's model number |
| serial_number | TEXT | The battery's serial number |
| cycle_count | INTEGER | The number of charge/discharge cycles |
| state | TEXT | One of the following: "AC Power" indicates the battery is connected to an external power source, "Battery Power" indicates that the battery is drawing internal power, "Off Line" indicates the battery is off-line or no longer connected |
| charging | INTEGER | 1 if the battery is currently being charged by a power source. 0 otherwise |
| charged | INTEGER | 1 if the battery is currently completely charged. 0 otherwise |
| designed_capacity | INTEGER | The battery's designed capacity in mAh |
| max_capacity | INTEGER | The battery's actual capacity when it is fully charged in mAh |
| current_capacity | INTEGER | The battery's current capacity (level of charge) in mAh |
| percent_remaining | INTEGER | The percentage of battery remaining before it is drained |
| amperage | INTEGER | The current amperage in/out of the battery in mA (positive means charging, negative means discharging) |
| voltage | INTEGER | The battery's current voltage in mV |
| minutes_until_empty | INTEGER | The number of minutes until the battery is fully depleted. This value is -1 if this time is still being calculated |
| minutes_to_full_charge | INTEGER | The number of minutes until the battery is fully charged. This value is -1 if this time is still being calculated. On Windows this is calculated from the charge rate and capacity and may not agree with the number reported in "Power & Battery" |
| chemistry | TEXT | The battery chemistry type (eg. LiP). Some possible values are documented in https://learn.microsoft.com/en-us/windows/win32/power/battery-information-str. |
| health | TEXT | One of the following: "Good" describes a well-performing battery, "Fair" describes a functional battery with limited capacity, or "Poor" describes a battery that's not capable of providing power |
| condition | TEXT | One of the following: "Normal" indicates the condition of the battery is within normal tolerances, "Service Needed" indicates that the battery should be checked out by a licensed Mac repair service, "Permanent Failure" indicates the battery needs replacement |
| manufacture_date | INTEGER | The date the battery was manufactured UNIX Epoch |

### carbon_black_info

**Platforms:** MacOS Linux Windows

Returns info about a Carbon Black sensor install.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| sensor_id | INTEGER | Sensor ID of the Carbon Black sensor |
| config_name | TEXT | Sensor group |
| collect_store_files | INTEGER | If the sensor is configured to send back binaries to the Carbon Black server |
| collect_module_loads | INTEGER | If the sensor is configured to capture module loads |
| collect_module_info | INTEGER | If the sensor is configured to collect metadata of binaries |
| collect_file_mods | INTEGER | If the sensor is configured to collect file modification events |
| collect_reg_mods | INTEGER | If the sensor is configured to collect registry modification events |
| collect_net_conns | INTEGER | If the sensor is configured to collect network connections |
| collect_processes | INTEGER | If the sensor is configured to process events |
| collect_cross_processes | INTEGER | If the sensor is configured to cross process events |
| collect_emet_events | INTEGER | If the sensor is configured to EMET events |
| collect_data_file_writes | INTEGER | If the sensor is configured to collect non binary file writes |
| collect_process_user_context | INTEGER | If the sensor is configured to collect the user running a process |
| collect_sensor_operations | INTEGER | Unknown |
| log_file_disk_quota_mb | INTEGER | Event file disk quota in MB |
| log_file_disk_quota_percentage | INTEGER | Event file disk quota in a percentage |
| protection_disabled | INTEGER | If the sensor is configured to report tamper events |
| sensor_ip_addr | TEXT | IP address of the sensor |
| sensor_backend_server | TEXT | Carbon Black server |
| event_queue | INTEGER | Size in bytes of Carbon Black event files on disk |
| binary_queue | INTEGER | Size in bytes of binaries waiting to be sent to Carbon Black server |

### chassis_info

**Platforms:** Windows

Display information pertaining to the chassis and its security status.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| audible_alarm | TEXT | If TRUE, the frame is equipped with an audible alarm. |
| breach_description | TEXT | If provided, gives a more detailed description of a detected security breach. |
| chassis_types | TEXT | A comma-separated list of chassis types, such as Desktop or Laptop. |
| description | TEXT | An extended description of the chassis if available. |
| lock | TEXT | If TRUE, the frame is equipped with a lock. |
| manufacturer | TEXT | The manufacturer of the chassis. |
| model | TEXT | The model of the chassis. |
| security_breach | TEXT | The physical status of the chassis such as Breach Successful, Breach Attempted, etc. |
| serial | TEXT | The serial number of the chassis. |
| smbios_tag | TEXT | The assigned asset tag number of the chassis. |
| sku | TEXT | The Stock Keeping Unit number if available. |
| status | TEXT | If available, gives various operational or nonoperational statuses such as OK, Degraded, and Pred Fail. |
| visible_alarm | TEXT | If TRUE, the frame is equipped with a visual alarm. |

### connected_displays

**Platforms:** MacOS

Provides information about the connected displays of the machine.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The name of the display. |
| product_id | TEXT | The product ID of the display. |
| serial_number | TEXT | The serial number of the display. (may not be unique) |
| vendor_id | TEXT | The vendor ID of the display. |
| manufactured_week | INTEGER | The manufacture week of the display. This field is 0 if not supported |
| manufactured_year | INTEGER | The manufacture year of the display. This field is 0 if not supported |
| display_id | TEXT | The display ID. |
| pixels | TEXT | The number of pixels of the display. |
| resolution | TEXT | The resolution of the display. |
| ambient_brightness_enabled | TEXT | The ambient brightness setting associated with the display. This will be 1 if enabled and is 0 if disabled or not supported. |
| connection_type | TEXT | The connection type associated with the display. |
| display_type | TEXT | The type of display. |
| main | INTEGER | If the display is the main display. |
| mirror | INTEGER | If the display is mirrored or not. This field is 1 if mirrored and 0 if not mirrored. |
| online | INTEGER | The online status of the display. This field is 1 if the display is online and 0 if it is offline. |
| rotation | TEXT | The rotation of the display (0, 90, 180, or 270 degrees). This field is -1 if display rotation is not supported. |

### cpu_info

**Platforms:** MacOS Linux Windows

Retrieve cpu hardware info of the machine.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device_id | TEXT | The DeviceID of the CPU. |
| model | TEXT | The model of the CPU. |
| manufacturer | TEXT | The manufacturer of the CPU. |
| processor_type | TEXT | The processor type, such as Central, Math, or Video. |
| cpu_status | INTEGER | The current operating status of the CPU. |
| number_of_cores | TEXT | The number of cores of the CPU. |
| logical_processors | INTEGER | The number of logical processors of the CPU. |
| address_width | TEXT | The width of the CPU address bus. |
| current_clock_speed | INTEGER | The current frequency of the CPU. |
| max_clock_speed | INTEGER | The maximum possible frequency of the CPU. |
| socket_designation | TEXT | The assigned socket on the board for the given CPU. |
| availability | TEXT | The availability and status of the CPU. |
| load_percentage | INTEGER | The current percentage of utilization of the CPU. |
| number_of_efficiency_cores | INTEGER | The number of efficiency cores of the CPU. Only available on Apple Silicon |
| number_of_performance_cores | INTEGER | The number of performance cores of the CPU. Only available on Apple Silicon |

### cpu_time

**Platforms:** MacOS Linux

Displays information from /proc/stat file about the time the cpu cores spent in different parts of the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| core | INTEGER | Name of the cpu (core) |
| user | BIGINT | Time spent in user mode |
| nice | BIGINT | Time spent in user mode with low priority (nice) |
| system | BIGINT | Time spent in system mode |
| idle | BIGINT | Time spent in the idle task |
| iowait | BIGINT | Time spent waiting for I/O to complete |
| irq | BIGINT | Time spent servicing interrupts |
| softirq | BIGINT | Time spent servicing softirqs |
| steal | BIGINT | Time spent in other operating systems when running in a virtualized environment |
| guest | BIGINT | Time spent running a virtual CPU for a guest OS under the control of the Linux kernel |
| guest_nice | BIGINT | Time spent running a niced guest |

### cpuid

**Platforms:** MacOS Linux Windows

Useful CPU features from the cpuid ASM call.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| feature | TEXT | Present feature flags |
| value | TEXT | Bit value or string |
| output_register | TEXT | Register used to for feature value |
| output_bit | INTEGER | Bit in register value for feature value |
| input_eax | TEXT | Value of EAX used |

### crashes

**Platforms:** MacOS

Application, System, and Mobile App crash logs.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Type of crash log |
| pid | BIGINT | Process (or thread) ID of the crashed process |
| path | TEXT | Path to the crashed process |
| crash_path | TEXT | Location of log file |
| identifier | TEXT | Identifier of the crashed process |
| version | TEXT | Version info of the crashed process |
| parent | BIGINT | Parent PID of the crashed process |
| responsible | TEXT | Process responsible for the crashed process |
| uid | INTEGER | User ID of the crashed process |
| datetime | TEXT | Date/Time at which the crash occurred |
| crashed_thread | BIGINT | Thread ID which crashed |
| stack_trace | TEXT | Most recent frame from the stack trace |
| exception_type | TEXT | Exception type of the crash |
| exception_codes | TEXT | Exception codes from the crash |
| exception_notes | TEXT | Exception notes from the crash |
| registers | TEXT | The value of the system registers |

### crontab

**Platforms:** MacOS Linux

Line parsed values from system and user cron/tab.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| event | TEXT | The job @event name (rare) |
| minute | TEXT | The exact minute for the job |
| hour | TEXT | The hour of the day for the job |
| day_of_month | TEXT | The day of the month for the job |
| month | TEXT | The month of the year for the job |
| day_of_week | TEXT | The day of the week for the job |
| command | TEXT | Raw command string |
| path | TEXT | File parsed |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### device_firmware

**Platforms:** MacOS

A best-effort list of discovered firmware versions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | Type of device |
| device | TEXT | The device name |
| version | TEXT | Firmware version |

### fan_speed_sensors

**Platforms:** MacOS

Fan speeds.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| fan | TEXT | Fan number |
| name | TEXT | Fan name |
| actual | INTEGER | Actual speed |
| min | INTEGER | Minimum speed |
| max | INTEGER | Maximum speed |
| target | INTEGER | Target speed |

### hardware_events

**Platforms:** MacOS Linux

**Table Type:** EVENTED TABLE

Hardware (PCI/USB/HID) events from UDEV or IOKit.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| action | TEXT | Remove, insert, change properties, etc |
| path | TEXT | Local device path assigned (optional) |
| type | TEXT | Type of hardware and hardware event |
| driver | TEXT | Driver claiming the device |
| vendor | TEXT | Hardware device vendor |
| vendor_id | TEXT | Hex encoded Hardware vendor identifier |
| model | TEXT | Hardware device model |
| model_id | TEXT | Hex encoded Hardware model identifier |
| serial | TEXT | Device serial (optional) |
| revision | TEXT | Device revision (optional) |
| time | BIGINT | Time of hardware event |
| eid | TEXT | Event ID |

### ibridge_info

**Platforms:** MacOS

Information about the Apple iBridge hardware controller.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| boot_uuid | TEXT | Boot UUID of the iBridge controller |
| coprocessor_version | TEXT | The manufacturer and chip version |
| firmware_version | TEXT | The build version of the firmware |
| unique_chip_id | TEXT | Unique id of the iBridge controller |

### intel_me_info

**Platforms:** Linux Windows

Intel ME/CSE Info.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| version | TEXT | Intel ME version |

### iokit_devicetree

**Platforms:** MacOS

The IOKit registry matching the DeviceTree plane.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Device node name |
| class | TEXT | Best matching device class (most-specific category) |
| id | BIGINT | IOKit internal registry ID |
| parent | BIGINT | Parent device registry ID |
| device_path | TEXT | Device tree path |
| service | INTEGER | 1 if the device conforms to IOService else 0 |
| busy_state | INTEGER | 1 if the device is in a busy state else 0 |
| retain_count | INTEGER | The device reference count |
| depth | INTEGER | Device nested depth |

### iokit_registry

**Platforms:** MacOS

The full IOKit registry without selecting a plane.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Default name of the node |
| class | TEXT | Best matching device class (most-specific category) |
| id | BIGINT | IOKit internal registry ID |
| parent | BIGINT | Parent registry ID |
| busy_state | INTEGER | 1 if the node is in a busy state else 0 |
| retain_count | INTEGER | The node reference count |
| depth | INTEGER | Node nested depth |

### kernel_info

**Platforms:** MacOS Linux Windows

Basic active kernel information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| version | TEXT | Kernel version |
| arguments | TEXT | Kernel arguments |
| path | TEXT | Kernel path |
| device | TEXT | Kernel device identifier |

### kernel_panics

**Platforms:** MacOS

System kernel panic logs.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Location of log file |
| time | TEXT | Formatted time of the event |
| registers | TEXT | A space delimited line of register:value pairs |
| frame_backtrace | TEXT | Backtrace of the crashed module |
| module_backtrace | TEXT | Modules appearing in the crashed module's backtrace |
| dependencies | TEXT | Module dependencies existing in crashed module's backtrace |
| name | TEXT | Process name corresponding to crashed thread |
| os_version | TEXT | Version of the operating system |
| kernel_version | TEXT | Version of the system kernel |
| system_model | TEXT | Physical system model, for example 'MacBookPro12,1 (Mac-E43C1C25D4880AD6)' |
| uptime | BIGINT | System uptime at kernel panic in nanoseconds |
| last_loaded | TEXT | Last loaded module before panic |
| last_unloaded | TEXT | Last unloaded module before panic |

### kva_speculative_info

**Platforms:** Windows

Display kernel virtual address and speculative execution information for the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| kva_shadow_enabled | INTEGER | Kernel Virtual Address shadowing is enabled. |
| kva_shadow_user_global | INTEGER | User pages are marked as global. |
| kva_shadow_pcid | INTEGER | Kernel VA PCID flushing optimization is enabled. |
| kva_shadow_inv_pcid | INTEGER | Kernel VA INVPCID is enabled. |
| bp_mitigations | INTEGER | Branch Prediction mitigations are enabled. |
| bp_system_pol_disabled | INTEGER | Branch Predictions are disabled via system policy. |
| bp_microcode_disabled | INTEGER | Branch Predictions are disabled due to lack of microcode update. |
| cpu_spec_ctrl_supported | INTEGER | SPEC_CTRL MSR supported by CPU Microcode. |
| ibrs_support_enabled | INTEGER | Windows uses IBRS. |
| stibp_support_enabled | INTEGER | Windows uses STIBP. |
| cpu_pred_cmd_supported | INTEGER | PRED_CMD MSR supported by CPU Microcode. |

### load_average

**Platforms:** MacOS Linux

Displays information about the system wide load averages.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| period | TEXT | Period over which the average is calculated. |
| average | TEXT | Load average over the specified period. |

### logical_drives

**Platforms:** Windows

Details for logical drives on the system. A logical drive generally represents a single partition.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device_id | TEXT | The drive id, usually the drive name, e.g., 'C:'. |
| type | TEXT | Deprecated (always 'Unknown'). |
| description | TEXT | The canonical description of the drive, e.g. 'Logical Fixed Disk', 'CD-ROM Disk'. |
| free_space | BIGINT | The amount of free space, in bytes, of the drive (-1 on failure). |
| size | BIGINT | The total amount of space, in bytes, of the drive (-1 on failure). |
| file_system | TEXT | The file system of the drive. |
| boot_partition | INTEGER | True if Windows booted from this drive. |

### memory_array_mapped_addresses

**Platforms:** MacOS Linux

Data associated for address mapping of physical memory arrays.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| handle | TEXT | Handle, or instance number, associated with the structure |
| memory_array_handle | TEXT | Handle of the memory array associated with this structure |
| starting_address | TEXT | Physical stating address, in kilobytes, of a range of memory mapped to physical memory array |
| ending_address | TEXT | Physical ending address of last kilobyte of a range of memory mapped to physical memory array |
| partition_width | INTEGER | Number of memory devices that form a single row of memory for the address partition of this structure |

### memory_arrays

**Platforms:** MacOS Linux

Data associated with collection of memory devices that operate to form a memory address.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| handle | TEXT | Handle, or instance number, associated with the array |
| location | TEXT | Physical location of the memory array |
| use | TEXT | Function for which the array is used |
| memory_error_correction | TEXT | Primary hardware error correction or detection method supported |
| max_capacity | INTEGER | Maximum capacity of array in gigabytes |
| memory_error_info_handle | TEXT | Handle, or instance number, associated with any error that was detected for the array |
| number_memory_devices | INTEGER | Number of memory devices on array |

### memory_device_mapped_addresses

**Platforms:** MacOS Linux

Data associated for address mapping of physical memory devices.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| handle | TEXT | Handle, or instance number, associated with the structure |
| memory_device_handle | TEXT | Handle of the memory device structure associated with this structure |
| memory_array_mapped_address_handle | TEXT | Handle of the memory array mapped address to which this device range is mapped to |
| starting_address | TEXT | Physical stating address, in kilobytes, of a range of memory mapped to physical memory array |
| ending_address | TEXT | Physical ending address of last kilobyte of a range of memory mapped to physical memory array |
| partition_row_position | INTEGER | Identifies the position of the referenced memory device in a row of the address partition |
| interleave_position | INTEGER | The position of the device in a interleave, i.e. 0 indicates non-interleave, 1 indicates 1st interleave, 2 indicates 2nd interleave, etc. |
| interleave_data_depth | INTEGER | The max number of consecutive rows from memory device that are accessed in a single interleave transfer; 0 indicates device is non-interleave |

### memory_devices

**Platforms:** MacOS Linux Windows

Physical memory device (type 17) information retrieved from SMBIOS.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| handle | TEXT | Handle, or instance number, associated with the structure in SMBIOS |
| array_handle | TEXT | The memory array that the device is attached to |
| form_factor | TEXT | Implementation form factor for this memory device |
| total_width | INTEGER | Total width, in bits, of this memory device, including any check or error-correction bits |
| data_width | INTEGER | Data width, in bits, of this memory device |
| size | INTEGER | Size of memory device in Megabyte |
| set | INTEGER | Identifies if memory device is one of a set of devices. A value of 0 indicates no set affiliation. |
| device_locator | TEXT | String number of the string that identifies the physically-labeled socket or board position where the memory device is located |
| bank_locator | TEXT | String number of the string that identifies the physically-labeled bank where the memory device is located |
| memory_type | TEXT | Type of memory used |
| memory_type_details | TEXT | Additional details for memory device |
| max_speed | INTEGER | Max speed of memory device in megatransfers per second (MT/s) |
| configured_clock_speed | INTEGER | Configured speed of memory device in megatransfers per second (MT/s) |
| manufacturer | TEXT | Manufacturer ID string |
| serial_number | TEXT | Serial number of memory device |
| asset_tag | TEXT | Manufacturer specific asset tag of memory device |
| part_number | TEXT | Manufacturer specific serial number of memory device |
| min_voltage | INTEGER | Minimum operating voltage of device in millivolts |
| max_voltage | INTEGER | Maximum operating voltage of device in millivolts |
| configured_voltage | INTEGER | Configured operating voltage of device in millivolts |

### memory_error_info

**Platforms:** MacOS Linux

Data associated with errors of a physical memory array.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| handle | TEXT | Handle, or instance number, associated with the structure |
| error_type | TEXT | type of error associated with current error status for array or device |
| error_granularity | TEXT | Granularity to which the error can be resolved |
| error_operation | TEXT | Memory access operation that caused the error |
| vendor_syndrome | TEXT | Vendor specific ECC syndrome or CRC data associated with the erroneous access |
| memory_array_error_address | TEXT | 32 bit physical address of the error based on the addressing of the bus to which the memory array is connected |
| device_error_address | TEXT | 32 bit physical address of the error relative to the start of the failing memory address, in bytes |
| error_resolution | TEXT | Range, in bytes, within which this error can be determined, when an error address is given |

### memory_info

**Platforms:** Linux

Main memory information in bytes.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| memory_total | BIGINT | Total amount of physical RAM, in bytes |
| memory_free | BIGINT | The amount of physical RAM, in bytes, left unused by the system |
| memory_available | BIGINT | The amount of physical RAM, in bytes, available for starting new applications, without swapping |
| buffers | BIGINT | The amount of physical RAM, in bytes, used for file buffers |
| cached | BIGINT | The amount of physical RAM, in bytes, used as cache memory |
| swap_cached | BIGINT | The amount of swap, in bytes, used as cache memory |
| active | BIGINT | The total amount of buffer or page cache memory, in bytes, that is in active use |
| inactive | BIGINT | The total amount of buffer or page cache memory, in bytes, that are free and available |
| swap_total | BIGINT | The total amount of swap available, in bytes |
| swap_free | BIGINT | The total amount of swap free, in bytes |

### memory_map

**Platforms:** Linux

OS memory region map.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Region name |
| start | TEXT | Start address of memory region |
| end | TEXT | End address of memory region |

### msr

**Platforms:** Linux

Various pieces of data stored in the model specific register per processor. NOTE: the msr kernel module must be enabled, and osquery must be run as root.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| processor_number | BIGINT | The processor number as reported in /proc/cpuinfo |
| turbo_disabled | BIGINT | Whether the turbo feature is disabled. |
| turbo_ratio_limit | BIGINT | The turbo feature ratio limit. |
| platform_info | BIGINT | Platform information. |
| perf_ctl | BIGINT | Performance setting for the processor. |
| perf_status | BIGINT | Performance status for the processor. |
| feature_control | BIGINT | Bitfield controlling enabled features. |
| rapl_power_limit | BIGINT | Run Time Average Power Limiting power limit. |
| rapl_energy_status | BIGINT | Run Time Average Power Limiting energy status. |
| rapl_power_units | BIGINT | Run Time Average Power Limiting power units. |

### nvram

**Platforms:** MacOS

Apple NVRAM variable listing.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Variable name |
| type | TEXT | Data type (CFData, CFString, etc) |
| value | TEXT | Raw variable data |

### oem_strings

**Platforms:** MacOS Linux

OEM defined strings retrieved from SMBIOS.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| handle | TEXT | Handle, or instance number, associated with the Type 11 structure |
| number | INTEGER | The string index of the structure |
| value | TEXT | The value of the OEM string |

### os_version

**Platforms:** MacOS Linux Windows

A single row containing the operating system name and version.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Distribution or product name |
| version | TEXT | Pretty, suitable for presentation, OS version |
| major | INTEGER | Major release version |
| minor | INTEGER | Minor release version |
| patch | INTEGER | Optional patch release |
| build | TEXT | Optional build-specific or variant string |
| platform | TEXT | OS Platform or ID |
| platform_like | TEXT | Closely related platforms |
| codename | TEXT | OS version codename |
| arch | TEXT | OS Architecture |
| extra | TEXT | Optional extra release specification |
| install_date | BIGINT | The install date of the OS. |
| revision | INTEGER | Update Build Revision, refers to the specific revision number of a Windows update |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| mount_namespace_id | TEXT | Mount namespace id |

### pci_devices

**Platforms:** MacOS Linux

PCI devices active on the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pci_slot | TEXT | PCI Device used slot |
| pci_class | TEXT | PCI Device class |
| driver | TEXT | PCI Device used driver |
| vendor | TEXT | PCI Device vendor |
| vendor_id | TEXT | Hex encoded PCI Device vendor identifier |
| model | TEXT | PCI Device model |
| model_id | TEXT | Hex encoded PCI Device model identifier |
| pci_class_id | TEXT | PCI Device class ID in hex format |
| pci_subclass_id | TEXT | PCI Device subclass in hex format |
| pci_subclass | TEXT | PCI Device subclass |
| subsystem_vendor_id | TEXT | Vendor ID of PCI device subsystem |
| subsystem_vendor | TEXT | Vendor of PCI device subsystem |
| subsystem_model_id | TEXT | Model ID of PCI device subsystem |
| subsystem_model | TEXT | Device description of PCI device subsystem |

### physical_disk_performance

**Platforms:** Windows

Provides provides raw data from performance counters that monitor hard or fixed disk drives on the system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the physical disk |
| avg_disk_bytes_per_read | BIGINT | Average number of bytes transferred from the disk during read operations |
| avg_disk_bytes_per_write | BIGINT | Average number of bytes transferred to the disk during write operations |
| avg_disk_read_queue_length | BIGINT | Average number of read requests that were queued for the selected disk during the sample interval |
| avg_disk_write_queue_length | BIGINT | Average number of write requests that were queued for the selected disk during the sample interval |
| avg_disk_sec_per_read | INTEGER | Average time, in seconds, of a read operation of data from the disk |
| avg_disk_sec_per_write | INTEGER | Average time, in seconds, of a write operation of data to the disk |
| current_disk_queue_length | INTEGER | Number of requests outstanding on the disk at the time the performance data is collected |
| percent_disk_read_time | BIGINT | Percentage of elapsed time that the selected disk drive is busy servicing read requests |
| percent_disk_write_time | BIGINT | Percentage of elapsed time that the selected disk drive is busy servicing write requests |
| percent_disk_time | BIGINT | Percentage of elapsed time that the selected disk drive is busy servicing read or write requests |
| percent_idle_time | BIGINT | Percentage of time during the sample interval that the disk was idle |

### platform_info

**Platforms:** MacOS Linux Windows

Information about EFI/UEFI/ROM and platform/boot.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| vendor | TEXT | Platform code vendor |
| version | TEXT | Platform code version |
| date | TEXT | Self-reported platform code update date |
| revision | TEXT | BIOS major and minor revision |
| extra | TEXT | Platform-specific additional information |
| firmware_type | TEXT | The type of firmware (uefi, bios, iboot, openfirmware, unknown). |
| address | TEXT | Relative address of firmware mapping |
| size | TEXT | Size in bytes of firmware |
| volume_size | INTEGER | (Optional) size of firmware volume |

### power_sensors

**Platforms:** MacOS

Machine power (currents, voltages, wattages, etc) sensors.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| key | TEXT | The SMC key on macOS |
| category | TEXT | The sensor category: currents, voltage, wattage |
| name | TEXT | Name of power source |
| value | TEXT | Power in Watts |

### registry

**Platforms:** Windows

All of the Windows registry hives.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| key | TEXT | Name of the key to search for |
| path | TEXT | Full path to the value |
| name | TEXT | Name of the registry value entry |
| type | TEXT | Type of the registry value, or 'subkey' if item is a subkey |
| data | TEXT | Data content of registry value |
| mtime | BIGINT | timestamp of the most recent registry write |

### secureboot

**Platforms:** MacOS Linux Windows

Secure Boot UEFI Settings.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| secure_boot | INTEGER | Whether secure boot is enabled |
| secure_mode | INTEGER | (Intel) Secure mode: 0 disabled, 1 full security, 2 medium security |
| description | TEXT | (Apple Silicon) Human-readable description: 'Full Security', 'Reduced Security', or 'Permissive Security' |
| kernel_extensions | INTEGER | (Apple Silicon) Allow user management of kernel extensions from identified developers (1 if allowed) |
| mdm_operations | INTEGER | (Apple Silicon) Allow remote (MDM) management of kernel extensions and automatic software updates (1 if allowed) |
| setup_mode | INTEGER | Whether setup mode is enabled |

### secureboot_certificates

**Platforms:** Linux

**Status:** New

X.509 certificates from UEFI Secure Boot signature databases (db and dbx EFI variables). Useful for monitoring CA expiry and adoption of updated certificates (e.g. Microsoft UEFI CA 2023).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| common_name | TEXT | Certificate CommonName |
| subject | TEXT | Certificate subject distinguished name |
| issuer | TEXT | Certificate issuer distinguished name |
| not_valid_before | TEXT | Lower bound of valid date |
| not_valid_after | TEXT | Certificate expiration date |
| sha1 | TEXT | SHA1 hash of the raw certificate contents |
| serial | TEXT | Certificate serial number |
| revoked | INTEGER | 1 if the certificate is in the dbx revocation list, 0 if it is in the db allowlist |
| path | TEXT | Path to the EFI variable file |
| is_ca | INTEGER | 1 if the certificate is a CA, 0 otherwise |
| self_signed | INTEGER | 1 if the certificate is self-signed, 0 otherwise |
| key_usage | TEXT | Certificate key usage extension string |
| authority_key_id | TEXT | Authority Key Identifier (AKI) |
| subject_key_id | TEXT | Subject Key Identifier (SKI) |
| signing_algorithm | TEXT | Algorithm used to sign the certificate |
| key_algorithm | TEXT | Public key algorithm |
| key_strength | TEXT | Public key size in bits |

### smc_keys

**Platforms:** MacOS

Apple's system management controller keys.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| key | TEXT | 4-character key |
| type | TEXT | SMC-reported type literal type |
| size | INTEGER | Reported size of data in bytes |
| value | TEXT | A type-encoded representation of the key value |
| hidden | INTEGER | 1 if this key is normally hidden, otherwise 0 |

### suid_bin

**Platforms:** MacOS Linux

suid binaries in common locations.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Binary path |
| username | TEXT | Binary owner username |
| groupname | TEXT | Binary owner group |
| permissions | TEXT | Binary permissions |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### system_controls

**Platforms:** MacOS Linux

sysctl names, values, and settings information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Full sysctl MIB name |
| oid | TEXT | Control MIB |
| subsystem | TEXT | Subsystem ID, control type |
| current_value | TEXT | Value of setting |
| config_value | TEXT | The MIB value set in /etc/sysctl.conf |
| type | TEXT | Data type |
| field_name | TEXT | Specific attribute of opaque type |

### system_info

**Platforms:** MacOS Linux Windows

System information for identification.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| hostname | TEXT | Network hostname including domain |
| uuid | TEXT | Unique ID provided by the system |
| cpu_type | TEXT | CPU type |
| cpu_subtype | TEXT | CPU subtype |
| cpu_brand | TEXT | CPU brand string, contains vendor and model |
| cpu_physical_cores | INTEGER | Number of physical CPU cores in to the system |
| cpu_logical_cores | INTEGER | Number of logical CPU cores available to the system |
| cpu_sockets | INTEGER | Number of processor sockets in the system |
| cpu_microcode | TEXT | Microcode version |
| physical_memory | BIGINT | Total physical memory in bytes |
| hardware_vendor | TEXT | Hardware vendor |
| hardware_model | TEXT | Hardware model |
| hardware_version | TEXT | Hardware version |
| hardware_serial | TEXT | Device serial number |
| board_vendor | TEXT | Board vendor |
| board_model | TEXT | Board model |
| board_version | TEXT | Board version |
| board_serial | TEXT | Board serial number |
| computer_name | TEXT | Friendly computer name (optional) |
| local_hostname | TEXT | Local hostname (optional) |
| emulated_cpu_type | TEXT | Emulated CPU type |

### system_profiler

**Platforms:** MacOS

Query system_profiler data types and return the full result as JSON. Returns only the data types specified in the constraints. See available data types with `system_profiler -listDataTypes`.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| data_type | TEXT | The system profiler data type (e.g., SPHardwareDataType) Required in WHERE clause |
| value | TEXT | A JSON representation of the full result dictionary for the data type |

### temperature_sensors

**Platforms:** MacOS

Machine's temperature sensors.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| key | TEXT | The SMC key on macOS |
| name | TEXT | Name of temperature source |
| celsius | DOUBLE | Temperature in Celsius |
| fahrenheit | DOUBLE | Temperature in Fahrenheit |

### time

**Platforms:** MacOS Linux Windows

Track current date and time in UTC.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| weekday | TEXT | Current weekday in UTC |
| year | INTEGER | Current year in UTC |
| month | INTEGER | Current month in UTC |
| day | INTEGER | Current day in UTC |
| hour | INTEGER | Current hour in UTC |
| minutes | INTEGER | Current minutes in UTC |
| seconds | INTEGER | Current seconds in UTC |
| timezone | TEXT | Timezone for reported time (hardcoded to UTC) |
| local_timezone | TEXT | Current local timezone in of the system |
| unix_time | INTEGER | Current UNIX time in UTC |
| timestamp | TEXT | Current timestamp (log format) in UTC |
| datetime | TEXT | Current date and time (ISO format) in UTC |
| iso_8601 | TEXT | Current time (ISO format) in UTC |
| win_timestamp | BIGINT | Timestamp value in 100 nanosecond units |

### time_machine_backups

**Platforms:** MacOS

Backups to drives using TimeMachine. This table requires Full Disk Access (FDA) permission.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| destination_id | TEXT | Time Machine destination ID |
| backup_date | INTEGER | Backup Date |

### time_machine_destinations

**Platforms:** MacOS

Locations backed up to using Time Machine. This table requires Full Disk Access (FDA) permission.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| alias | TEXT | Human readable name of drive |
| destination_id | TEXT | Time Machine destination ID |
| consistency_scan_date | INTEGER | Consistency scan date |
| root_volume_uuid | TEXT | Root UUID of backup volume |
| bytes_available | INTEGER | Bytes available on volume |
| bytes_used | INTEGER | Bytes used on volume |
| encryption | TEXT | Last known encrypted state |

### tpm_info

**Platforms:** Windows

A table that lists the TPM related information.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| activated | INTEGER | TPM is activated |
| enabled | INTEGER | TPM is enabled |
| owned | INTEGER | TPM is owned |
| manufacturer_version | TEXT | TPM version |
| manufacturer_id | INTEGER | TPM manufacturers ID |
| manufacturer_name | TEXT | TPM manufacturers name |
| product_name | TEXT | Product name of the TPM |
| physical_presence_version | TEXT | Version of the Physical Presence Interface |
| spec_version | TEXT | Trusted Computing Group specification that the TPM supports |

### ulimit_info

**Platforms:** MacOS Linux

System resource usage limits.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| type | TEXT | System resource to be limited |
| soft_limit | TEXT | Current limit value |
| hard_limit | TEXT | Maximum limit value |

### uptime

**Platforms:** MacOS Linux Windows

Track time passed since last boot. Some systems track this as calendar time, some as runtime.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| days | INTEGER | Days of uptime |
| hours | INTEGER | Hours of uptime |
| minutes | INTEGER | Minutes of uptime |
| seconds | INTEGER | Seconds of uptime |
| total_seconds | BIGINT | Total uptime seconds |

### usb_devices

**Platforms:** MacOS Linux

USB devices that are actively plugged into the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| usb_address | INTEGER | USB Device used address |
| usb_port | INTEGER | USB Device used port |
| vendor | TEXT | USB Device vendor string |
| vendor_id | TEXT | Hex encoded USB Device vendor identifier |
| version | TEXT | USB Device version number |
| model | TEXT | USB Device model string |
| model_id | TEXT | Hex encoded USB Device model identifier |
| serial | TEXT | USB Device serial connection |
| class | TEXT | USB Device class |
| subclass | TEXT | USB Device subclass |
| protocol | TEXT | USB Device protocol |
| removable | INTEGER | 1 If USB device is removable else 0 |

### video_info

**Platforms:** Windows

Retrieve video card information of the machine.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| color_depth | INTEGER | The amount of bits per pixel to represent color. |
| driver | TEXT | The driver of the device. |
| driver_date | BIGINT | The date listed on the installed driver. |
| driver_version | TEXT | The version of the installed driver. |
| manufacturer | TEXT | The manufacturer of the gpu. |
| model | TEXT | The model of the gpu. |
| series | TEXT | The series of the gpu. |
| video_mode | TEXT | The current resolution of the display. |

### virtual_memory_info

**Platforms:** MacOS

Darwin Virtual Memory statistics.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| free | BIGINT | Total number of free pages. |
| active | BIGINT | Total number of active pages. |
| inactive | BIGINT | Total number of inactive pages. |
| speculative | BIGINT | Total number of speculative pages. |
| throttled | BIGINT | Total number of throttled pages. |
| wired | BIGINT | Total number of wired down pages. |
| purgeable | BIGINT | Total number of purgeable pages. |
| faults | BIGINT | Total number of calls to vm_faults. |
| copy | BIGINT | Total number of copy-on-write pages. |
| zero_fill | BIGINT | Total number of zero filled pages. |
| reactivated | BIGINT | Total number of reactivated pages. |
| purged | BIGINT | Total number of purged pages. |
| file_backed | BIGINT | Total number of file backed pages. |
| anonymous | BIGINT | Total number of anonymous pages. |
| uncompressed | BIGINT | Total number of uncompressed pages. |
| compressor | BIGINT | The number of pages used to store compressed VM pages. |
| decompressed | BIGINT | The total number of pages that have been decompressed by the VM compressor. |
| compressed | BIGINT | The total number of pages that have been compressed by the VM compressor. |
| page_ins | BIGINT | The total number of requests for pages from a pager. |
| page_outs | BIGINT | Total number of pages paged out. |
| swap_ins | BIGINT | The total number of compressed pages that have been swapped out to disk. |
| swap_outs | BIGINT | The total number of compressed pages that have been swapped back in from disk. |

### windows_crashes

**Platforms:** Windows

Extracted information from Windows crash logs (Minidumps).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| datetime | TEXT | Timestamp (log format) of the crash |
| module | TEXT | Path of the crashed module within the process |
| path | TEXT | Path of the executable file for the crashed process |
| pid | BIGINT | Process ID of the crashed process |
| tid | BIGINT | Thread ID of the crashed thread |
| version | TEXT | File version info of the crashed process |
| process_uptime | BIGINT | Uptime of the process in seconds |
| stack_trace | TEXT | Multiple stack frames from the stack trace |
| exception_code | TEXT | The Windows exception code |
| exception_message | TEXT | The NTSTATUS error message associated with the exception code |
| exception_address | TEXT | Address (in hex) where the exception occurred |
| registers | TEXT | The values of the system registers |
| command_line | TEXT | Command-line string passed to the crashed process |
| current_directory | TEXT | Current working directory of the crashed process |
| username | TEXT | Username of the user who ran the crashed process |
| machine_name | TEXT | Name of the machine where the crash happened |
| major_version | INTEGER | Windows major version of the machine |
| minor_version | INTEGER | Windows minor version of the machine |
| build_number | INTEGER | Windows build number of the crashing machine |
| type | TEXT | Type of crash log |
| crash_path | TEXT | Path of the log file |

### wmi_bios_info

**Platforms:** Windows

Lists important information from the system bios.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the Bios setting |
| value | TEXT | Value of the Bios setting |
