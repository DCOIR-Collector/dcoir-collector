param(
    [string]$SecretText,
    [string]$ToolPath,
    [string[]]$Arguments,
    [string]$RunCommand
)

function Convert-TestSecret {
    ConvertTo-SecureString $SecretText -AsPlainText -Force
}

function Invoke-OperatorTool {
    Start-Process -FilePath $ToolPath -ArgumentList $Arguments -Wait
}

function Install-RunKeyProbe {
    Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'DcoirProbe' -Value $RunCommand
}

Convert-TestSecret
Invoke-OperatorTool
Install-RunKeyProbe
