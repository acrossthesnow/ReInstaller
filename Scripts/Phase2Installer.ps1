#Start-Transcript -Path "logs.txt"
cd $env:TEMP\ReInstaller\Scripts\
Start-Transcript -Path "logs.txt"
python ReInstaller.py -e
robocopy /E $env:TEMP\ReInstaller\ $PSScriptRoot\.. 
del $env:TEMP\ReInstaller
Stop-Transcript