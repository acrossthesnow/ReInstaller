@echo off
xcopy "%~dp0" %TEMP%\ReInstaller\ /v /q /s /z /i /y
cls
echo Installing Chocolatey...
start "Chocolatey Install" /wait cmd /c "powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))""
echo Chocolatey installed.
echo .
echo =================================
echo Installing python...
start "Python Install" /wait cmd /c "choco install python311 -y"
echo Python installed.
echo .
echo =================================
echo Installing git...
start "Python Install" /wait cmd /c "choco install git -y"
echo Python installed.
echo .
echo =================================
echo Installing python depenencies...
start "Dependency Install" /wait cmd /c "python -m pip install --upgrade pip & pip install git+https://github.com/rsalmei/alive-progress"
echo Python dependencies installed.
echo .
echo =================================
echo About to begin the Reinstaller.
pause
cls
pushd
cd %TEMP%\ReInstaller\
start "ReInstaller" /wait cmd /k "python %TEMP%\ReInstaller\ReInstaller.py"
start "Clean-up" cmd /c "rmdir %TEMP%\ReInstaller\ /s /q"