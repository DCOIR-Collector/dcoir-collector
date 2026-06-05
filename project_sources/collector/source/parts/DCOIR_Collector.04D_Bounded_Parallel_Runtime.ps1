<#
.SYNOPSIS
DCOIR collector bounded parallel runtime helpers.

.DESCRIPTION
Implements the bounded Windows PowerShell 5.1-safe parallel baseline runtime, including
worker definitions, cache initialization, overlap proof generation, and serial fallback
behavior for steps that are not safely satisfied by worker output.

.FILE NAME
DCOIR_Collector.04D_Bounded_Parallel_Runtime.ps1

.INPUTS
Collector state hashtable, baseline worker definitions, command strings, step names,
and allowed exit-code lists.

.OUTPUTS
Worker proof artifacts, cached command output text, collector notes/errors, and serial
or cached command text returned to the caller.
#>

$Global:ParallelBaselineCommandCache = @{}
$Global:ParallelBaselineWorkerArtifacts = New-Object System.Collections.ArrayList
$Global:ParallelExecutionProofPath = $null

<#
.SYNOPSIS
Resets all bounded parallel runtime caches and proof paths.

.DESCRIPTION
Clears the worker command cache, worker artifact list, and proof path so a collect run
starts with a clean bounded-parallel-runtime state.

.FUNCTION NAME
Reset-ParallelBaselineCache

.INPUTS
No direct parameters.

.OUTPUTS
No direct output. Resets global parallel-runtime state.
#>
function Reset-ParallelBaselineCache {
  $Global:ParallelBaselineCommandCache = @{}
  $Global:ParallelBaselineWorkerArtifacts = New-Object System.Collections.ArrayList
  $Global:ParallelExecutionProofPath = $null
}

<#
.SYNOPSIS
Runs one command serially and returns its combined text output.

.DESCRIPTION
Calls the standard cmd capture helper for a single step and returns the combined stdout,
stderr, command, and exit-code text surface.

.FUNCTION NAME
Get-SerialCmdText

.INPUTS
Command string, StepName string, and optional allowed exit-code list.

.OUTPUTS
String containing the combined captured process output.
#>
function Get-SerialCmdText {
  param(
    [string]$Command,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  $result = Invoke-CmdCapture -Command $Command -StepName $StepName -AllowedExitCodes $AllowedExitCodes
  return (Get-CombinedProcessOutput -Result $result)
}

<#
.SYNOPSIS
Returns the bounded parallel baseline worker definitions.

.DESCRIPTION
Defines the small, read-only worker groups that can run in parallel during collect mode,
including their step names, command strings, and allowed exit codes.

.FUNCTION NAME
Get-ParallelBaselineWorkerDefinitions

.INPUTS
No direct parameters.

.OUTPUTS
Array of ordered worker-definition hashtables.
#>
function Get-ParallelBaselineWorkerDefinitions {
  return @(
    [ordered]@{
      Name = 'host_baseline'
      Steps = @(
        [ordered]@{ StepName = 'HOST_DATE_TIME_HOSTNAME'; Command = 'date /t & time /t & hostname & ver'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'HOST_SYSTEMINFO'; Command = 'systeminfo'; AllowedExitCodes = @(0) }
      )
    },
    [ordered]@{
      Name = 'identity_context'
      Steps = @(
        [ordered]@{ StepName = 'IDENTITY_WHOAMI_ALL'; Command = 'whoami /all'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'IDENTITY_QUERY_USER_QWINSTA'; Command = 'query user & qwinsta'; AllowedExitCodes = @(0,1) }
      )
    },
    [ordered]@{
      Name = 'network_light'
      Steps = @(
        [ordered]@{ StepName = 'NETWORK_IPCONFIG'; Command = 'ipconfig /all'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'NETWORK_DNS_CACHE'; Command = 'ipconfig /displaydns'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'NETWORK_ROUTE_PRINT'; Command = 'route print'; AllowedExitCodes = @(0) },
        [ordered]@{ StepName = 'NETWORK_ARP_A'; Command = 'arp -a'; AllowedExitCodes = @(0) }
      )
    },
    [ordered]@{
      Name = 'security_posture'
      Steps = @(
        [ordered]@{ StepName = 'SECURITY_FIREWALL_PROFILES'; Command = 'netsh advfirewall show allprofiles'; AllowedExitCodes = @(0) }
      )
    }
  )
}

<#
.SYNOPSIS
Initializes the bounded parallel baseline runtime for a collect run.

.DESCRIPTION
Resets the global cache, starts the bounded worker jobs during collect mode, harvests
successful worker output into the cache, writes the overlap-proof artifact, records
fallback notes for unsuccessful worker steps, and cleans up the background jobs.

.FUNCTION NAME
Initialize-ParallelBaselineCache

.INPUTS
Collector state hashtable used to locate the artifacts directory and store the proof
artifact path.

.OUTPUTS
No direct return value. Updates global cache state, proof artifacts, and collector
notes/errors.
#>
function Initialize-ParallelBaselineCache {
  param([hashtable]$State)

  Reset-ParallelBaselineCache

  if ($Mode -ne 'Collect') { return }

  $workerDefinitions = @(Get-ParallelBaselineWorkerDefinitions)
  if (@($workerDefinitions).Count -lt 2) {
    Add-CollectorNote 'Parallel baseline runtime definitions were insufficient; collector will remain serial for this run.'
    return
  }

  $workerDir = Join-Path $State.ArtifactsDir 'parallel_workers'
  Ensure-Directory -Path $workerDir

  $workerScript = {
    param([hashtable]$WorkerDefinition,[string]$ParallelWorkerDir)

    <#
    .SYNOPSIS
    Captures one bounded-parallel worker step inside the background job.

    .DESCRIPTION
    Starts cmd.exe for the provided worker step definition, captures stdout and stderr,
    evaluates the exit code against the step's allowed list, and returns the normalized
    step-result object that is later written into the worker proof artifact.

    .FUNCTION NAME
    Invoke-WorkerCommandCapture

    .INPUTS
    StepDefinition hashtable containing StepName, Command, and AllowedExitCodes.

    .OUTPUTS
    Ordered hashtable describing the captured step output, exit code, allowed-exit-code
    evaluation, and combined text surface.
    #>
    function Invoke-WorkerCommandCapture {
      param([hashtable]$StepDefinition)

      $psi = New-Object System.Diagnostics.ProcessStartInfo
      $psi.FileName = 'cmd.exe'
      $psi.Arguments = ('/c ' + [string]$StepDefinition.Command)
      $psi.UseShellExecute = $false
      $psi.RedirectStandardOutput = $true
      $psi.RedirectStandardError = $true
      $psi.CreateNoWindow = $true

      $proc = New-Object System.Diagnostics.Process
      $proc.StartInfo = $psi
      [void]$proc.Start()
      $stdout = $proc.StandardOutput.ReadToEnd()
      $stderr = $proc.StandardError.ReadToEnd()
      $proc.WaitForExit()

      $allowed = @($StepDefinition.AllowedExitCodes)
      if (@($allowed).Count -eq 0) { $allowed = @(0) }
      $withinAllowed = (@($allowed) -contains [int]$proc.ExitCode)

      $lines = New-Object System.Collections.ArrayList
      [void]$lines.Add(('COMMAND={0}' -f [string]$StepDefinition.Command))
      [void]$lines.Add(('EXIT_CODE={0}' -f [int]$proc.ExitCode))
      [void]$lines.Add('')
      [void]$lines.Add('STDOUT:')
      [void]$lines.Add($stdout)
      [void]$lines.Add('')
      [void]$lines.Add('STDERR:')
      [void]$lines.Add($stderr)

      return [ordered]@{
        step_name = [string]$StepDefinition.StepName
        command = [string]$StepDefinition.Command
        exit_code = [int]$proc.ExitCode
        allowed_exit_codes = @($allowed)
        within_allowed_exit_codes = [bool]$withinAllowed
        text = ($lines -join [Environment]::NewLine)
      }
    }

    $started = Get-Date
    $stepResults = New-Object System.Collections.ArrayList
    foreach ($stepDefinition in @($WorkerDefinition.Steps)) {
      [void]$stepResults.Add((Invoke-WorkerCommandCapture -StepDefinition $stepDefinition))
    }
    $ended = Get-Date

    $status = 'OK'
    if (@($stepResults | Where-Object { -not $_.within_allowed_exit_codes }).Count -gt 0) {
      $status = 'PARTIAL_SUCCESS'
    }

    $workerResult = [ordered]@{
      worker_name = [string]$WorkerDefinition.Name
      status = $status
      start_time_utc = $started.ToUniversalTime().ToString('o')
      end_time_utc = $ended.ToUniversalTime().ToString('o')
      duration_ms = [int][Math]::Round(($ended - $started).TotalMilliseconds)
      worker_pid = $PID
      step_results = @($stepResults)
    }

    $resultPath = Join-Path $ParallelWorkerDir ('parallel_worker_{0}.json.txt' -f [string]$WorkerDefinition.Name)
    Set-Content -Path $resultPath -Value (($workerResult | ConvertTo-Json -Depth 10) + [Environment]::NewLine) -Encoding UTF8 -ErrorAction Stop
    return $resultPath
  }

  $jobs = @()
  try {
    foreach ($definition in $workerDefinitions) {
      $jobs += Start-Job -Name ('DCOIR_{0}' -f $definition.Name) -ScriptBlock $workerScript -ArgumentList $definition, $workerDir
    }

    if (@($jobs).Count -eq 0) {
      Add-CollectorNote 'Parallel baseline runtime could not start any workers; collector will remain serial for this run.'
      return
    }

    Wait-Job -Job $jobs | Out-Null

    $workerObjects = New-Object System.Collections.ArrayList
    foreach ($job in @($jobs)) {
      try {
        $jobOutput = @(Receive-Job -Job $job -ErrorAction Stop)
        foreach ($resultPath in $jobOutput) {
          if (-not [string]::IsNullOrWhiteSpace([string]$resultPath) -and (Test-Path -LiteralPath $resultPath)) {
            [void]$Global:ParallelBaselineWorkerArtifacts.Add([string]$resultPath)
            $workerObject = Get-Content -LiteralPath $resultPath -Raw -ErrorAction Stop | ConvertFrom-Json
            [void]$workerObjects.Add($workerObject)
            foreach ($stepResult in @($workerObject.step_results)) {
              if ($stepResult.within_allowed_exit_codes) {
                $Global:ParallelBaselineCommandCache[[string]$stepResult.step_name] = [string]$stepResult.text
              } else {
                Add-CollectorNote ('Parallel worker [{0}] captured step [{1}] with exit code [{2}]; that step will fall back to serial execution when needed.' -f $workerObject.worker_name, $stepResult.step_name, $stepResult.exit_code)
              }
            }
          }
        }
      } catch {
        Add-CollectorError ('Parallel baseline worker job [{0}] failed: {1}' -f $job.Name, $_.Exception.Message)
      }
    }

    $workerResults = @($workerObjects | Sort-Object start_time_utc, worker_name)
    $overlaps = New-Object System.Collections.ArrayList
    for ($i = 0; $i -lt @($workerResults).Count; $i++) {
      for ($j = $i + 1; $j -lt @($workerResults).Count; $j++) {
        $left = $workerResults[$i]
        $right = $workerResults[$j]
        $leftStart = [datetime]::Parse([string]$left.start_time_utc)
        $leftEnd = [datetime]::Parse([string]$left.end_time_utc)
        $rightStart = [datetime]::Parse([string]$right.start_time_utc)
        $rightEnd = [datetime]::Parse([string]$right.end_time_utc)
        if (($leftStart -lt $rightEnd) -and ($rightStart -lt $leftEnd)) {
          [void]$overlaps.Add([ordered]@{
            left_worker = [string]$left.worker_name
            right_worker = [string]$right.worker_name
            left_start_utc = [string]$left.start_time_utc
            left_end_utc = [string]$left.end_time_utc
            right_start_utc = [string]$right.start_time_utc
            right_end_utc = [string]$right.end_time_utc
          })
        }
      }
    }

    $proofStatus = if (@($workerResults).Count -ge 2 -and @($overlaps).Count -gt 0) { 'OVERLAP_CONFIRMED' } else { 'NO_OVERLAP_OBSERVED' }
    $proofObject = [ordered]@{
      proof_status = $proofStatus
      implementation_mode = 'bounded_parallel_jobs'
      deterministic_post_processing = 'Parent waits for all parallel worker jobs before baseline report assembly continues.'
      worker_count = @($workerResults).Count
      cached_step_count = @($Global:ParallelBaselineCommandCache.Keys).Count
      worker_artifact_paths = @($Global:ParallelBaselineWorkerArtifacts)
      worker_results = $workerResults
      overlapping_pairs = @($overlaps)
    }

    $proofPath = Write-ArtifactText -ArtifactsDir $State.ArtifactsDir -Section 'PARALLEL_EXECUTION' -Name 'parallel_execution_proof.json.txt' -Text (Convert-ToSafeJsonText -InputObject $proofObject)
    $Global:ParallelExecutionProofPath = $proofPath
    $State.ParallelExecutionProofPath = $proofPath

    if ($proofStatus -eq 'OVERLAP_CONFIRMED') {
      Add-CollectorNote ('Bounded parallel baseline workers executed with observed overlap across {0} worker pair(s).' -f @($overlaps).Count)
    } else {
      Add-CollectorNote 'Bounded parallel baseline workers ran, but explicit timing overlap was not observed in this run.'
    }
  } catch {
    Add-CollectorError ('Failed to initialize bounded parallel baseline runtime: {0}' -f $_.Exception.Message)
  } finally {
    foreach ($job in @($jobs)) {
      try { Remove-Job -Job $job -Force -ErrorAction SilentlyContinue } catch { }
    }
  }
}

<#
.SYNOPSIS
Returns cached worker output when available or runs the command serially.

.DESCRIPTION
Looks for the requested step name in the bounded parallel baseline command cache and
returns that cached text when present. If no cached result exists, it falls back to the
standard serial command capture path.

.FUNCTION NAME
Get-CmdText

.INPUTS
Command string, StepName string, and optional allowed exit-code list.

.OUTPUTS
String containing cached worker text or combined serial command output.
#>
function Get-CmdText {
  param(
    [string]$Command,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )

  if ($Global:ParallelBaselineCommandCache -and $StepName -and $Global:ParallelBaselineCommandCache.ContainsKey($StepName)) {
    return [string]$Global:ParallelBaselineCommandCache[$StepName]
  }

  return (Get-SerialCmdText -Command $Command -StepName $StepName -AllowedExitCodes $AllowedExitCodes)
}
