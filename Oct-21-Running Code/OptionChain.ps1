$fpath = 'C:\pyAutomation\'
$logfile = $fpath + 'Status.log'
$pslog = $fpath + 'ps.log'
$process = 'python.exe'
While ((Get-Date -Format 'HH:mm') -gt '09:15' -and (Get-Date -Format 'HH:mm') -lt '15:40')
 {
  $msg1 = (Get-Date -Format 'HH:mm') + " | executing loop"
  $msg1 | Out-File $logfile
  Write-Host $msg1
  $json = $fpath + '\Files\*.json'
  cd $fpath
  $py = 'C:\Users\Administrator\AppData\Local\Programs\Python\Python39\python.exe'
  $File = $fpath + 'NSEOptionChain_Updated.py'
  #$File = $fpath + 'test.py'
   $value = Get-CimInstance Win32_Process -Filter "name = '$process'" | where {$_.CommandLine -match 'NSEOptionChain_Updated.py'}
  #$value = Get-CimInstance Win32_Process -Filter "name = '$process'" | where {$_.CommandLine -match 'test.py'}
  if (!($value)) {Start-Process $py $File -WorkingDirectory $fpath }
  Start-Sleep -Seconds 60
}

$msg2 = (Get-Date -Format 'HH:mm') + " | Wait for Tomorrow" 
if (!((Get-Date -Format 'HH:mm') -gt '09:15' -and (Get-Date -Format 'HH:mm') -lt '15:46')) 
{ 
  $msg2 | Out-File $logfile; Write-Host $msg2
  # if((Get-Date -Format 'HH:mm') -eq '23:45') {Start-Sleep -Seconds 60; Get-Item $json | Remove-Item }
  Start-Sleep -Seconds 1500 
}