import os
import subprocess
import re
import csv
from datetime import datetime
import glob
import argparse
from alive_progress import alive_bar

#Global Variables
parser = argparse.ArgumentParser()
parser.add_argument('-e', '-ScriptExecuted', type=str, required=False)
args = parser.parse_args()
try:
    if args.e:
        cwd = os.getenv("TEMP")
    else:
        cwd = os.getcwd()

except:
    cwd = os.getcwd()

powershellPath = "powershell.exe"
programsFile = str(datetime.now().strftime("%Y%b%d_%H%M%S") + "-programs.txt")
historyFolder = cwd + "\\Data\\Program History\\"
programsPath = historyFolder + programsFile
scriptDirectory = '..\\Scripts\\'
programsScript = scriptDirectory + "InstalledPrograms.ps1"
dataDirectory = '\\Data\\'
packageReference = 'PackageReference.csv'
referencePath = cwd + dataDirectory + packageReference
notFound = []
storedPackages = []

print(os.listdir(referencePath))


def systemClear():
    import sys
    import os

    if sys.platform.startswith('darwin'):
        os.system('clear')
    elif sys.platform.startswith('linux'):
        os.system('clear')
    elif sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
        os.system('cls')

def systemPause():
    import os
    os.system('pause')

class Program:
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.package = ''
        #self.install = False
        #self.equivalent = False
        #self.review = True
        self.options = {}
        self.source = ''
        #self.approved = False
        self.status = 0
    
    #5 - Install
    #4 - Waiting Approval
    #3 - Waiting Package Selection
    #2 - Reserved
    #1 - Intentionally Revoked
    #0 - Not seen

    def Install(self):
        if self.package != '':
            self.status = 5
        else:
            self.status = 3
    
    def Approval(self):
        if self.package != '':
            self.status = 4
        
        else:
            self.status = 3
    
    def Selection(self):
        self.status = 3

    def Revoke(self):
        self.status = 1

    def IsInstall(self):
        if self.status == 5:
            return True
        
        else:
            return False
    
    def IsApproval(self):
        if self.status == 4:
            return True
        else:
            return False
    
    def IsSelection(self):
        if self.status == 3:
            return True
        else:
            return False
    
    def IsRevoked(self):
        if self.status == 1:
            return True
        else:
            return False
    
    def IsUntouched(self):
        if self.status == 0:
            return True
        else:
            return False

def NewestFile(path):
    files = os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    return max(paths, key=os.path.getctime)

def GatherPrograms(mostRecent = False):
    args = "powershell.exe -ExecutionPolicy Bypass -File Scripts\InstalledPrograms.ps1"
    output = subprocess.run(args, stdout=subprocess.PIPE, universal_newlines=True).stdout
    if not os.path.exists(programsFolder):
        os.makedirs(programsFolder)

    with open(programsPath, 'w') as file:
        file.write(output)

#Read all packages and their information from PackageReference.csv
def ReadPackageReference():
    with open(referencePath) as file:
        reader = csv.DictReader(file)
        for row in reader:
            storedPackages.append(row)

#Store all packages and their information in PackageReference.csv
def StorePackageReference(programs):
    fields = ['Name', 'Version', 'Package','Status']
    toBeStored = []
    #Generate list of items to be stored
    for program in programs:
        if not program.IsUntouched():
            toBeStored.append([program.name,program.version,program.package,program.status])

    for package in toBeStored:
        for i, item in enumerate(storedPackages):
            if package[0] == item['Name'] and package[1] == item['Version']:
                del storedPackages[i]
    
    for package in storedPackages:
        if package['Status'] != '0':
            toBeStored.append(package)

    with open(referencePath, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(fields)
        for program in toBeStored:
            writer.writerow(program)

#Get information about a specific package that had been stored in PackageReference.csv
def GetStoredPackage(program):
    for package in storedPackages:
        if package['Name'] == program.name and package['Version'] == program.version:
            program.name = package['Name']
            program.version = package['Version']
            program.package = package['Package']
            program.status = int(package['Status'])
            return(True)

    return(False)

#Determine how the file being read is formatted
def DetermineType(file):
    with open(file, "rb") as file:
        beginning = file.read(4)
        # The order of these if-statements is important
        # otherwise UTF32 LE may be detected as UTF16 LE as well
        if beginning == b'\x00\x00\xfe\xff':
            return(5)
            #print("UTF-32 BE")
        elif beginning == b'\xff\xfe\x00\x00':
            return(4)
            #print("UTF-32 LE")
        elif beginning[0:3] == b'\xef\xbb\xbf':
            return(3)
            #print("UTF-8")
        elif beginning[0:2] == b'\xff\xfe':
            return(2)
            #print("UTF-16 LE")
        elif beginning[0:2] == b'\xfe\xff':
            return(1)
            #print("UTF-16 BE")
        else:
            return(0)
            #print("Unknown or no BOM")

#Read any file in - utilizes DetermineType so there are no errors
def ReadFile(file):
    type = DetermineType(file)

    if type == 0:
        f = open(file, 'r')

    elif type == 1:
        f = open(file, 'r', encoding='UTF-16 BE')

    elif type == 2:
        f = open(file, 'r', encoding='UTF-16 LE')

    elif type == 3:
        f = open(file, 'r', encoding='UTF-8')

    elif type == 4:
        f = open(file, 'r', encoding='UTF-32 LE')

    elif type == 5:
        f = open(file, 'r', encoding='UTF-32 BE')

    return(f.readlines())

#Given a package name, get the info from choco including source.
def GetPackageInfo(program):
    source = ''
    if program.package != '':
        try:
            output = subprocess.run("choco info " + program.package, stdout=subprocess.PIPE, universal_newlines=True)
            tmp = output.stdout.split('\n')
            for item in tmp:
                if "Software Source" in item or "Package Source" in item and "http" in item:
                    try:
                        source = item.split(":", 1)[1].lstrip()
                    except:
                        continue
                if "Package approved as a trusted package" in item:
                    program.trusted = True

            program.source = source

        except:
            program.Approval()
            
def FindChocoPackage(programs, attended=True, freshScan=False):
    systemClear()
    with alive_bar(title='Searching for packages', total=len(programs)) as bar:
        for i, program in enumerate(programs):
            if GetStoredPackage(program) and not freshScan:
                GetPackageInfo(program)
                bar()
                continue


            else:    
                output = subprocess.run("choco search " + program.name, stdout=subprocess.PIPE, universal_newlines=True)
                parted = program.name.split()
                if len(parted) > 1:
                    if output.stdout.__contains__('0 packages found'):
                        for i in range(0, len(parted)):
                            output = subprocess.run("choco search " + ' '.join(parted[0:(len(parted)-1-i)]), stdout=subprocess.PIPE, universal_newlines=True)
                            
                            if output.stdout.__contains__('0 packages found') and (len(parted)-1-i) != 1:
                                continue
                            
                            elif output.stdout.__contains__('0 packages found'):
                                program.Revoke()
                                break
                                                
                            elif output.stdout.__contains__('1 packages found'):
                                program.package = output.stdout.split('\n')[1].split()[0]
                                program.Approval()
                                GetPackageInfo(program)
                                break

                            elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and attended == False:
                                options = output.stdout.split('\n')
                                options.pop(0)

                                for x, option in enumerate(options):
                                    if option.endswith('packages found.'):
                                        d = len(options) - x
                                    
                                for x in range(d):
                                    options.pop(-1)
                                for i, option in enumerate(options):
                                    if i == 25:
                                        break
                                    program.options[option] = option.split()[0]

                                program.Selection()
                                break

                            elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and attended == True:
                                with bar.pause():
                                    options = output.stdout.split('\n')
                                    options.pop(0)

                                    for x, option in enumerate(options):
                                        if option.endswith('packages found.'):
                                            d = len(options) - x
                                        
                                    for x in range(d):
                                        options.pop(-1)

                                    loop = True
                                    while loop == True:    
                                        print("\n===================================================================")
                                        length = len(options)
                                        for i, package in enumerate(reversed(options), start=1):
                                            n = length - i
                                            print(str(n+1) + ". " + package)
                                        
                                        print()
                                        print("Program Name: " + program.name + "    Version: " + program.version)
                                        print()
                                        print("0. Don't Install")
                                        print("-1. Exit Attended Mode")
                                        selection = input("Which package would you like to install for this program?: ")
                                        if selection == '0':
                                            program.Revoke()
                                            loop = False
                                            bar()

                                        elif selection == '-1':
                                            attended = False
                                            program.package = options[0].split()[0]
                                            program.Selection()
                                            
                                            GetPackageInfo(program)
                                            loop = False
                                            bar()
                                            
                                        else:
                                            try:
                                                program.package = options[int(selection)-1].split()[0]
                                                GetPackageInfo(program)
                                                program.Install()
                                                loop = False
                                                bar()
                                            except:
                                                systemClear()
                                                print("The number you have entered is not valid. Please try again.")
                                                systemPause()
                                                loop = True

                                break
                    
                    elif output.stdout.__contains__('1 packages found'):
                        program.package = output.stdout.split('\n')[1].split()[0]
                        program.Approval()
                        GetPackageInfo(program)
                        

                    elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and attended == False:
                        
                        options = output.stdout.split('\n')
                        options.pop(0)

                        for x, option in enumerate(options):
                            if option.endswith('packages found.'):
                                d = len(options) - x
                            
                        for x in range(d):
                            options.pop(-1)
                        for i, option in enumerate(options):
                            if i == 25:
                                break
                            program.options[option] = option.split()[0]

                        program.Selection()
                        

                    elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and attended == True:
                        with bar.pause():
                            options = output.stdout.split('\n')
                            options.pop(0)

                            for x, option in enumerate(options):
                                if option.endswith('packages found.'):
                                    d = len(options) - x
                                
                            for x in range(d):
                                options.pop(-1)

                            loop = True
                            while loop == True:    
                                print("\n===================================================================")
                                length = len(options)
                                for i, package in enumerate(reversed(options), start=1):
                                    n = length - i
                                    print(str(n+1) + ". " + package)
                                
                                print()
                                print("Program Name: " + program.name + "    Version: " + program.version)
                                print()
                                print("0. Don't Install")
                                print("-1. Exit Attended Mode")
                                selection = input("Which package would you like to install for this program?: ")
                                if selection == '0':
                                    program.Revoke()
                                    loop = False
                                    bar()

                                elif selection == '-1':
                                    attended = False
                                    program.package = options[0].split()[0]
                                    program.Selection()
                                    GetPackageInfo(program)
                                    loop = False
                                    bar()
                                    
                                else:
                                    try:
                                        program.package = options[int(selection)-1].split()[0]
                                        GetPackageInfo(program)
                                        program.Install()
                                        loop = False
                                        bar()
                                    except:
                                        systemClear()
                                        print("The number you have entered is not valid. Please try again.")
                                        systemPause()
                                        loop = True

                elif len(parted) == 1:
                    if output.stdout.__contains__('0 packages found'):
                        program.Revoke()
                        
                
                    elif output.stdout.__contains__('1 packages found'):
                        program.package = output.stdout.split('\n')[1].split()[0]
                        program.Approval()
                        GetPackageInfo(program)

                    elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and attended == False:
                        options = output.stdout.split('\n')
                        options.pop(0)

                        for x, option in enumerate(options):
                            if option.endswith('packages found.'):
                                d = len(options) - x
                            
                        for x in range(d):
                            options.pop(-1)
                        for option in options:
                            program.options[option] = option.split()[0]

                        program.Selection()


                    elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and attended == True:
                        with bar.pause():
                            options = output.stdout.split('\n')
                            options.pop(0)

                            for x, option in enumerate(options):
                                if option.endswith('packages found.'):
                                    d = len(options) - x
                                
                            for x in range(d):
                                options.pop(-1)

                            loop = True
                            while loop == True:    
                                print("\n===================================================================")
                                length = len(options)
                                for i, package in enumerate(reversed(options), start=1):
                                    n = length - i
                                    print(str(n+1) + ". " + package)

                                
                                print()
                                print("Program Name: " + program.name + "    Version: " + program.version)
                                print()
                                print("0. Don't Install")
                                print("-1. Exit Attended Mode")
                                selection = input("Which package would you like to install for this program?: ")
                                
                                if selection == '0':
                                    program.Revoke()
                                    loop = False
                                    bar()
                                    

                                elif selection == '-1':
                                    attended = False
                                    program.package = options[0].split()[0]
                                    program.Selection()
                                    GetPackageInfo(program)
                                    loop = False
                                    bar()
                                    
                                else:
                                    try:
                                        program.package = options[int(selection)-1].split()[0]
                                        GetPackageInfo(program)
                                        program.Install()
                                        loop = False
                                        bar()
                                        break
                                    except:
                                        systemClear()
                                        print("The number you have entered is not valid. Please try again.")
                                        systemPause()
                                        loop = True


            bar()

def PackageSelection(program):
    loop = True
    if not program.options:
        FindChocoPackage([program], freshScan = True)

    else:
        while loop == True:
            systemClear()
            print("\n===================================================================")
            length = len(program.options)
            for i, package in enumerate(reversed(program.options), start=1):
                n = length - i
                print(str(n+1) + ". " + package)

            print()
            print("Program Name: " + program.name + "    Version: " + program.version)
            selection = input("Which package would you like to install for this program?(0 - No package) [0]:   ")
            try:
                if selection == '' or selection == '0' or selection.isspace():
                    program.Revoke()
                    program.package = ''

                else:
                    selection = int(selection)
                    for i, package in enumerate(program.options):
                        if selection - 1 == i:
                            program.package = program.options[package]
                            GetPackageInfo(program)
                            program.Install()

                loop = False
            except:
                systemClear()
                print("The selection you have entered is not valid. Please try again.")
                loop = True
                continue
                      
def PrintDetails(program):
    print("Program Name: " + program.name + "  -   Version: " + program.version)
    print("Package: " + program.package)
    print("Install: " + str(program.IsInstall()))
    print("Review: " + str(program.IsApproval()))
    #print("Equivalent Package: " + str(program.equivalent))
    #print("Review: " + str(program.review))
    print("Packages Found: " + str(len(program.options)))
    print("Package Source: " + program.package)

#Menu for modifying a program
def ModifyPackage(program):
    loop = True
    while loop == True:
        systemClear()
        PrintDetails(program)
        print()
        
        print("0. Don't Install/Exit")
        print("1. Select/Edit Package")
        print("2. Approve for install")
        selection = input("What would you like to do?: ")
        if selection == '0':
            program.Revoke()
            if program.source == '' or program.source.isspace():
                program.package = ''
            
            loop = False

        elif selection == '1':
            PackageSelection(program)
            loop = False

        elif selection == '2':
            if program.package != '':
                program.Install()
            
            else:
                systemClear()
                print("There is no package selected. Please select one.")
                systemPause()
                PackageSelection(program)

            loop = False

        else:
            systemClear()
            print("The number you have entered is invalid. Please try again.")
            loop = True
            systemPause()

#Print all programs and gives user the option to select a program to modify
def ProgramSelection(programs):
    
    loop = True
    while loop == True:
        systemClear()
        print()
        print("==================================================")
        for i, program in enumerate(programs):
            if program.package != '':
                print(str(i+1) + ". " + program.name + "    -   " + program.package + " -   " + program.source)
            elif program.package == '' or program.package.isspace():
                print(str(i+1) + ". " + program.name + "    -   " + "(No package selected)")
                
        selection = input("Which program would you like to edit?(0 - Go back): ")
        try:
            selection = int(selection)
            if selection == '0' or selection.isspace():
                loop = False
            elif int(selection) in range(1, len(programs)+1):
                ModifyPackage(programs[selection-1])
                loop = True
            else:
                print("The response you've given is invalid, please try again.")
                systemPause()
                loop = True

        except:
            print("The response you've given is invalid, please try again.")
            systemPause()
            loop = True

#Review all packages once all information has automatically been gathered.
def PrintPackages(programs):
    systemClear()

    install = False
    approve = False
    review = False
    ignore = False

    print("\n\n\n\n\n")
    print(datetime.now().strftime("%Y/%b/%d %H:%M:%S"))
    print("==================================================")
    for i, program in enumerate(programs):
        if program.IsInstall():
            print(str(i) + ".  " + program.name + "    -   " + program.package + "  -   " + program.source)
            install = True
    if not install:
        print("NONE")

    print()
    print("Packages listed above WILL be installed.")

    #Only approval needed
    print()
    print("==================================================")
    print("Package below need to be approved before install:")
    print()
    for i, program in enumerate(programs):
        if program.IsApproval():
            print(str(i) + ".  " + program.name + "    -   " + program.package + "  -   " + program.source)
            approve = True
    if not approve:
        print("NONE")
    
    #Package Selection Needed
    print()
    print("==================================================")
    print("Packages below must have a suitable package selected:")
    print()
    for i, program in enumerate(programs):
        if program.IsSelection():
            print(str(i) + ".  " + program.name + " - " + program.version)
            review = True
    if not review:
        print("NONE")

    #Will not be installed for various reasons
    print()
    print("==================================================")
    print("Packages below will not be installed: ")
    print()
    for i, program in enumerate(programs):
        if program.IsRevoked():
            print(str(i) + ".  " + program.name + " - " + program.version)
            ignore = True
    if not ignore:
        print("NONE")

    if approve or review:
        systemPause()

    return(approve, review)

def ApprovePackages(programs):
    #Has a package, just needs to be reviewed
    
    length = 0
    for program in programs:
        if program.IsApproval():
            length = length + 1
    if length > 0:
        systemClear()
        print("The following programs need to be approved.")
        systemPause()
        with alive_bar(title='Approving Packages', total=length) as bar:
            for program in programs:
                systemClear()
                if program.IsApproval():
                    with bar.pause():
                        PrintDetails(program)
                        print()
                        print("0. Package incorrect - Disapprove")
                        print("1. Package is correct - Approve")
                        print("2. Select a different one.")
                        selection = input("Please select one [0]: ")
                        if selection == '' or selection == '0' or selection.isspace():
                            program.Revoke()
                            

                        elif selection == '2':
                            PackageSelection(program)

                        else:
                            program.Install()

                        bar()
                             
def ReviewPackages(programs):
    #Doesn't have a package, but has options
    length = 0
    for program in programs:
        if program.IsSelection():
            length = length + 1
    if length > 1:
        systemClear()
        print("The following programs need a package to be selected.")
        systemPause()
        with alive_bar(title='Reviewing Packages', total=length) as bar:
            for program in programs:
                with bar.pause():
                    # if program.IsSelection():
                    #     loop = True
                    #     while loop == True:
                    #         systemClear()
                    #         print(program.name + " (" + program.version + ")")
                    #         print()
                    #         print("The above program will be installed with the following package: " + program.package + " (" + program.source + ")")
                    #         print()
                    #         print("0. Don't Install")
                    #         print("1. Install")
                    #         print("2. Modify Package")
                    #         selection = input("Do you approve this?[0]")
                    #         try:
                    #             if selection == '' or selection == '0':
                    #                 program.Revoke()
                    #                 loop = False

                    #             elif selection == '1':
                    #                 if program.Is
                    #                 program.ApproveForInstall()
                    #                 loop = False

                    #             elif selection == '2':
                    #                 ModifyPackage(program)
                    #                 loop = False
                    #         except:
                    #             systemClear()
                    #             print("The option you have entered is invalid, please try again.")
                    #             loop = True
                    #             systemPause()

                    # elif program.IsSelection():
                    #     PackageSelection(program)
                    if program.IsSelection():
                        PackageSelection(program)

                bar()

#Read programs file generated by InstallPrograms.ps1
def ReadPrograms(mostRecent = True):
    programs = []   #Program objects
    lines = []
    
    if mostRecent == True:
        folderPath = programsFolder
        fileType = r'\*.txt'
        files = glob.glob(folderPath + fileType)
        maxFile = max(files, key=os.path.getctime)

        file = ReadFile(maxFile)

    else:    
        loop = True
        while loop == True:
            systemClear()
            files = os.listdir(programsFolder)
            for i, file in enumerate(files):
                print(str(i+1) + ". " + file)

            try:
                selection = int(input("Please selection a file to read from: "))-1
                file = ReadFile(programsFolder + files[selection])
                loop = False
            except:
                systemClear()
                print("You have entered an invalid option. Please try again.")
                systemPause()
                loop = True

    file.pop(0)
    file.pop(0)
    file.pop(0)

    for line in file:
        try:
            info = line.rstrip(' \n')
            name = re.split(" {3}", info)[0]
            name = name.strip(',')
            version = re.split(" {3}", info)[-1]
            version = version.lstrip(' ')
            if name.isspace() or version.isspace():
                continue
            elif name =='' or version == '':
                continue
            elif name == version:
                continue
            else:
                program = Program(name, version)
                programs.append(program)
        except:
            continue

    return(programs)

def InstallPackages(programs):
    packages = []
    length = 0
    for program in programs:
        if program.IsInstall():
            if not packages.__contains__(program.package):
                packages.append(program.package)
                
            length = length + 1
    with alive_bar(title='Installing Packages', total=length) as bar:
        for package in packages:               
            args = "choco install " + package + " -y"
            output = subprocess.run(args, stdout=subprocess.PIPE, universal_newlines=True)
            bar()

def main():
    ReadPackageReference()
    attended = False
    mainLoop = True
    reviewNow = False
    # print(os.getcwd())
    while mainLoop == True:
        try:
            systemClear()
            print("===========Main Menu===========")
            print("Attended Mode: " + str(attended))
            print("0. Exit")
            print("1. Old Computer")
            print("2. New Computer")
            print("3. Change Attended Mode")
            selection = input("What would you like to do? [0]: ")

            if selection == '1':
                files = os.listdir(programsFolder)
                if files:
                    systemClear()
                    print("\n===================================================================")
                    for file in files:
                        
                        print(file)
                    print("\nAbove are the times you've already gathered applications.")
                    response = input("Would you like to re-gather all applications? y/[n]: ")
                    if response.lower()=='y':
                        GatherPrograms()
                        programs = ReadPrograms(mostRecent=True)

                    else:
                        systemClear()
                        print("0. Use most recent list of programs generated.")
                        print("1. Select a list of programs.")
                        response = input("What would you like to do? [0]: ")
                        if response == '1':
                            programs = ReadPrograms(mostRecent=False)
                        
                        else:
                            programs = ReadPrograms(mostRecent=True)


                else:
                    GatherPrograms()
                    programs = ReadPrograms(mostRecent=True)
                
                reviewLoop = True
                while reviewLoop == True:
                    try:
                        systemClear()
                        selection = input("Programs were successfully gathered. Would you like to review them now? (y/[n]): ")
                        if selection.lower() == 'y':
                            reviewNow = True
                        else:
                            reviewNow = False
                            
                        reviewLoop = False
                    except:
                        systemClear()
                        print("The selection you have entered is invalid, please try again.")
                        reviewLoop = True

            elif selection == '2':

                #GatherPrograms()
                files = os.listdir(programsFolder)

                systemClear()
                print("\n===================================================================")
                for file in files:
                    
                    print(file)
                print("\nAbove are the times you've already gathered applications.")
                print("0. Use most recent list of programs generated.")
                print("1. Select a list of programs.")
                response = input("What would you like to do? [0]: ")
                if response == '1':
                    programs = ReadPrograms(mostRecent=False)
                
                else:
                    programs = ReadPrograms(mostRecent=True)

                FindChocoPackage(programs, attended = attended)

                installLoop = True
                while installLoop:
                    result = PrintPackages(programs)
                    print()

                    if not result[0] and not result[1]:
                        StorePackageReference(programs)
                        print()
                        print("Install Menu:")
                        print("0. Back to Main Menu")
                        print("1. Install all programs")
                        print("2. Edit a program")

                        selection = input("What would you like to do?: ")

                        try:
                            selection = int(selection)
                            if selection == 0:
                                installLoop = False

                            elif selection == 1:
                                InstallPackages(programs)
                                installLoop = True

                            elif selection == 2:
                                ProgramSelection(programs)
                                installLoop = True

                        except:
                            systemClear()
                            print("The response you have given is invalid, please try again.")
                            installLoop = True
                    
                    if result[0]:
                        ApprovePackages(programs)

                    if result[1]:
                        ReviewPackages(programs)

            elif selection == '3':
                if attended == True:
                    attended = False
                elif attended == False:
                    attended = True

            else:
                mainLoop = False

            
            if reviewNow == True:

                FindChocoPackage(programs, attended = attended)

                installLoop = True
                while installLoop:
                    result = PrintPackages(programs)
                    print()

                    if not result[0] and not result[1]:
                        StorePackageReference(programs)
                        print()
                        print("Review Menu:")
                        print("0. Back to Main Menu")
                        print("2. Edit a program")

                        selection = input("What would you like to do?: ")

                        try:
                            selection = int(selection)
                            if selection == 0:
                                installLoop = False

                            elif selection == 2:
                                ProgramSelection(programs)
                                installLoop = True

                        except:
                            systemClear()
                            print("The response you have given is invalid, please try again.")
                            installLoop = True
                    
                    if result[0]:
                        ApprovePackages(programs)

                    if result[1]:
                        ReviewPackages(programs)

        except:
            systemClear()
            print("The input you provided was invalid, please try again.")
            systemPause()
            mainLoop = True
    
if __name__ == "__main__":
    main()

    #Figure out how to update chocolatey package checksum
