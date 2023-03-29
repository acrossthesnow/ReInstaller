start cmd /k powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
choco install python
py -m ensurepip --upgrade
pip install git+https://github.com/rsalmei/alive-progress
python .\ReInstaller.py