# Knowledge - Reference - Elastic Response Actions Reference

_Governed reference for native Elastic response-action syntax_

**Summary:** Use this page when the next analyst action should be a native Elastic response action. Preserve native response-action syntax directly, and do not wrap native response actions inside `execute`.

---

## Reference source

The material below is preserved from the approved response-actions source markdown. Keep command names, parameters, privileges, and layout exact when using it as a reference.

---

# Endpoint response actions

**IMPORTANT**: This documentation is no longer updated. Refer to [Elastic's version policy](https://www.elastic.co/support/eol) and the [latest documentation](https://www.elastic.co/docs/solutions/security/endpoint-response-actions).

The response console allows you to perform response actions on an endpoint using a terminal-like interface. You can enter action commands and get near-instant feedback on them. Actions are also recorded in the endpoint’s [response actions history](https://www.elastic.co/guide/en/security/8.19/response-actions.html#actions-log "Response actions history") for reference.

Response actions are supported on all endpoint platforms (Linux, macOS, and Windows).

**Requirements**

- Response actions and the response console UI are [Enterprise subscription](https://www.elastic.co/pricing) features.
- Endpoints must have Elastic Agent version 8.4 or higher installed with the Elastic Defend integration to receive response actions.
- Some response actions require specific [privileges](https://www.elastic.co/guide/en/security/8.19/endpoint-management-req.html "Elastic Defend feature privileges"), indicated below. These are required to perform actions both in the response console and in other areas of the Elastic Security app (such as isolating a host from a detection alert).
- Users must have privileges for at least one response action to access the response console.

**Interface description:** The response console page shows the selected endpoint, its health status, a **Response actions history** button, a **Help** control, an empty console output area, and a **Submit response action** input field at the bottom where commands are entered.

Launch the response console from any of the following places in Elastic Security:

- **Endpoints** page → **Actions** menu (**…**) → **Respond**
- Endpoint details flyout → **Take action** → **Respond**
- Alert or event details flyout → **Take action** → **Respond**
- Host details page → **Respond**

To perform an action on the endpoint, enter a [response action command](https://www.elastic.co/guide/en/security/8.19/response-actions.html#response-action-commands "Response action commands") in the input area at the bottom of the console, then press **Return**. Output from the action is displayed in the console.

If a host is unavailable, pending actions will execute once the host comes online. Pending actions expire after two weeks and can be tracked in the response actions history.

> **Note:**
>
> Some response actions may take a few seconds to complete. Once you enter a command, you can immediately enter another command while the previous action is running.

Activity in the response console is persistent, so you can navigate away from the page and any pending actions you’ve submitted will continue to run. To confirm that an action completed, return to the response console to view the console output or check the [response actions history](https://www.elastic.co/guide/en/security/8.19/response-actions.html#actions-log "Response actions history").

> **Important:**
>
> Once you submit a response action, you can’t cancel it, even if the action is pending for an offline host.

## Response action commands

The following response action commands are available in the response console.

### `isolate`

[Isolate the host](https://www.elastic.co/guide/en/security/8.19/host-isolation-ov.html "Isolate a host"), blocking communication with other hosts on the network.

Required privilege: **Host Isolation**

Example: `isolate --comment "Isolate host related to detection alerts"`

### `release`

Release an isolated host, allowing it to communicate with the network again.

Required privilege: **Host Isolation**

Example: `release --comment "Release host, everything looks OK"`

### `status`

Show information about the host’s status, including: Elastic Agent status and version, the Elastic Defend integration’s policy status, and when the host was last active.

### `processes`

Show a list of all processes running on the host. This action may take a minute or so to complete.

Required privilege: **Process Operations**

> **Tip:**
>
> Use this command to get current PID or entity ID values, which are required for other response actions such as `kill-process` and `suspend-process`.
>
> Entity IDs may be more reliable than PIDs, because entity IDs are unique values on the host, while PID values can be reused by the operating system.

> **Note:**
>
> Running this command on third-party-protected hosts might return the process list in a different format. Refer to [*Third-party response actions*](https://www.elastic.co/guide/en/security/8.19/third-party-actions.html "Third-party response actions") for more information.

### `kill-process`

Terminate a process. You must include one of the following parameters to identify the process to terminate:

- `--pid`: A process ID (PID) representing the process to terminate.
- `--entityId`: An entity ID representing the process to terminate.

Required privilege: **Process Operations**

Example: `kill-process --pid 123 --comment "Terminate suspicious process"`

> **Note:**
>
> For SentinelOne-enrolled hosts, you must use the parameter `--processName` to identify the process to terminate. `--pid` and `--entityId` are not supported.
>
> Example: `kill-process --processName cat --comment "Terminate suspicious process"`

### `suspend-process`

Suspend a process. You must include one of the following parameters to identify the process to suspend:

- `--pid`: A process ID (PID) representing the process to suspend.
- `--entityId`: An entity ID representing the process to suspend.

Required privilege: **Process Operations**

Example: `suspend-process --pid 123 --comment "Suspend suspicious process"`

### `get-file`

Retrieve a file from a host. Files are downloaded in a password-protected `.zip` archive to prevent the file from running. Use password `elastic` to open the `.zip` in a safe environment.

> **Note:**
>
> Files retrieved from third-party-protected hosts require a different password. Refer to [*Third-party response actions*](https://www.elastic.co/guide/en/security/8.19/third-party-actions.html "Third-party response actions") for your system’s password.

You must include the following parameter to specify the file’s location on the host:

- `--path`: The file’s full path (including the file name).

Required privilege: **File Operations**

Example: `get-file --path "/full/path/to/file.txt" --comment "Possible malware"`

> **Note:**
>
> The maximum file size that can be retrieved using `get-file` is `104857600` bytes, or 100 MB.

> **Tip:**
>
> You can use the [Osquery manager integration](https://www.elastic.co/guide/en/security/8.19/use-osquery.html "Osquery") to query a host’s operating system and gain insight into its files and directories, then use `get-file` to retrieve specific files.

> **Note:**
>
> When Elastic Defend prevents file activity due to [malware prevention](https://www.elastic.co/guide/en/security/8.19/configure-endpoint-integration-policy.html#malware-protection "Malware protection"), the file is quarantined on the host and a malware prevention alert is created. To retrieve this file with `get-file`, copy the path from the alert’s **Quarantined file path** field (`file.Ext.quarantine_path`), which appears under **Highlighted fields** in the alert details flyout. Then paste the value into the `--path` parameter.

### `execute`

Run a shell command on the host. The command’s output and any errors appear in the response console, up to 2000 characters. The complete output (stdout and stderr) are also saved to a downloadable `.zip` archive (password: `elastic`). Use these parameters:

- `--command`: (Required) A shell command to run on the host. The command must be supported by `bash` for Linux and macOS hosts, and `cmd.exe` for Windows.

  > **Note:**
  >
  > - Multiple consecutive dashes in the value must be escaped; single dashes do not need to be escaped. For example, to represent a directory named `/opt/directory--name`, use the following: `/opt/directory\-\-name`.
  > - You can use quotation marks without escaping. For example:
  >   `execute --command "cd "C:\Program Files\directory""`
- `--timeout`: (Optional) How long the host should wait for the command to complete. Use `h` for hours, `m` for minutes, `s` for seconds (for example, `2s` is two seconds). If no timeout is specified, it defaults to four hours.

Required privilege: **Execute Operations**

Example: `execute --command "ls -al" --timeout 2s --comment "Get list of all files"`

> **Warning:**
>
> This response action runs commands on the host using the same user account running the Elastic Defend integration, which normally has full control over the system. Be careful with any commands that could cause irrevocable changes.

### `upload`

Upload a file to the host. The file is saved to the location on the host where Elastic Endpoint is installed. After you run the command, the full path is returned in the console for reference. Use these parameters:

- `--file`: (Required) The file to send to the host. As soon as you type this parameter, a popup appears — select it to navigate to the file, or drag and drop the file onto the popup.
- `--overwrite`: (Optional) Overwrite the file on the host if it already exists.

Required privilege: **File Operations**

Example: `upload --file --comment "Upload remediation script"`

> **Tip:**
>
> You can follow this with the `execute` response action to upload and run scripts for mitigation or other purposes.

> **Note:**
>
> The default file size maximum is 25 MB, configurable in `kibana.yml` with the `xpack.securitySolution.maxUploadResponseActionFileBytes` setting. You must enter the value in bytes (the maximum is `104857600` bytes, or 100 MB).

### `scan`

Scan a specific file or directory on the host for malware. This uses the [malware protection settings](https://www.elastic.co/guide/en/security/8.19/configure-endpoint-integration-policy.html#malware-protection "Malware protection") (such as **Detect** or **Prevent** options, or enabling the blocklist) as configured in the host’s associated Elastic Defend integration policy. Use these parameters:

- `--path`: (Required) The absolute path to a file or directory to be scanned.

Required privilege: **Scan Operations**

Example: `scan --path "/Users/username/Downloads" --comment "Scan Downloads folder for malware"`

> **Note:**
>
> Scanning can take longer for directories containing a lot of files.

### `runscript`

Run a script on a host.

#### CrowdStrike

For CrowdStrike, you must include one of the following parameters to identify the script you want to run:

- `--Raw`: The full script content provided directly as a string.
- `--CloudFile`: The name of the script stored in a cloud storage location. When using this parameter, select from a list of saved custom scripts.
- `--HostPath`: The absolute or relative file path of the script located on the host machine.

You can also use these optional parameters:

- `--CommandLine`: Additional command-line arguments passed to the script to customize its execution.
- `--Timeout`: The maximum duration, in seconds, that the script can run before it’s forcibly stopped. If no timeout is specified, it defaults to 60 seconds.

Required privilege: **Execute Operations**

Examples:

`runscript --CloudFile="CloudScript1.ps1" --CommandLine="-Verbose true" --Timeout=180`

````text
runscript --Raw=```Get-ChildItem.```
````

`runscript --HostPath="C:\temp\LocalScript.ps1" --CommandLine="-Verbose true"`

#### Microsoft Defender for Endpoint

For Microsoft Defender for Endpoint, you must include the following parameter to identify the script you want to run:

- `--ScriptName`: The name of the script stored in a cloud storage location. Select from a list of saved custom scripts.

You can also use this optional parameter:

- `--Args`: Additional command-line arguments passed to the script to customize its execution.

  > **Note:**
  >
  > The response console does not support double-dash (`--`) syntax within the `--Args` parameter.

Required privilege: **Execute Operations**

Example: `runscript --ScriptName="Script2.sh" --Args="-Verbose true"`

## Supporting commands and parameters

### `--comment`

Add to a command to include a comment explaining or describing the action. Comments are included in the response actions history.

### `--help`

Add to a command to get help for that command.

Example: `isolate --help`

### `clear`

Clear all output from the response console.

### `help`

List supported commands in the console output area.

> **Tip:**
>
> You can also get a list of commands in the [Help panel](https://www.elastic.co/guide/en/security/8.19/response-actions.html#help-panel "Help panel"), which stays on the screen independently of the output area.

## Help panel

Click the circular Help icon labeled **Help** in the upper-right to open the **Help** panel, which lists available response action commands and parameters as a reference.

> **Note:**
>
> This panel displays only the response actions that the user has privileges to perform.

**Help panel description:** The Help panel lists available response action commands with a plus-sign add button beside each command. Visible examples include `isolate`, `release`, `status`, `processes`, `kill-process --pid`, `suspend-process --pid`, `get-file --path`, `execute --command`, `upload --file`, and `scan --path`. It also lists supporting commands and parameters such as `--comment`.

You can use this panel to build commands with less typing. Click the add icon, shown as a plus sign in a circle, to add a command to the input area. Then enter any additional parameters or a comment, and press **Return** to run the command.

If the endpoint is running an older version of Elastic Agent, some response actions may not be supported, as indicated by an informational icon and tooltip. [Upgrade Elastic Agent](https://www.elastic.co/guide/en/fleet/8.19/upgrade-elastic-agent.html) on the endpoint to be able to use the latest response actions.

**Unsupported-action description:** Unsupported response actions are marked with a warning triangle. Hovering over the related indicator shows a tooltip that says **Unsupported command**.

## Response actions history

Click **Response actions history** to display a log of the response actions performed on the endpoint, such as isolating a host or terminating a process. You can filter the information displayed in this view. Refer to [*Response actions history*](https://www.elastic.co/guide/en/security/8.19/response-actions-history.html "Response actions history") for more details.

**Response actions history description:** The history view shows filters for username, action, status, type, and time range, followed by a table of actions. The table includes columns such as **Time**, **Command**, **User**, **Comments**, and **Status**. Example rows show commands such as `release`, `isolate`, and `processes` with a **Successful** status.
