# Knowledge - 99G - OSQuery Persistence and Startup Tables

_Exact OSQuery persistence, startup, scheduled-task, service, and shim reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### appcompat_shims

**Platforms:** Windows

Application Compatibility shims are a way to persist malware. This table presents the AppCompat Shim information from the registry in a nice format. See http://files.brucon.org/2015/Tomczak_and_Ballenthin_Shims_for_the_Win.pdf for more details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| executable | TEXT | Name of the executable that is being shimmed. This is pulled from the registry. |
| path | TEXT | This is the path to the SDB database. |
| description | TEXT | Description of the SDB. |
| install_time | INTEGER | Install time of the SDB |
| type | TEXT | Type of the SDB database. |
| sdb_id | TEXT | Unique GUID of the SDB. |

### autoexec

**Platforms:** Windows

Aggregate of executables that will automatically execute on the target machine. This is an amalgamation of other tables like services, scheduled_tasks, startup_items and more.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path to the executable |
| name | TEXT | Name of the program |
| source | TEXT | Source table of the autoexec item |

### background_activities_moderator

**Platforms:** Windows

Background Activities Moderator (BAM) tracks application execution.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Application file path. |
| last_execution_time | BIGINT | Most recent time application was executed. |
| sid | TEXT | User SID. |

### browser_plugins

**Platforms:** MacOS

All C/NPAPI browser plugin details for all users. C/NPAPI has been deprecated on all major browsers. To query for plugins on modern browsers, try: `chrome_extensions` `firefox_addons` `safari_extensions`.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local user that owns the plugin |
| name | TEXT | Plugin display name |
| identifier | TEXT | Plugin identifier |
| version | TEXT | Plugin short version |
| sdk | TEXT | Build SDK used to compile plugin |
| description | TEXT | Plugin description text |
| development_region | TEXT | Plugin language-localization |
| native | INTEGER | Plugin requires native execution |
| path | TEXT | Path to plugin bundle |
| disabled | INTEGER | Is the plugin disabled. 1 = Disabled |

### chrome_extension_content_scripts

**Platforms:** MacOS Linux Windows

Chrome browser extension content scripts.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| browser_type | TEXT | The browser type (Valid values: chrome, chromium, opera, yandex, brave) |
| uid | BIGINT | The local user that owns the extension |
| identifier | TEXT | Extension identifier |
| version | TEXT | Extension-supplied version |
| script | TEXT | The content script used by the extension |
| match | TEXT | The pattern that the script is matched against |
| profile_path | TEXT | The profile path |
| path | TEXT | Path to extension folder |
| referenced | BIGINT | 1 if this extension is referenced by the Preferences file of the profile |

### drivers

**Platforms:** Windows

Details for in-use Windows device drivers. This does not display installed but unused drivers.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| device_id | TEXT | Device ID |
| device_name | TEXT | Device name |
| image | TEXT | Path to driver image file |
| description | TEXT | Driver description |
| service | TEXT | Driver service name, if one exists |
| service_key | TEXT | Driver service registry key |
| version | TEXT | Driver version |
| inf | TEXT | Associated inf file |
| class | TEXT | Device/driver class name |
| provider | TEXT | Driver provider |
| manufacturer | TEXT | Device manufacturer |
| driver_key | TEXT | Driver key |
| date | BIGINT | Driver date |
| signed | INTEGER | Whether the driver is signed or not |

### event_taps

**Platforms:** MacOS

Returns information about installed event taps.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| enabled | INTEGER | Is the Event Tap enabled |
| event_tap_id | INTEGER | Unique ID for the Tap |
| event_tapped | TEXT | The mask that identifies the set of events to be observed. |
| process_being_tapped | INTEGER | The process ID of the target application |
| tapping_process | INTEGER | The process ID of the application that created the event tap. |

### kernel_extensions

**Platforms:** MacOS

macOS's kernel extensions, both loaded and within the load search path.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| idx | INTEGER | Extension load tag or index |
| refs | INTEGER | Reference count |
| size | BIGINT | Bytes of wired memory used by extension |
| name | TEXT | Extension label |
| version | TEXT | Extension version |
| linked_against | TEXT | Indexes of extensions this extension is linked against |
| path | TEXT | Optional path to extension bundle |

### kernel_modules

**Platforms:** Linux

Linux kernel modules both loaded and within the load search path.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Module name |
| size | BIGINT | Size of module content |
| used_by | TEXT | Module reverse dependencies |
| status | TEXT | Kernel module status |
| address | TEXT | Kernel module address |

### launchd

**Platforms:** MacOS

LaunchAgents and LaunchDaemons from default search paths.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Path to daemon or agent plist |
| name | TEXT | File name of plist (used by launchd) |
| label | TEXT | Daemon or agent service name |
| program | TEXT | Path to target program |
| run_at_load | TEXT | Should the program run on launch load |
| keep_alive | TEXT | Should the process be restarted if killed |
| on_demand | TEXT | Deprecated key, replaced by keep_alive |
| disabled | TEXT | Skip loading this daemon or agent on boot |
| username | TEXT | Run this daemon or agent as this username |
| groupname | TEXT | Run this daemon or agent as this group |
| stdout_path | TEXT | Pipe stdout to a target path |
| stderr_path | TEXT | Pipe stderr to a target path |
| start_interval | TEXT | Frequency to run in seconds |
| program_arguments | TEXT | Command line arguments passed to program |
| watch_paths | TEXT | Key that launches daemon or agent if path is modified |
| queue_directories | TEXT | Similar to watch_paths but only with non-empty directories |
| inetd_compatibility | TEXT | Run this daemon or agent as it was launched from inetd |
| start_on_mount | TEXT | Run daemon or agent every time a filesystem is mounted |
| root_directory | TEXT | Key used to specify a directory to chroot to before launch |
| working_directory | TEXT | Key used to specify a directory to chdir to before launch |
| process_type | TEXT | Key describes the intended purpose of the job |

### launchd_overrides

**Platforms:** MacOS

Override keys, per user, for LaunchDaemons and Agents.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| label | TEXT | Daemon or agent service name |
| key | TEXT | Name of the override key |
| value | TEXT | Overridden value |
| uid | BIGINT | User ID applied to the override, 0 applies to all |
| path | TEXT | Path to daemon or agent plist |

### scheduled_tasks

**Platforms:** Windows

Lists all of the tasks in the Windows task scheduler.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the scheduled task |
| action | TEXT | Actions executed by the scheduled task |
| path | TEXT | Path to the executable to be run |
| enabled | INTEGER | Whether or not the scheduled task is enabled |
| state | TEXT | State of the scheduled task |
| hidden | INTEGER | Whether or not the task is visible in the UI |
| last_run_time | BIGINT | Timestamp the task last ran |
| next_run_time | BIGINT | Timestamp the task is scheduled to run next |
| last_run_message | TEXT | Exit status message of the last task run |
| last_run_code | TEXT | Exit status code of the last task run |

### services

**Platforms:** Windows

Lists all installed Windows services and their relevant data.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Service name |
| service_type | TEXT | Service Type: OWN_PROCESS, SHARE_PROCESS and maybe Interactive (can interact with the desktop) |
| display_name | TEXT | Service Display name |
| status | TEXT | Service Current status: STOPPED, START_PENDING, STOP_PENDING, RUNNING, CONTINUE_PENDING, PAUSE_PENDING, PAUSED |
| pid | INTEGER | the Process ID of the service |
| start_type | TEXT | Service start type: BOOT_START, SYSTEM_START, AUTO_START, DEMAND_START, DISABLED |
| win32_exit_code | INTEGER | The error code that the service uses to report an error that occurs when it is starting or stopping |
| service_exit_code | INTEGER | The service-specific error code that the service returns when an error occurs while the service is starting or stopping |
| path | TEXT | Path to Service Executable |
| module_path | TEXT | Path to ServiceDll |
| description | TEXT | Service Description |
| user_account | TEXT | The name of the account that the service process will be logged on as when it runs. This name can be of the form Domain\\UserName. If the account belongs to the built-in domain, the name can be of the form .\\UserName. |

### shimcache

**Platforms:** Windows

Application Compatibility Cache, contains artifacts of execution.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| entry | INTEGER | Execution order. |
| path | TEXT | This is the path to the executed file. |
| modified_time | INTEGER | File Modified time. |
| execution_flag | INTEGER | Boolean Execution flag, 1 for execution, 0 for no execution, -1 for missing (this flag does not exist on Windows 10 and higher). |

### startup_items

**Platforms:** MacOS Linux Windows

Applications and binaries set as startup items.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of startup item |
| path | TEXT | Path of startup item |
| args | TEXT | Arguments provided to startup executable |
| type | TEXT | Type of startup item. On macOS this can be app, agent (LaunchAgent), daemon (LaunchDaemon), login item, or user item. |
| source | TEXT | Directory containing startup item (on macOS, the subsystem providing it) |
| status | TEXT | Startup status. On Linux: enabled or disabled. On macOS: Combination of enabled, allowed, notified, and hidden. Apple does not seem to document these status values, but allowed seems to indicate whether it is enabled in System Settings. |
| username | TEXT | The user associated with the startup item |

### system_extensions

**Platforms:** MacOS

macOS (>= 10.15) system extension table.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| path | TEXT | Original path of system extension |
| UUID | TEXT | Extension unique id |
| state | TEXT | System extension state |
| identifier | TEXT | Identifier name |
| version | TEXT | System extension version |
| category | TEXT | System extension category |
| bundle_path | TEXT | System extension bundle path |
| team | TEXT | Signing team ID |
| mdm_managed | INTEGER | 1 if managed by MDM system extension payload configuration, 0 otherwise |

### systemd_units

**Platforms:** Linux

Track systemd units.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| id | TEXT | Unique unit identifier |
| description | TEXT | Unit description |
| load_state | TEXT | Reflects whether the unit definition was properly loaded |
| active_state | TEXT | The high-level unit activation state, i.e. generalization of SUB |
| sub_state | TEXT | The low-level unit activation state, values depend on unit type |
| unit_file_state | TEXT | Whether the unit file is enabled, e.g. `enabled`, `masked`, `disabled`, etc |
| following | TEXT | The name of another unit that this unit follows in state |
| object_path | TEXT | The object path for this unit |
| job_id | BIGINT | Next queued job id |
| job_type | TEXT | Job type |
| job_path | TEXT | The object path for the job |
| fragment_path | TEXT | The unit file path this unit was read from, if there is any |
| user | TEXT | The configured user, if any |
| source_path | TEXT | Path to the (possibly generated) unit configuration file |

### wmi_cli_event_consumers

**Platforms:** Windows

WMI CommandLineEventConsumer, which can be used for persistence on Windows. See https://www.blackhat.com/docs/us-15/materials/us-15-Graeber-Abusing-Windows-Management-Instrumentation-WMI-To-Build-A-Persistent%20Asynchronous-And-Fileless-Backdoor-wp.pdf for more details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| namespace | TEXT | The WMI namespace where the consumer was found. |
| name | TEXT | Unique name of a consumer. |
| command_line_template | TEXT | Standard string template that specifies the process to be started. This property can be NULL, and the ExecutablePath property is used as the command line. |
| executable_path | TEXT | Module to execute. The string can specify the full path and file name of the module to execute, or it can specify a partial name. If a partial name is specified, the current drive and current directory are assumed. |
| class | TEXT | The name of the class. |
| relative_path | TEXT | Relative path to the class or instance. |

### wmi_event_filters

**Platforms:** Windows

Lists WMI event filters.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| namespace | TEXT | The WMI namespace where the filter was found. |
| name | TEXT | Unique identifier of an event filter. |
| query | TEXT | Windows Management Instrumentation Query Language (WQL) event query that specifies the set of events for consumer notification, and the specific conditions for notification. |
| query_language | TEXT | Query language that the query is written in. |
| class | TEXT | The name of the class. |
| relative_path | TEXT | Relative path to the class or instance. |

### wmi_filter_consumer_binding

**Platforms:** Windows

Lists the relationship between event consumers and filters.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| namespace | TEXT | The WMI namespace where the binding was found. |
| consumer | TEXT | Reference to an instance of __EventConsumer that represents the object path to a logical consumer, the recipient of an event. |
| filter | TEXT | Reference to an instance of __EventFilter that represents the object path to an event filter which is a query that specifies the type of event to be received. |
| class | TEXT | The name of the class. |
| relative_path | TEXT | Relative path to the class or instance. |

### wmi_script_event_consumers

**Platforms:** Windows

WMI ActiveScriptEventConsumer, which can be used for persistence on Windows. See https://www.blackhat.com/docs/us-15/materials/us-15-Graeber-Abusing-Windows-Management-Instrumentation-WMI-To-Build-A-Persistent%20Asynchronous-And-Fileless-Backdoor-wp.pdf for more details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| namespace | TEXT | The WMI namespace where the consumer was found. |
| name | TEXT | Unique identifier for the event consumer. |
| scripting_engine | TEXT | Name of the scripting engine to use, for example, 'VBScript'. This property cannot be NULL. |
| script_file_name | TEXT | Name of the file from which the script text is read, intended as an alternative to specifying the text of the script in the ScriptText property. |
| script_text | TEXT | Text of the script that is expressed in a language known to the scripting engine. This property must be NULL if the ScriptFileName property is not NULL. |
| class | TEXT | The name of the class. |
| relative_path | TEXT | Relative path to the class or instance. |
