# ReInstaller

Have you ever needed something to reinstall application after a fresh install of Windows???

"ReInstaller" is a Python script that automates the process of re-installing all previously installed applications on a Windows machine after a Windows reinstallation. The script creates a log of all currently installed applications, and after the reinstallation of Windows, it uses Chocolatey, a package manager for Windows, to download and install all the applications from the internet. This ensures that the reinstalled applications are fresh and not corrupted, which could be the case if they were restored from a backup. The program is easy to use and can save users significant time and effort in reinstalling applications manually after a Windows reinstallation.


# Execution
1. Copy the ReInstaller files onto a USB drive.
2. Right-click on the "install.bat" file and select "Run as Administrator".
3. ReInstaller will run and prompt you to reboot your computer if necessary.
4. After rebooting, ReInstaller will prompt you to confirm if the computer is the new or old one.
5. Follow the prompts in ReInstaller to exit the program and proceed with reinstalling Windows.
6. After Windows is reinstalled, run ReInstaller again and select "new computer" when prompted.
7. Review the list of programs to be installed and follow the prompts to begin the installation process.
