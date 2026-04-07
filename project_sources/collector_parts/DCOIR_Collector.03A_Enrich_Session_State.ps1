function Get-SessionById {
  param([hashtable]$State,[string]$SessionId)
  foreach ($session in @($State.EnrichSessions)) {
    if ($session.SessionId -eq $SessionId) { return $session }
  }
  return $null
}

function Initialize-EnrichSession {
  param(
    [hashtable]$State,
    [string]$RequestedSessionId,
    [switch]$ForceNew
  )

  if (-not $State.ContainsKey("EnrichSessions") -or $null -eq $State.EnrichSessions) {
    $State.EnrichSessions = @()
  } else {
    $State.EnrichSessions = @($State.EnrichSessions)
  }
  if (-not $State.ContainsKey("EnrichSessionCounter") -or $null -eq $State.EnrichSessionCounter) {
    $State.EnrichSessionCounter = 0
  }

  if (-not $State.ContainsKey('LastSessionResolutionMode')) {
    $State.LastSessionResolutionMode = $null
  }

  if (-not [string]::IsNullOrWhiteSpace($RequestedSessionId)) {
    $existing = Get-SessionById -State $State -SessionId $RequestedSessionId
    if ($existing) {
      $existing.SessionResolutionMode = 'REUSED_REQUESTED_SESSION'
      $State.LastSessionResolutionMode = 'REUSED_REQUESTED_SESSION'
      return $existing
    }
    throw "Requested enrichment session was not found: $RequestedSessionId"
  }

  if (-not $ForceNew -and -not [string]::IsNullOrWhiteSpace([string]$State.OpenEnrichSessionId)) {
    $open = Get-SessionById -State $State -SessionId ([string]$State.OpenEnrichSessionId)
    if ($open -and -not $open.Finalized) {
      $open.SessionResolutionMode = 'REUSED_OPEN_SESSION'
      $State.LastSessionResolutionMode = 'REUSED_OPEN_SESSION'
      return $open
    }
  }

  $State.EnrichSessionCounter = [int]$State.EnrichSessionCounter + 1
  $sessionNumber = "{0:D3}" -f [int]$State.EnrichSessionCounter
  $sessionStamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $sessionId = "ENRICH_{0}_{1}" -f $sessionNumber, $sessionStamp

  $sessionRoot = Join-Path $State.EnrichSessionsDir $sessionId
  $sessionArtifactsDir = Join-Path $sessionRoot "artifacts"
  $sessionStagedDir = Join-Path $sessionRoot "staged"
  $sessionLogsDir = Join-Path $sessionRoot "logs"
  Ensure-Directory -Path $sessionRoot
  Ensure-Directory -Path $sessionArtifactsDir
  Ensure-Directory -Path $sessionStagedDir
  Ensure-Directory -Path $sessionLogsDir

  $session = @{
    SessionId = $sessionId
    SessionRoot = $sessionRoot
    ArtifactsDir = $sessionArtifactsDir
    StagedDir = $sessionStagedDir
    LogsDir = $sessionLogsDir
    SummaryPath = (Join-Path $sessionRoot ("DCOIR_ENRICH_SUMMARY_{0}_{1}_{2}.txt" -f $sessionId, $env:COMPUTERNAME, $State.RunId))
    ManifestPath = (Join-Path $sessionRoot ("manifest_{0}.json" -f $sessionId))
    BundlePath = $null
    CreatedLocal = (Get-Date).ToString("o")
    Finalized = $false
    ActionCount = 0
    SessionResolutionMode = 'CREATED_NEW_SESSION'
  }

  $State.EnrichSessions = @($State.EnrichSessions) + @($session)
  $State.OpenEnrichSessionId = $sessionId
  $State.LastSessionResolutionMode = 'CREATED_NEW_SESSION'

  $header = @(
    "CollectorVersion=$ScriptVersion"
    "Mode=Enrich"
    "RunId=$($State.RunId)"
    "EnrichSessionId=$sessionId"
    "SessionResolutionMode=CREATED_NEW_SESSION"
    "Host=$env:COMPUTERNAME"
    "SessionCreatedLocal=$(Get-Date -Format o)"
    "SessionRoot=$sessionRoot"
  ) -join [Environment]::NewLine
  Set-Content -Path $session.SummaryPath -Value $header -Encoding UTF8

  return $session
}

function Finalize-EnrichSession {
  param(
    [hashtable]$State,
    [hashtable]$Session,
    [hashtable]$ToolMap
  )

  $manifest = New-Manifest -ManifestPath $Session.ManifestPath -State $State -ModeName "Enrich" -TierName $Tier -Files (
    @($Session.SummaryPath) +
    @(Get-ChildItem -LiteralPath $Session.ArtifactsDir -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) +
    @(Get-ChildItem -LiteralPath $Session.StagedDir -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName }) +
    @(Get-ChildItem -LiteralPath $Session.LogsDir -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })
  ) -ToolMap $ToolMap -Extra @{
    enrich_session_id = $Session.SessionId
    action_count = $Session.ActionCount
    session_resolution_mode = $Session.SessionResolutionMode
    append_model = 'enrich-start creates a new session; enrich-add reuses the current open session unless explicitly overridden; enrich-finalize finalizes the current open session.'
  }

  $bundleInputs = @(
    $Session.SummaryPath,
    $Session.ArtifactsDir,
    $Session.StagedDir,
    $Session.LogsDir,
    $manifest
  )

  $bundlePath = New-BundleZip -BundlesDir $State.BundlesDir -BundleName ("DCOIR_ENRICH_BUNDLE_{0}_{1}_{2}.zip" -f $Session.SessionId, $env:COMPUTERNAME, $State.RunId) -Paths $bundleInputs
  $Session.BundlePath = $bundlePath
  $Session.Finalized = $true
  if ($State.OpenEnrichSessionId -eq $Session.SessionId) {
    $State.OpenEnrichSessionId = $null
  }
  return $bundlePath
}
