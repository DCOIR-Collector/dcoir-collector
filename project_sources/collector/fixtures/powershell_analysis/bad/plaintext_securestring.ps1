$PlainText = "not-a-real-secret"
$SecureValue = ConvertTo-SecureString $PlainText -AsPlainText -Force
Write-Output $SecureValue.Length
