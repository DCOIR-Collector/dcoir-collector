$Global:ParallelBaselineCommandCache = @{}
$Global:ParallelBaselineWorkerArtifacts = New-Object System.Collections.ArrayList
$Global:ParallelExecutionProofPath = $null

function Reset-ParallelBaselineCache {
  $Global:ParallelBaselineCommandCache = @{}
  $Global:ParallelBaselineWorkerArtifacts = New-Object System.Collections.ArrayList
  $Global:ParallelExecutionProofPath = $null
}

function Get-SerialCmdText {
  param(
    [string]$Command,
    [string]$StepName,
    [int[]]$AllowedExitCodes = @(0)
  )
  $result = Invoke-CmdCapture -Command $Command -StepName $StepName -AllowedExitCodes $AllowedExitCodes
  return (Get-CombinedProcessOutput -Result $result)
}

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
    Set-Content -Path $resultPath -Value (($workerResult | ConvertTo-Json -Depth 10) + [Environment]::NewLine) -Encoding UTF8
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
            $workerObject = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
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
