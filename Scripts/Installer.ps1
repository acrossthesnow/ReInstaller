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
cd $env:TEMP\ReInstaller\Scripts
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
Write-Host "Changing RunOnce script." -foregroundcolor "magenta"
$RunOnceKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce"
set-itemproperty $RunOnceKey "NextRun" ('C:\Windows\System32\WindowsPowerShell\v1.0\Powershell.exe -executionPolicy Unrestricted -File ' + '$env:TEMP\ReInstaller\Scripts\Phase2Installer.ps1')
#Stop-Transcript
Restart-Computer -Force -Confirm