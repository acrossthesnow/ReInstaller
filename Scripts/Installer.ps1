param([switch]$Elevated)

function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

if ((Test-Admin) -eq $false)  {
    if ($elevated) {
        # tried to elevate, did not work, aborting
    } else {
        Start-Process powershell.exe -Verb RunAs -ArgumentList ('-noprofile -noexit -file "{0}" -elevated' -f ($myinvocation.MyCommand.Definition))
    }
    exit
}

#Start-Transcript -Path "logs.txt"
robocopy /E $PSScriptRoot\.. $env:TEMP\ReInstaller\
Set-Location -Path $env:TEMP\ReInstaller\Scripts
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
$env:ChocolateyInstall = Convert-Path "$((Get-Command choco).Path)\..\.."   
Import-Module "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
refreshenv
choco install python311 -y
refreshenv
choco install git -y
refreshenv
python -m pip install --upgrade pip
refreshenv
pip install git+https://github.com/rsalmei/alive-progress
refreshenv

##Remove remnant task
schtasks /delete /tn ReInstaller /f

## Create the action
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-noexit -executionPolicy bypass  -File Phase2Installer.ps1' -WorkingDirectory $env:TEMP\ReInstaller\Scripts\

## Set to run as local system, No need to store Credentials!!!
$principal = New-ScheduledTaskPrincipal -UserId "$env:ComputerName\\$env:UserName" -LogonType Interactive -RunLevel Highest

## set to run at startup could also do -AtLogOn for the trigger
$trigger = New-ScheduledTaskTrigger -AtLogon -User "$env:ComputerName\\$env:UserName"
$Settings = New-ScheduledTaskSettingsSet -Priority 4

## register it (save it) and it will show up in default folder of task scheduler.
$Task = New-ScheduledTask -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings
Register-ScheduledTask -TaskName 'ReInstaller' -InputObject $Task

#Set current path for next stage
$location = "$PSScriptRoot\"
$location|export-clixml -path "$env:TEMP\ReInstaller\Scripts\ORIGINALPATH.xml"


Read-Host -Prompt "Press to enter to restart computer and launch ReInstaller..."
#$RunOnceKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
#set-itemproperty $RunOnceKey "ReInstaller" ('C:\Windows\System32\WindowsPowerShell\v1.0\Powershell.exe -noexit -executionPolicy bypass -File $env:TEMP\ReInstaller\Scripts\Phase2Installer.ps1')
# Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
# Install-Module PSWindowsUpdate -Force
# Import-Module PSWindowsUpdate
# Get-WUInstall -AcceptAll -AutoReboot
#Stop-Transcript
Restart-Computer