# Runtime Reference Patterns

For variable `VAR_NAME`, use this JSON pattern in `reference_additional_runtimes_json`:

```json
{
  "javascript": "process.env.VAR_NAME",
  "node_js": "process.env.VAR_NAME",
  "typescript": "process.env.VAR_NAME",
  "rust": "std::env::var(\"VAR_NAME\")",
  "go": "os.Getenv(\"VAR_NAME\")",
  "dotnet_csharp": "Environment.GetEnvironmentVariable(\"VAR_NAME\", EnvironmentVariableTarget.Machine)",
  "java": "System.getenv(\"VAR_NAME\")",
  "ruby": "ENV[\"VAR_NAME\"]",
  "php": "getenv(\"VAR_NAME\")",
  "r": "Sys.getenv(\"VAR_NAME\")",
  "vba": "Environ$(\"VAR_NAME\")",
  "docker_cli_env": "-e VAR_NAME",
  "container_shell": "$VAR_NAME",
  "wsl_bridge": "$VAR_NAME after export from Windows"
}
```

PowerShell/cmd/bash/Python fields should normally be separate table fields:
- PowerShell: `[Environment]::GetEnvironmentVariable('VAR_NAME','Machine')`
- cmd: `%VAR_NAME%`
- WSL/bash: `$VAR_NAME`
- Python: `os.environ.get('VAR_NAME')`
