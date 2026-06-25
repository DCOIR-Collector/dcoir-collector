Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'

function Join-DcoirPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Base,

    [Parameter(Mandatory = $true)]
    [string[]]$Parts
  )

  $path = $Base
  foreach ($part in $Parts) {
    $path = Join-Path $path $part
  }
  return $path
}

function Get-DcoirRepoRoot {
  $candidate = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
  while ($true) {
    $collectorEntry = Join-DcoirPath -Base $candidate -Parts @('project_sources','collector','source','DCOIR_Collector.ps1')
    if (Test-Path -LiteralPath $collectorEntry) {
      return $candidate
    }

    $parent = Split-Path -Parent $candidate
    if ([string]::IsNullOrWhiteSpace($parent) -or ($parent -eq $candidate)) {
      throw "Could not locate repository root from Pester path: $PSScriptRoot"
    }
    $candidate = $parent
  }
}

function Get-DcoirCollectorLayout {
  $repoRoot = Get-DcoirRepoRoot
  [pscustomobject]@{
    RepoRoot = $repoRoot
    CollectorRoot = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector')
    CollectorEntry = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','source','DCOIR_Collector.ps1')
    CollectorPartsDirectory = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','source','parts')
    CollectorManifest = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','manifests','Collector_Runtime_Package_Manifest.json')
    CollectorHarness = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','harness','run_DCOIR_Tests.ps1')
    HarnessAssembler = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','harness','assemble_run_DCOIR_Tests.ps1')
    HarnessPartsDirectory = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','harness','source','parts')
    PesterBoundaryJson = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','powershell_engine_pester_boundary.json')
    PesterBoundaryReport = Join-DcoirPath -Base $repoRoot -Parts @('project_sources','collector','powershell_engine_pester_boundary_report.md')
  }
}

function Read-DcoirText {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $resolved = (Resolve-Path -LiteralPath $Path).Path
  return [System.IO.File]::ReadAllText($resolved)
}

function Read-DcoirJson {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  return (Read-DcoirText -Path $Path | ConvertFrom-Json)
}

function Convert-DcoirBundleVersionToScriptVersion {
  param(
    [Parameter(Mandatory = $true)]
    [string]$BundleVersion
  )

  return ($BundleVersion -replace '_', '.')
}

function Get-DcoirWrapperPartNames {
  param(
    [Parameter(Mandatory = $true)]
    [string]$CollectorEntryPath
  )

  $text = Read-DcoirText -Path $CollectorEntryPath
  $match = [regex]::Match($text, '(?ms)^\s*\$collectorPartFiles\s*=\s*@\((?<body>.*?)^\s*\)')
  if (-not $match.Success) {
    throw 'Could not find $collectorPartFiles block in DCOIR_Collector.ps1.'
  }

  $names = New-Object System.Collections.ArrayList
  foreach ($nameMatch in [regex]::Matches($match.Groups['body'].Value, '"(?<name>DCOIR_Collector\.[^"]+\.ps1)"')) {
    [void]$names.Add([string]$nameMatch.Groups['name'].Value)
  }
  return @($names)
}

function Get-DcoirManifestPartPaths {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Manifest
  )

  return @($Manifest.collector_part_files | ForEach-Object { [string]$_ })
}

function Get-DcoirManifestPartNames {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Manifest
  )

  return @(Get-DcoirManifestPartPaths -Manifest $Manifest | ForEach-Object { Split-Path -Leaf $_ })
}

function Get-DcoirCollectorSourceFiles {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Layout,

    [Parameter(Mandatory = $true)]
    [object]$Manifest
  )

  $paths = New-Object System.Collections.ArrayList
  [void]$paths.Add($Layout.CollectorEntry)
  foreach ($relativePath in (Get-DcoirManifestPartPaths -Manifest $Manifest)) {
    $normalizedRelativePath = ([string]$relativePath) -replace '/', [System.IO.Path]::DirectorySeparatorChar
    [void]$paths.Add((Join-Path $Layout.RepoRoot $normalizedRelativePath))
  }
  return @($paths)
}

function Get-DcoirParsedFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $tokens = $null
  $parseErrors = $null
  $ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$parseErrors)
  [pscustomobject]@{
    Path = $Path
    Ast = $ast
    Tokens = $tokens
    Errors = @($parseErrors)
  }
}

function Get-DcoirEntryParameterAst {
  param(
    [Parameter(Mandatory = $true)]
    [System.Management.Automation.Language.Ast]$Ast,

    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $parameters = @($Ast.ParamBlock.Parameters | Where-Object { $_.Name.VariablePath.UserPath -eq $Name })
  if (@($parameters).Count -ne 1) {
    throw "Expected exactly one parameter named $Name, found $(@($parameters).Count)."
  }
  return $parameters[0]
}

function Get-DcoirAttributePositionalValues {
  param(
    [Parameter(Mandatory = $true)]
    [System.Management.Automation.Language.ParameterAst]$ParameterAst,

    [Parameter(Mandatory = $true)]
    [string]$AttributeName
  )

  $values = New-Object System.Collections.ArrayList
  foreach ($attribute in @($ParameterAst.Attributes)) {
    $typeName = [string]$attribute.TypeName.Name
    if (($typeName -ieq $AttributeName) -or ($typeName -ieq ($AttributeName + 'Attribute'))) {
      foreach ($argument in @($attribute.PositionalArguments)) {
        if ($argument -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
          [void]$values.Add([string]$argument.Value)
        } elseif ($argument -is [System.Management.Automation.Language.ConstantExpressionAst]) {
          [void]$values.Add([string]$argument.Value)
        }
      }
    }
  }
  return @($values)
}

function Get-DcoirScriptVersionFromWrapper {
  param(
    [Parameter(Mandatory = $true)]
    [string]$CollectorEntryPath
  )

  $text = Read-DcoirText -Path $CollectorEntryPath
  $match = [regex]::Match($text, '^\s*\$ScriptVersion\s*=\s*"(?<version>[^"]+)"', 'Multiline')
  if (-not $match.Success) {
    throw 'Could not find $ScriptVersion assignment in DCOIR_Collector.ps1.'
  }
  return [string]$match.Groups['version'].Value
}

function Get-DcoirFunctionDefinitions {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Paths
  )

  $rows = New-Object System.Collections.ArrayList
  foreach ($path in $Paths) {
    $text = Read-DcoirText -Path $path
    $lineNumber = 0
    foreach ($line in ($text -split "`r?`n")) {
      $lineNumber += 1
      $match = [regex]::Match($line, '^\s*function\s+(?<name>[-A-Za-z0-9_]+)\b')
      if ($match.Success) {
        [void]$rows.Add([pscustomobject]@{
          Name = [string]$match.Groups['name'].Value
          NormalizedName = ([string]$match.Groups['name'].Value).ToLowerInvariant()
          Path = $path
          Line = $lineNumber
        })
      }
    }
  }
  return @($rows)
}

function Get-DcoirCommandAsts {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Paths
  )

  $rows = New-Object System.Collections.ArrayList
  foreach ($path in $Paths) {
    $parsed = Get-DcoirParsedFile -Path $path
    if (@($parsed.Errors).Count -gt 0) {
      continue
    }
    $commands = $parsed.Ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true)
    foreach ($command in @($commands)) {
      [void]$rows.Add($command)
    }
  }
  return @($rows)
}

function Get-DcoirCommandParameterNames {
  param(
    [Parameter(Mandatory = $true)]
    [System.Management.Automation.Language.CommandAst]$CommandAst
  )

  $names = New-Object System.Collections.ArrayList
  foreach ($element in @($CommandAst.CommandElements)) {
    if ($element -is [System.Management.Automation.Language.CommandParameterAst]) {
      [void]$names.Add([string]$element.ParameterName)
    }
  }
  return @($names)
}

function ConvertTo-DcoirKeyValueMap {
  param(
    [Parameter(Mandatory = $true)]
    [object[]]$Lines
  )

  $map = @{}
  foreach ($rawLine in @($Lines)) {
    foreach ($line in ([string]$rawLine -split "`r?`n")) {
      if ([string]::IsNullOrWhiteSpace($line)) { continue }
      $index = $line.IndexOf('=')
      if ($index -lt 1) { continue }
      $key = $line.Substring(0, $index)
      $value = $line.Substring($index + 1)
      $map[$key] = $value
    }
  }
  return $map
}

function Compare-DcoirStringArray {
  param(
    [Parameter(Mandatory = $true)]
    [AllowEmptyCollection()]
    [string[]]$Expected,

    [Parameter(Mandatory = $true)]
    [AllowEmptyCollection()]
    [string[]]$Actual
  )

  $differences = New-Object System.Collections.ArrayList
  if (@($Expected).Count -ne @($Actual).Count) {
    [void]$differences.Add([pscustomobject]@{
      Index = -1
      Expected = ('count={0}' -f @($Expected).Count)
      Actual = ('count={0}' -f @($Actual).Count)
    })
  }

  $max = [Math]::Max(@($Expected).Count, @($Actual).Count)
  for ($index = 0; $index -lt $max; $index += 1) {
    $expectedValue = if ($index -lt @($Expected).Count) { [string]$Expected[$index] } else { '<missing>' }
    $actualValue = if ($index -lt @($Actual).Count) { [string]$Actual[$index] } else { '<missing>' }
    if ($expectedValue -cne $actualValue) {
      [void]$differences.Add([pscustomobject]@{
        Index = $index
        Expected = $expectedValue
        Actual = $actualValue
      })
    }
  }

  return @($differences)
}

function Get-DcoirFunctionAstByName {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Paths,

    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $matches = New-Object System.Collections.ArrayList
  foreach ($path in $Paths) {
    $parsed = Get-DcoirParsedFile -Path $path
    if (@($parsed.Errors).Count -gt 0) { continue }
    $nodes = $parsed.Ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $Name }, $true)
    foreach ($node in @($nodes)) {
      [void]$matches.Add([pscustomobject]@{
        Path = $path
        Name = $node.Name
        Text = $node.Extent.Text
        Line = $node.Extent.StartLineNumber
      })
    }
  }

  if (@($matches).Count -ne 1) {
    throw "Expected exactly one function AST named $Name, found $(@($matches).Count)."
  }

  return $matches[0]
}

function Get-DcoirFunctionTextByName {
  param(
    [Parameter(Mandatory = $true)]
    [string[]]$Paths,

    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  return [string](Get-DcoirFunctionAstByName -Paths $Paths -Name $Name).Text
}

function Get-DcoirAssignedStringValues {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Text,

    [Parameter(Mandatory = $true)]
    [string]$VariableName
  )

  $escapedVariableName = [regex]::Escape($VariableName)
  $pattern = ('(?m)\${0}\s*=\s*"(?<value>[^"]+)"' -f $escapedVariableName)
  return @([regex]::Matches($Text, $pattern) | ForEach-Object { [string]$_.Groups['value'].Value } | Select-Object -Unique)
}

function Assert-DcoirTextContains {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Text,

    [Parameter(Mandatory = $true)]
    [string]$Needle,

    [Parameter(Mandatory = $true)]
    [string]$Because
  )

  $Text.Contains($Needle) | Should -BeTrue -Because $Because
}

function Assert-DcoirTextDoesNotMatch {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Text,

    [Parameter(Mandatory = $true)]
    [string]$Pattern,

    [Parameter(Mandatory = $true)]
    [string]$Because
  )

  ([regex]::IsMatch($Text, $Pattern)) | Should -BeFalse -Because $Because
}
