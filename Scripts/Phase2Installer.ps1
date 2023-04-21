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


Read-Host -Prompt "Press to enter to start ReInstaller..."
$location = import-clixml -path "$env:TEMP\ReInstaller\Scripts\ORIGINALPATH.xml"
Set-Location -Path $env:TEMP\ReInstaller\Scripts\
python ReInstaller.py -e
robocopy /COPYALL /IM /IS /IT /E $env:TEMP\ReInstaller\ $location 
Set-Location -Path $location
#Remove-Item -Path $env:TEMP\ReInstaller -Recurse -Force
schtasks /delete /tn ReInstaller /f
