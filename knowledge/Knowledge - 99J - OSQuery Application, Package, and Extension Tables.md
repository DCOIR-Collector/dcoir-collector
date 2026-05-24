# Knowledge - 99J - OSQuery Application, Package, and Extension Tables

_Exact OSQuery application, package, browser-extension, and program-inventory reference tables._

**Summary:** This page preserves the exact OSQuery source markdown for the tables in this shard. Use it as the governed exact-name reference for table and field lookup.

---

### app_schemes

**Platforms:** MacOS

macOS application schemes and handlers (e.g., http, file, mailto).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| scheme | TEXT | Name of the scheme/protocol |
| handler | TEXT | Application label for the handler |
| enabled | INTEGER | 1 if this handler is the OS default, else 0 |
| external | INTEGER | 1 if this handler does NOT exist on macOS by default, else 0 |
| protected | INTEGER | 1 if this handler is protected (reserved) by macOS, else 0 |

### apps

**Platforms:** MacOS

macOS applications installed in known search paths (e.g., /Applications).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the Name.app folder |
| path | TEXT | Absolute and full Name.app path |
| bundle_executable | TEXT | Info properties CFBundleExecutable label |
| bundle_identifier | TEXT | Info properties CFBundleIdentifier label |
| bundle_name | TEXT | Info properties CFBundleName label |
| bundle_short_version | TEXT | Info properties CFBundleShortVersionString label |
| bundle_version | TEXT | Info properties CFBundleVersion label |
| bundle_package_type | TEXT | Info properties CFBundlePackageType label |
| environment | TEXT | Application-set environment variables |
| element | TEXT | Does the app identify as a background agent |
| compiler | TEXT | Info properties DTCompiler label |
| development_region | TEXT | Info properties CFBundleDevelopmentRegion label |
| display_name | TEXT | Info properties CFBundleDisplayName label |
| info_string | TEXT | Info properties CFBundleGetInfoString label |
| minimum_system_version | TEXT | Minimum version of macOS required for the app to run |
| category | TEXT | The UTI that categorizes the app for the App Store |
| applescript_enabled | TEXT | Info properties NSAppleScriptEnabled label |
| copyright | TEXT | Info properties NSHumanReadableCopyright label |
| last_opened_time | DOUBLE | The time that the app was last used |

### apt_sources

**Platforms:** Linux

Current list of APT repositories or software channels.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Repository name |
| source | TEXT | Source file |
| base_uri | TEXT | Repository base URI |
| release | TEXT | Release name |
| version | TEXT | Repository source version |
| maintainer | TEXT | Repository maintainer |
| components | TEXT | Repository components |
| architectures | TEXT | Repository architectures |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### chocolatey_packages

**Platforms:** Windows

Chocolatey packages installed in a system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Package display name |
| version | TEXT | Package-supplied version |
| summary | TEXT | Package-supplied summary |
| author | TEXT | Optional package author |
| license | TEXT | License under which package is launched |
| path | TEXT | Path at which this package resides |

### chrome_extensions

**Platforms:** MacOS Linux Windows

Chrome-based browser extensions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| browser_type | TEXT | The browser type (Valid values: chrome, chromium, opera, yandex, brave, edge, edge_beta) |
| uid | BIGINT | The local user that owns the extension |
| name | TEXT | Extension display name |
| profile | TEXT | The name of the Chrome profile that contains this extension |
| profile_path | TEXT | The profile path |
| referenced_identifier | TEXT | Extension identifier, as specified by the preferences file. Empty if the extension is not in the profile. |
| identifier | TEXT | Extension identifier, computed from its manifest. Empty in case of error. |
| version | TEXT | Extension-supplied version |
| description | TEXT | Extension-optional description |
| default_locale | TEXT | Default locale supported by extension |
| current_locale | TEXT | Current locale supported by extension |
| update_url | TEXT | Extension-supplied update URI |
| author | TEXT | Optional extension author |
| persistent | INTEGER | 1 If extension is persistent across all tabs else 0 |
| path | TEXT | Path to extension folder |
| permissions | TEXT | The permissions required by the extension |
| permissions_json | TEXT | The JSON-encoded permissions required by the extension |
| optional_permissions | TEXT | The permissions optionally required by the extensions |
| optional_permissions_json | TEXT | The JSON-encoded permissions optionally required by the extensions |
| manifest_hash | TEXT | The SHA256 hash of the manifest.json file |
| referenced | BIGINT | 1 if this extension is referenced by the Preferences file of the profile |
| from_webstore | TEXT | True if this extension was installed from the web store |
| state | TEXT | 1 if this extension is enabled |
| install_time | TEXT | Extension install time, in its original Webkit format |
| install_timestamp | BIGINT | Extension install time, converted to unix time |
| manifest_json | TEXT | The manifest file of the extension |
| key | TEXT | The extension key, from the manifest file |

### cups_destinations

**Platforms:** MacOS

Returns all configured printers.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the printer |
| option_name | TEXT | Option name |
| option_value | TEXT | Option value |

### cups_jobs

**Platforms:** MacOS

Returns all completed print jobs from cups.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| title | TEXT | Title of the printed job |
| destination | TEXT | The printer the job was sent to |
| user | TEXT | The user who printed the job |
| format | TEXT | The format of the print job |
| size | INTEGER | The size of the print job |
| completed_time | INTEGER | When the job completed printing |
| processing_time | INTEGER | How long the job took to process |
| creation_time | INTEGER | When the print request was initiated |

### deb_packages

**Platforms:** Linux

The installed DEB package database.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Package name |
| version | TEXT | Package version |
| source | TEXT | Package source |
| size | BIGINT | Package size in bytes |
| arch | TEXT | Package architecture |
| revision | TEXT | Package revision |
| status | TEXT | Package status |
| maintainer | TEXT | Package maintainer |
| section | TEXT | Package section |
| priority | TEXT | Package priority |
| admindir | TEXT | libdpkg admindir. Defaults to /var/lib/dpkg |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| mount_namespace_id | TEXT | Mount namespace id |

### firefox_addons

**Platforms:** MacOS Linux Windows

Firefox browser extensions, webapps, and addons.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local user that owns the addon |
| name | TEXT | Addon display name |
| identifier | TEXT | Addon identifier |
| creator | TEXT | Addon-supported creator string |
| type | TEXT | Extension, addon, webapp |
| version | TEXT | Addon-supplied version string |
| description | TEXT | Addon-supplied description string |
| source_url | TEXT | URL that installed the addon |
| visible | INTEGER | 1 If the addon is shown in browser else 0 |
| active | INTEGER | 1 If the addon is active else 0 |
| disabled | INTEGER | 1 If the addon is application-disabled else 0 |
| autoupdate | INTEGER | 1 If the addon applies background updates else 0 |
| location | TEXT | Global, profile location |
| path | TEXT | Path to plugin bundle |

### homebrew_packages

**Platforms:** MacOS

The installed homebrew package database.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Package name |
| path | TEXT | Package install path |
| version | TEXT | Current 'linked' version |
| type | TEXT | Package type ('formula' or 'cask') |
| auto_updates | INTEGER | 1 if the cask auto-updates otherwise 0 |
| app_name | TEXT | Name of the installed App (for Casks) |
| prefix | TEXT | Homebrew install prefix |

### ie_extensions

**Platforms:** Windows

Internet Explorer browser extensions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Extension display name |
| registry_path | TEXT | Extension identifier |
| version | TEXT | Version of the executable |
| path | TEXT | Path to executable |

### jetbrains_plugins

**Platforms:** MacOS Linux Windows

JetBrains IDEs plugins.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| product_type | TEXT | The product type (Valid values: CLion, DataGrip, GoLand, IntelliJIdea, IntelliJIdeaCommunityEdition, PhpStorm, PyCharm, PyCharmCommunityEdition, ReSharper, Rider, RubyMine, RustRover, WebStorm) |
| uid | BIGINT | The local user that owns the plugin |
| name | TEXT | Name of the plugin (Title Case) |
| version | TEXT | Version of the plugin |
| vendor | TEXT | The vendor name or organization id that authored the plugin |
| path | TEXT | The path on the filesystem for the plugin. This may be a folder or a jar filename |

### npm_packages

**Platforms:** MacOS Linux Windows

Node packages installed in a system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Package display name |
| version | TEXT | Package-supplied version |
| description | TEXT | Package-supplied description |
| author | TEXT | Package-supplied author |
| license | TEXT | License under which package is launched |
| homepage | TEXT | Package supplied homepage |
| path | TEXT | Path at which this module resides |
| directory | TEXT | Directory where node_modules are located |
| depth | INTEGER | Nesting depth of the package (0 = direct dependency) |
| max_depth | INTEGER | Maximum depth to search for nested packages (default 100, -1 = unlimited) |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| mount_namespace_id | TEXT | Mount namespace id |

### package_receipts

**Platforms:** MacOS

macOS package receipt details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package_id | TEXT | Package domain identifier |
| package_filename | TEXT | Filename of original .pkg file |
| version | TEXT | Installed package version |
| location | TEXT | Optional relative install path on volume |
| install_time | DOUBLE | Timestamp of install time |
| installer_name | TEXT | Name of installer process |
| path | TEXT | Path of receipt plist |

### patches

**Platforms:** Windows

Lists all the patches applied. Note: This does not include patches applied via MSI or downloaded from Windows Update (e.g. Service Packs).

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| csname | TEXT | The name of the host the patch is installed on. |
| hotfix_id | TEXT | The KB ID of the patch. |
| caption | TEXT | Short description of the patch. |
| description | TEXT | Fuller description of the patch. |
| fix_comments | TEXT | Additional comments about the patch. |
| installed_by | TEXT | The system context in which the patch as installed. |
| install_date | TEXT | Indicates when the patch was installed. Lack of a value does not indicate that the patch was not installed. |
| installed_on | TEXT | The date when the patch was installed. |

### portage_keywords

**Platforms:** Linux

A summary about portage configurations like keywords, mask and unmask.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package | TEXT | Package name |
| version | TEXT | The version which are affected by the use flags, empty means all |
| keyword | TEXT | The keyword applied to the package |
| mask | INTEGER | If the package is masked |
| unmask | INTEGER | If the package is unmasked |

### portage_packages

**Platforms:** Linux

List of currently installed packages.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package | TEXT | Package name |
| version | TEXT | The version which are affected by the use flags, empty means all |
| slot | TEXT | The slot used by package |
| build_time | BIGINT | Unix time when package was built |
| repository | TEXT | From which repository the ebuild was used |
| eapi | BIGINT | The eapi for the ebuild |
| size | BIGINT | The size of the package |
| world | INTEGER | If package is in the world file |

### portage_use

**Platforms:** Linux

List of enabled portage USE values for specific package.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| package | TEXT | Package name |
| version | TEXT | The version of the installed package |
| use | TEXT | USE flag which has been enabled for package |

### programs

**Platforms:** Windows

Represents products as they are installed by Windows Installer. A product generally correlates to one installation package on Windows. Some fields may be blank as Windows installation details are left to the discretion of the product author.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Commonly used product name. |
| version | TEXT | Product version information. |
| install_location | TEXT | The installation location directory of the product. |
| install_source | TEXT | The installation source of the product. |
| language | TEXT | The language of the product. |
| publisher | TEXT | Name of the product supplier. |
| uninstall_string | TEXT | Path and filename of the uninstaller. |
| install_date | TEXT | Date that this product was installed on the system. |
| identifying_number | TEXT | Product identification such as a serial number on software, or a die number on a hardware chip. |
| package_family_name | TEXT | A combination of PackageName and PublisherHash that is used to uniquely identify applications across versions and architectures. |
| upgrade_code | TEXT | Specific to MSI applications, a GUID used to identify a product suite across multiple versions. |

### python_packages

**Platforms:** MacOS Linux Windows

Python packages installed in a system. NOTE: when querying on windows, even without a users cross join, all user installed python packages will be returned. This special behavior is to not break original functionality.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Package display name |
| uid | BIGINT | The local user that owns the python package |
| version | TEXT | Package-supplied version |
| summary | TEXT | Package-supplied summary |
| author | TEXT | Optional package author |
| license | TEXT | License under which package is launched |
| path | TEXT | Path at which this module resides |
| directory | TEXT | Directory where Python modules are located |
| pid_with_namespace | INTEGER | Pids that contain a namespace |

### rpm_packages

**Platforms:** Linux

RPM packages that are currently installed on the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | RPM package name |
| version | TEXT | Package version |
| release | TEXT | Package release |
| source | TEXT | Source RPM package name (optional) |
| size | BIGINT | Package size in bytes |
| sha1 | TEXT | SHA1 hash of the package contents |
| arch | TEXT | Architecture(s) supported |
| epoch | INTEGER | Package epoch value |
| install_time | INTEGER | When the package was installed |
| vendor | TEXT | Package vendor |
| package_group | TEXT | Package group |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
| mount_namespace_id | TEXT | Mount namespace id |

### running_apps

**Platforms:** MacOS

macOS applications currently running on the host system.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| pid | INTEGER | The pid of the application |
| bundle_identifier | TEXT | The bundle identifier of the application |
| is_active | INTEGER | (DEPRECATED) |

### safari_extensions

**Platforms:** MacOS

Safari browser extension details for all users. This table requires Full Disk Access (FDA) permission.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| uid | BIGINT | The local user that owns the extension |
| name | TEXT | Extension display name |
| identifier | TEXT | Extension identifier |
| version | TEXT | Extension long version |
| sdk | TEXT | Bundle SDK used to compile extension |
| description | TEXT | Optional extension description text |
| path | TEXT | Path to the Info.plist describing the extension |
| bundle_version | TEXT | The version of the build that identifies an iteration of the bundle |
| copyright | TEXT | A human-readable copyright notice for the bundle |

### vscode_extensions

**Platforms:** MacOS Linux Windows

Lists all vscode extensions.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Extension Name |
| uuid | TEXT | Extension UUID |
| version | TEXT | Extension version |
| path | TEXT | Extension path |
| publisher | TEXT | Publisher Name |
| publisher_id | TEXT | Publisher ID |
| installed_at | BIGINT | Installed Timestamp |
| prerelease | INTEGER | Pre release version |
| uid | BIGINT | The local user that owns the plugin |
| vscode_edition | TEXT | The VSCode edition (vscode, vscode_insiders, vscodium, vscodium_insiders, cursor, windsurf, trae) |

### windows_optional_features

**Platforms:** Windows

Lists names and installation states of windows features. Maps to Win32_OptionalFeature WMI class.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Name of the feature |
| caption | TEXT | Caption of feature in settings UI |
| state | INTEGER | Installation state value. 1 == Enabled, 2 == Disabled, 3 == Absent |
| statename | TEXT | Installation state name. 'Enabled','Disabled','Absent' |

### windows_search

**Platforms:** Windows

Run searches against the Windows system index database using Advanced Query Syntax. See https://learn.microsoft.com/en-us/windows/win32/search/-search-3x-advancedquerysyntax for details.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | The name of the item |
| path | TEXT | The full path of the item. |
| size | BIGINT | The item size in bytes. |
| date_created | INTEGER | The unix timestamp of when the item was created. |
| date_modified | INTEGER | The unix timestamp of when the item was last modified |
| owner | TEXT | The owner of the item |
| type | TEXT | The item type |
| properties | TEXT | Additional property values JSON |
| query | TEXT | Windows search query |
| sort | TEXT | Sort for windows api |
| max_results | INTEGER | Maximum number of results returned by windows api, set to -1 for unlimited |
| additional_properties | TEXT | Comma separated list of columns to include in properties JSON |

### windows_update_history

**Platforms:** Windows

Provides the history of the windows update events.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| client_app_id | TEXT | Identifier of the client application that processed an update |
| date | BIGINT | Date and the time an update was applied |
| description | TEXT | Description of an update |
| hresult | BIGINT | HRESULT value that is returned from the operation on an update |
| operation | TEXT | Operation on an update |
| result_code | TEXT | Result of an operation on an update |
| server_selection | TEXT | Value that indicates which server provided an update |
| service_id | TEXT | Service identifier of an update service that is not a Windows update |
| support_url | TEXT | Hyperlink to the language-specific support information for an update |
| title | TEXT | Title of an update |
| update_id | TEXT | Revision-independent identifier of an update |
| update_revision | BIGINT | Revision number of an update |

### yum_sources

**Platforms:** Linux

Current list of Yum repositories or software channels.

Improve this Description on Github

| Column | Type | Description |
|---|---|---|
| name | TEXT | Repository name |
| source | TEXT | Source file |
| baseurl | TEXT | Repository base URL |
| mirrorlist | TEXT | Mirrorlist URL |
| metalink | TEXT | Metalink URL |
| enabled | TEXT | Whether the repository is used |
| gpgcheck | TEXT | Whether packages are GPG checked |
| gpgkey | TEXT | URL to GPG key |
| pid_with_namespace | INTEGER | Pids that contain a namespace |
