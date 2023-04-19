Read-Host -Prompt "Press to start ReInstaller"
$location = import-clixml -path "$env:TEMP\ReInstaller\Scripts\ORIGINALPATH.xml"
cd $env:TEMP\ReInstaller\Scripts\
python ReInstaller.py -e
robocopy /COPYALL /IM /IS /IT /E $env:TEMP\ReInstaller\ $location 
del $env:TEMP\ReInstaller
schtasks /delete /tn ReInstaller /f