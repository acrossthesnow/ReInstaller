import os
import subprocess
import re
import csv

from alive_progress import alive_bar

#%SystemRoot%\system32\WindowsPowerShell\v1.0\
powershellPath = "powershell.exe"
cwd = os.getcwd()
programsFile = "programs.txt"
programsFilePath = cwd+"\\"+programsFile
programsScript = "InstalledPrograms.ps1"
notFound = []

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
        self.install = True
        self.equivalent = True
        self.review = False
        self.options = {}

def GatherPrograms(filepath):
    args = "powershell.exe -ExecutionPolicy Bypass -File .\InstalledPrograms.ps1"
    output = subprocess.run(args, stdout=subprocess.PIPE, universal_newlines=True).stdout.split('\n')

def ReadStoredPackages(programs):
    alreadyStored = []

    #Gather items already stored
    with open('PackageReference.csv') as file:
        reader = csv.DictReader(file)
        for row in reader:
            alreadyStored.append(row)

    return(alreadyStored)

def StorePackages(programs):
    fields = ['Name', 'Version', 'Package']
    toBeStored = []
    alreadyStored = []
    #Generate list of items to be stored
    for program in programs:
        if program.install and not program.review:
            toBeStored.append([program.name,program.version,program.package])
    
    alreadyStored = ReadStoredPackages(programs)




    with open('PackageReference.csv', 'w') as file:
        file.write("Name,Version,Package\n")
        for program in programs:
            if program.install and not program.review:
                file.write(program.name + ',' + program.version + ',' + program.package + '\n')



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

def GetPackageInfo(program):
    if program.package:
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
            program.install = False

def FindChocoPackage(programs, unattended=False):
    with alive_bar(len(programs)) as bar:
        for i, program in enumerate(programs):
            output = subprocess.run("choco search " + program.name, stdout=subprocess.PIPE, universal_newlines=True)
            parted = program.name.split()
            if len(parted) > 1:
                if output.stdout.__contains__('0 packages found'):
                    for i in range(0, len(parted)):
                        output = subprocess.run("choco search " + ' '.join(parted[0:(len(parted)-1-i)]), stdout=subprocess.PIPE, universal_newlines=True)
                        
                        if output.stdout.__contains__('0 packages found') and (len(parted)-1-i) != 1:
                            continue
                        
                        elif output.stdout.__contains__('0 packages found'):
                            program.equivalent = False
                            program.review = False
                            program.install = False
                            break
                                               
                        elif output.stdout.__contains__('1 packages found'):
                            program.package = output.stdout.split('\n')[1].split()[0]
                            GetPackageInfo(program)
                            break

                        elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and unattended == True:
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

                            program.review = True
                            program.equivalent = False
                            program.install = False
                            break

                        elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and unattended == False:
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
                                    for x, option in enumerate(options):
                                        print(str((x+1))+".  "+option)
                                        
                                        if x == 25:
                                            break
                                    
                                    print()
                                    print("Program Name: " + program.name + "    Version: " + program.version)
                                    selection = input("Which package would you like to install for this program?(0 - Don't Install, X - Exit Attended Mode):   ")
                                    if selection == '0':
                                        program.install = False
                                        program.equivalent = False
                                        program.review = False
                                        loop = False
                                        bar()

                                    elif selection.lower() == 'x':
                                        unattended = True
                                        program.package = options[0].split()[0]
                                        program.review = True
                                        program.install = False
                                        GetPackageInfo(program)
                                        loop = False
                                        bar()
                                        
                                    else:
                                        try:
                                            program.package = options[int(selection)-1].split()[0]
                                            GetPackageInfo(program)
                                            loop = False
                                            bar()
                                        except:
                                            systemClear()
                                            print("The number you have entered is not valid. Please try again.")
                                            systemPause()
                                            loop = True

                            break


            elif len(parted) == 1:
                if output.stdout.__contains__('0 packages found'):
                    program.equivalent = False
                    program.review = False
                    program.install = False
                    

            
                elif output.stdout.__contains__('1 packages found'):
                    program.package = output.stdout.split('\n')[1].split()[0]
                    GetPackageInfo(program)

                elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and unattended == True:
                    options = output.stdout.split('\n')
                    options.pop(0)

                    for x, option in enumerate(options):
                        if option.endswith('packages found.'):
                            d = len(options) - x
                        
                    for x in range(d):
                        options.pop(-1)
                    for option in options:
                        program.options[option] = option.split()[0]

                    program.review = True
                    program.equivalent = False


                elif not output.stdout.__contains__('1 packages found') and not output.stdout.__contains__('0 packages found') and unattended == False:
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
                            for x, option in enumerate(options):
                                print(str((x+1))+".  "+option)
                                
                                if x == 25:
                                    break
                            
                            print()
                            print("Program Name: " + program.name + "    Version: " + program.version)
                            selection = input("Which package would you like to install for this program?(0 - Don't Install, X - Exit Attended Mode):   ")
                            if selection == '0':
                                program.install = False
                                program.equivalent = False
                                program.review = False
                                loop = False
                                bar()
                                

                            elif selection.lower() == 'x':
                                unattended = True
                                program.package = options[0].split()[0]
                                program.review = True
                                GetPackageInfo(program)
                                loop = False
                                bar()
                                
                            else:
                                try:
                                    program.package = options[int(selection)-1].split()[0]
                                    GetPackageInfo(program)
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
        FindChocoPackage([program])

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
            selection = input("Which package would you like to install for this program?(0 - Don't Install):   ")
            try:
                selection = int(selection)
                loop = False
            except:
                if selection == '':
                    program.install = False
                    program.review = False
                    program.equivalent = False
                    break
                else:
                    systemClear()
                    print("The selection you have entered is not valid. Please try again.")
                    loop = True
                    continue
        
            if selection == '0':
                program.install = False
                program.review = False
                program.equivalent = False
            
            else:
                for i, package in enumerate(program.options):
                    if selection - 1 == i:
                        program.package = program.options[package]
                        GetPackageInfo(program)
                        program.review = False
                        program.install = True
                        program.equivalent = True

def PrintDetails(program):
    print("Program Name: " + program.name + "  -   Version: " + program.version)
    print("Package: " + program.package)
    print("Install: " + str(program.install))
    print("Equivalent Package: " + str(program.equivalent))
    print("Review: " + str(program.review))
    print("Packages Found: " + str(len(program.options)))

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
            program.install = False
            program.review = False
            loop = False

        elif selection == '1':
            PackageSelection(program)
            loop = False

        elif selection == '2':
            if program.package:
                program.install = True
                program.review = False
            
            else:
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
            if program.package:
                print(str(i+1) + ". " + program.name + "    -   " + program.package + " -   " + program.source)
            elif not program.package:
                print(str(i+1) + ". " + program.name + "    -   " + "(No package selected)")
                
        selection = input("Which program would you like to edit?(0 - Go back): ")
        try:
            selection = int(selection)
            if selection == 0:
                loop = False
            elif selection in range(1, len(programs)+1):
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
def ReviewPackages(programs):
    systemClear()

    install = False
    approve = False
    review = False
    ignore = False
    exitFlag = False

    print()
    print("==================================================")
    for i, program in enumerate(programs):
        if not program.review and program.install:
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
        if program.review and program.package:
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
        if program.review and not program.package:
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
        if not program.review and not program.install:
            print(str(i) + ".  " + program.name + " - " + program.version)
            ignore = True
    if not ignore:
        print("NONE")

    if approve:
        while loop2:
            selection = input("Approve packages individually? y/[n]: ")
            try:
                if selection.lower == 'n' or selection.lower == '':
                    for program in programs:
                        if program.package and program.review:
                            program.install = True
                            
                elif selection.lower == 'y':
                    for program in programs:
                        ModifyPackage(program)
                continue
                loop2 = False

            except:
                loop2 = True


    if review:
        systemClear()
        for program in programs:
            if program.review and program.package:
                loop = True
                while loop == True:
                    print(program.name + " (" + program.version + ")")
                    print("The above program will be installed with the following package: program.package" + " (" + program.source + ")")
                    print()
                    selection = input("Do you approve this?(y - Install, n - Don't Install, q - Modify Package)[n]")
                    try:
                        if selection == '' or selection.lower == 'n':
                            program.install = False
                            program.review = False
                            loop = False

                        elif selection.lower == 'y':
                            program.install = True
                            program.review = False
                            loop = False

                        elif selection.lower == 'q':
                            ModifyPackage(program)
                            loop = False
                    except:
                        systemClear()
                        print("The option you have entered is invalid, please try again.")
                        loop = True
                        systemPause()

            elif program.review and not program.package:
                ModifyPackage(program)

    return(approve, review)

#Read programs file generated by InstallPrograms.ps1
def ReadPrograms():
    programs = []   #Program objects
    lines = []

    file = ReadFile(programsFile)

    file.pop(0)
    file.pop(0)
    file.pop(0)

    for line in file:
        try:
            info = line.rstrip(' \n')
            name = re.split(" {3}", info)[0]
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
    with alive_bar(len(programs)) as bar:
        for program in programs:
            if program.install and not program.review:                
                if program.package != '':
                    args = "choco install " + program.package + " -y"
                    subprocess.run(args)
                    program.installed = True
            bar()

def main():
    # print(os.getcwd())

    if os.path.exists(programsFilePath):
        response = input("Would you like to start over?")
        if response.lower()=='y':
            GatherPrograms()
    else:
        GatherPrograms()
    
    programs = ReadPrograms()

    FindChocoPackage(programs, True)

    mainLoop = True
    while mainLoop:
        result = ReviewPackages(programs)
        print()

        if not result[0] and not result[1]:
            print()
            print("Main Menu:")
            print("0. Exit")
            print("1. Install all programs")
            print("2. Edit a program")

            selection = input("What would you like to do?: ")

        else:
            systemPause()

        try:
            selection = int(selection)
            if selection == 0:
                mainLoop = False

            elif selection == 1:
                InstallPackages(programs)
                mainLoop = True

            elif selection == 2:
                ProgramSelection(programs)
                mainLoop = True

        except:
            systemClear()
            print("The response you have given is invalid, please try again.")

        InstallPackages(programs)
        
        os.system("PAUSE")

if __name__ == "__main__":
    main()

    #Review all installed programs and remove the ones already installed
    #Check where chocolatey is getting it's files.
    #Figure out how to update chocolatey package checksum
    #Export application name with package name for easy lookup
    #Add history folder for previous applications
