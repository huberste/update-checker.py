#!/usr/bin/python

from __future__ import print_function # new fancy print function
from urlparse import urlparse # web traffic stuff
from ftplib import FTP # for ftp client support

import sys # system stuff
import urllib2 # http stuff
import re # regular expressions
import csv # csv files
import os # for folder generation, ...
import getopt # for command line options
import msilib # for msi stuff
import datetime # for date and time stuff

SOFTWARE_FILE = "software.csv"
USERPROFILE = os.environ["USERPROFILE"]
DOWNLOAD_DIR = USERPROFILE + "\\Downloads"

INSTALL_FILE_HEADER_1 = "@echo off\n\nREM This cmd file installs "
INSTALL_FILE_HEADER_2 = "\nREM Automatically created on "
INSTALL_FILE_HEADER_3 = " by update-checker\n\nREM Variable vom Verzeichnis des Mandanten setzen\nset manpath=%~dp0\n\nREM wechsel ins Files-Verzeichnis\ncd ..\\..\\\n\nREM Variable vom File-Verzeichnis\nset a=%cd%\n\necho Installing "
MSI_INSTALL_LINE_1 = "msiexec /i "
MSI_INSTALL_LINE_2 = " /qn /norestart /l*v \"C:\\temp\\"
MSI_INSTALL_LINE_3 = "_install.log\""
INSTALL_FILE_FOOTER = "\necho re-organizing shortcuts...\nREM TODO\n\necho Done"

UNINSTALL_FILE_HEADER_1 = "@echo off\n\nREM This cmd file uninstalls "
UNINSTALL_FILE_HEADER_2 = "\nREM Automatically created on "
UNINSTALL_FILE_HEADER_3 = " by update-checker\n\necho Uninstalling "
MSI_UNINSTALL_LINE_1 = "msiexec /x "
MSI_UNINSTALL_LINE_2 = " /qn /norestart /l*v \"C:\\temp\\"
MSI_UNINSTALL_LINE_3 = "_uninstall.log\""
UNINSTALL_FILE_FOOTER = "\necho re-organizing shortcuts...\nREM TODO\necho Done"


VERSION = "0.3"
USAGE = "USAGE: \npython update-checker.py -i|--input-file <inputfile> [--(deep-)debug] [-d|--download-anyway | --no-download] [-h|--human-readable] [-n|--name <name>] [-v|--verbose] [--version]"

is_later_args = []
is_later_answers = []


def warning(*objs):
    """prints a warning message to standard out
    Args:
        *objs: the same objects that the print function takes
    """
    print("WARNING: ", *objs, file=sys.stderr)


def error(*objs):
    """prints an error message to standard out
    Args:
        *objs: the same objects that the print function takes
    """
    print("ERROR: ", *objs, file=sys.stderr)


def sizeof_fmt(num, suffix="B"):
    """formats the given number in human readable format
    Args:
        num: The number to be formatted
        suffix: the suffix that shall be put behind the formatted number
    Returns:
        The given num neatly formatted
    """
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def downloadfile(software, ver, lang, arch, dllink):
    """Downloads a File
    
    Downloads a file in the DOWNLOAD_DIR\software\ver\lang\arch\files folder
    
    Args:
        software: Name of the software to download
        ver: Version String of the software to download
        lang: Language of the software to download (e.g. "de" or "en"
        arch: Architecture of the software to download (e.g. "x86" or "x64"
        dllink: URL to the file to be downloaded
    """
    
    try:
        # append cookie for oracle java
        opener = urllib2.build_opener()
        opener.addheaders.append(("Cookie", "oraclelicense=accept-securebackup-cookie"))
        
        downloadurl = opener.open(dllink)
        meta = downloadurl.info()
        
        software_dir = "%s\\%s\\%s\\%s\\%s\\files\\" % (DOWNLOAD_DIR, software, ver, lang, arch)
        
        file_name = software_dir
        
        # set correct filename for download
        if "filename" in urllib2.unquote(downloadurl.geturl()):
            file_name = software_dir + re.compile("filename=([^&]*)").findall(urllib2.unquote(downloadurl.geturl()))[0]
        else: 
            file_name = software_dir + urllib2.unquote(downloadurl.geturl().split("/")[-1])
        
        # we don't need (or want) the stuff following the "?"
        file_name = file_name.split("?")[0]
        
        if file_name.endswith("\\"):
            file_name = file_name + "download"
        
        # make directory
        if not (os.path.isdir(software_dir)):
            os.makedirs(software_dir)
            
        f = open(file_name, 'wb')
        file_size = int(meta.getheaders("Content-Length")[0])
        print(" Downloading: %s Size: %s" % (file_name, sizeof_fmt(file_size)))

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = downloadurl.read(block_sz)
            if not buffer:
                    break

            file_size_dl += len(buffer)
            f.write(buffer)
            status = "\r%s    [%3.2f%%]     " % (sizeof_fmt(file_size_dl), file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print(status, end="")
            sys.stdout.flush()
        
        print()

        f.close()
        createCommandFiles(software, ver, lang, arch, file_name)
        print(" Finished download!")
    except urllib2.URLError as e:
        error("could not download %s: %s" % (dllink, e.strerror))
    except Error as e:
        error("could not download %s: %s" % (dllink, e.strerror))


def getFileEnding(file_name):
    fileName, fileExtension = os.path.splitext(file_name)
    return fileExtension;


def createCommandFiles(software, ver, lang, arch, file_name):
    # make directories
    software_dir = "%s\\%s\\%s\\%s\\%s" % (DOWNLOAD_DIR, software, ver, lang, arch)
    files_dir = "%s\\files" % (software_dir)
    mandanten_dir = "%s\\mandanten" % (software_dir)
    install_dir = "%s\\INSTALL" % (mandanten_dir)
    install_file = "%s\\install.cmd" % (install_dir)
    uninstall_file = "%s\\uninstall.cmd" % (install_dir)
    paket_dir = "%s\\paket" % (software_dir)
    if not (os.path.isdir(mandanten_dir)):
        os.makedirs(mandanten_dir)
    if not (os.path.isdir(install_dir)):
        os.makedirs(install_dir)
    if not (os.path.isdir(paket_dir)):
        os.makedirs(paket_dir)
    
    today = datetime.date.today()
    date = today.strftime("%Y-%m-%d")
    
    # install.cmd file
    finstall = open(install_file, 'w')
    
    # install.cmd file header
    print(INSTALL_FILE_HEADER_1, file=finstall, end="")
    print(software, ver, file=finstall, end="")
    print(INSTALL_FILE_HEADER_2, file=finstall, end="")
    print(date,file=finstall, end="")
    print(INSTALL_FILE_HEADER_3, file=finstall, end="")
    print(software, " ", ver, "...", file=finstall,  sep="")
    
    msi = (getFileEnding(file_name) == ".msi")
    
    # install.cmd install line
    if msi:
        print(MSI_INSTALL_LINE_1, file=finstall, end="")
        print("\"", os.path.basename(file_name), "\"", file=finstall, sep="", end="")
        print(MSI_INSTALL_LINE_2, file=finstall, end="")
        print(software, ver, file=finstall, sep="_", end="")
        print(MSI_INSTALL_LINE_3, file=finstall)
    else:
        print("%INSTALL_COMMANDS%", file=finstall)
    
    # install.cmd footer
    print(INSTALL_FILE_FOOTER, file=finstall, end="")
    
    finstall.close()
    
    # uninstall.cmd
    funinstall = open(uninstall_file, 'w')
    # uninstall.cmd file header
    print(UNINSTALL_FILE_HEADER_1, file=funinstall, end="")
    print(software, ver, file=funinstall, end="")
    print(UNINSTALL_FILE_HEADER_2, file=funinstall, end="")
    print(date,file=funinstall, end="")
    print(UNINSTALL_FILE_HEADER_3, file=funinstall, end="")
    print(software, " ", ver, "...", file=funinstall,  sep="")
    
    print(file_name)
    
    # uninstall.cmd uninstall line
    if msi:
        print(MSI_UNINSTALL_LINE_1, file=funinstall, end="")
        print(getMsiProperty(file_name, "ProductCode"), file=funinstall, sep="", end="")
        print(MSI_UNINSTALL_LINE_2, file=funinstall, end="")
        print(software, ver, file=funinstall, sep="_", end="")
        print(MSI_UNINSTALL_LINE_3, file=funinstall)
    else:
        print("%UNINSTALL_COMMANDS%", file=funinstall)
    
    # uninstall.cmd footer
    print(UNINSTALL_FILE_FOOTER, file=funinstall, end="")
    

def islater(versiona, versionb):
    """Compares two Strings representing a version.
    
    Args:
        versiona: Version String one
        versionb: Version String two
     
    Returns:
        True if versiona is later (newer) than versionb
        False otherwise
    """
    
    if (versiona == versionb):
        return False
    
    #save previous function calls to make stuff faster :-)
    i = 0
    for is_later_arg in is_later_args:
        i = i+1
        if (is_later_arg == "%s %s" % (versiona, versionb)):
            return is_later_answers[i-1]
    
    #The following block is only needed if version strings appear as 31/01/1999
    #date strings. This is impossible as we check in main method.
    #if (versiona.find("/") > -1):
    #    versiona =  ".".join(versiona.split("/")[::-1])
    #if (versionb.find("/") > -1):
    #    versionb =  ".".join(versionb.split("/")[::-1])
    
    # Java Version numbers (e.g. 8u31)
    versiona = versiona.replace('u','.')
    versionb = versionb.replace('u','.')
    
    versionasplit = versiona.split('.')
    versionbsplit = versionb.split('.')
    
    i = 0
    while ((i < len(versionasplit)) & (i < len(versionbsplit))):
        
        # if not digit: ask user
        if ( (not versionasplit[i].isdigit()) | (not versionbsplit[i].isdigit())):
            newer = raw_input(" USER INPUT NEEDED: is " + versiona + " newer than " + versionb + "? (Y/n) ")
            is_later_args.append("%s %s" % (versiona,  versionb))
            if ((newer == "Y") | (newer == "Yes") | (newer == "yes") | (newer == "") | (newer == "y")):
                is_later_answers.append("%s %s" % (versiona, versionb))
                return True
            else:
                is_later_answers.append("%s %s" % (versiona, versionb))
                return False
        
        # apparently new version
        if int(versionasplit[i]) > int(versionbsplit[i]):
            return True
        # apparently old download version (strange things happen all the time...)
        if int(versionasplit[i]) < int(versionbsplit[i]):
            return False
        i = i+1
        
    # apparently latest version is longer, e.g. "3.4" vs "3.4.2"
    if (len(versionasplit) > len(versionbsplit)):
        return True
        
    # should only end here if same version...
    return False

def getMsiProperty(path ,property):
    print(path)
    db = msilib.OpenDatabase(path, msilib.MSIDBOPEN_READONLY)
    view = db.OpenView ("SELECT Value FROM Property WHERE Property='" + property + "'")
    view.Execute(None)
    result = view.Fetch()
    return result.GetString(1)
    
def main(argv):
    debug = False
    deepdebug = False
    filterSoftwareName = False
    inputfile = SOFTWARE_FILE
    verbose = False
    download_anyway = False
    human_readable = False
    no_download = False
    save_html = False
    
    #parse command line options
    try:
        opts, args = getopt.getopt(argv,"dhi:n:v",["deep-debug","debug","download-anyway","help","html","human-readable","input-file=","name","no-download","verbose","version"])
    except getopt.GetoptError:
        print(USAGE)
        sys.exit(2)
    if (len(args) > 0):
        print("unknown argument(s): " + args)
        sys.exit(2)
    for opt, arg in opts:
        if opt == "--debug":
            debug = True
        elif opt == "--deep-debug":
            debug = True
            deepdebug = True
        elif opt in ("-d", "--download-anyway"):
            download_anyway = True
        elif opt == "--help":
            print(USAGE)
            sys.exit()
        elif opt in ("-h", "--human-readable"):
            human_readable = True
        elif opt in ("--html"):
            save_html = True
        elif opt in ("-i", "--input-file"):
            inputfile = arg
        elif opt in ("-n", "--name"):
            filterSoftwareName = True
            softwareNameFilter = arg
        elif opt == "--no-download":
            no_download = True
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt == "--version":
            print ("update-checker.py version "+ VERSION)
            sys.exit()
            
    if no_download and download_anyway:
        error("--download-anyway and --no-download are exclusive!")
        print(USAGE)
        sys.exit(2)
    
    # result is a list of softwares that have new versions
    result = []
    #somethingwentwrong is a list of software that could not be checked / downloaded.
    somethingwentwrong = []

    #read csv file into softwares
    softwares = list()
    with open(inputfile, "rb") as csvfile:
        softwarereader = csv.reader(csvfile, delimiter=",", quotechar="\'")
        for row in softwarereader:
            softwares.append(row)
    csvfile.close()
    
    # each entry in SOFTWARE_FILE
    for row in softwares:
        # skip empty lines
        if len(row) < 1:
            continue;
        # skip commented lines
        if row[0].startswith("#"):
            continue
        # line sanity check
        if len(row) < 8:
            warning("%s entry \"%s\" wrong formatted. Skipping..." % (inputfile,",".join(row)))
            continue
        
        software = row[0]
        lang = row[1]
        arch = row[2]
        versite = row[3]
        versionregex = row[4]
        dlsite = row[5]
        dlregex = row[6]
        currver = row[7]
        if len(row) > 8:
            onlycheck = True
        else:
            onlycheck = False
		
        # name filter
        if filterSoftwareName:
            if not(softwareNameFilter.lower() in software.lower()):
                continue
        
        print(software)
        
        latestver = "0"
        if (versite.startswith("ftp://")):
            if debug:
                print("[DEBUG] FTP Transfer")
            
            ftp = FTP(re.compile("ftp://([^/]+)/").findall(versite)[0])
            ftp.login()
            lines = ftp.nlst(re.compile("ftp://[^/]+/(.*)").findall(versite)[0])
            for line in lines:
                ver = line.split("/")[len(line.split("/"))-1]
                if (ver.find(".") > -1):
                    if islater(ver, latestver):
                        latestver = ver
        else:
            try:
                url = urllib2.urlopen(versite)
            except urllib2.URLError as e:
                error("could not open url %s: %s" % (versite, e.strerror))
                continue
            html = url.read()
            
            if deepdebug:
                print(html)
			
            if save_html:
                version_html_file_path = "%s\\%s\\" % (DOWNLOAD_DIR, software)
                version_html_file_name = "%s\\%s\\version.html" % (DOWNLOAD_DIR, software)
                if not os.path.exists(version_html_file_path): os.makedirs(version_html_file_path)
                version_html_file = open(version_html_file_name, 'w')
                version_html_file.write(html)
                version_html_file.close
            
            latestvers = re.compile(versionregex).findall(html)
            if len(latestvers) < 1:
                warning("could not find version on site \n    " + versite + "\n with re \n    " +    versionregex + "\n Skipping " + software)
                somethingwentwrong.append("%s" % (software))
                continue
            latestver = latestvers[0]

        if debug:
            print ("[DEBUG] grep'd version:", latestver)
			
        # if latestver is date (e.g. "31/01/1999")
        if (re.match('\d{2}/\d{2}/\d{4}', latestver) != None):
            latestver =  ".".join(latestver.split("/")[::-1])
        
        # if latestver is date (e.g. "31-01-1999")
        if (re.match('\d{2}-\d{2}-\d{4}', latestver) != None):
            latestver =  ".".join(latestver.split("-")[::-1])
        
        # if latestver is date (e.g. "1999-01-31")
        if (re.match('\d{4}-\d{2}-\d{2}', latestver) != None):
            latestver =  ".".join(latestver.split("-"))
        
        if not download_anyway:
            print(" current version:", currver)
        print(" latest version:", latestver)
        
        dllink = ""
        if (not onlycheck) and islater(latestver, currver):
            if (dlsite.startswith("ftp://")):
                if debug:
                    print("[DEBUG] FTP Transfer")
            else:
                try:
                    url = urllib2.urlopen(dlsite)
                except urllib2.URLError as e:
                    #error("could not open url %s: %f: %s" % (dlsite, e.errno, e.strerror))
                    error("could not open url %s: %s" % (dlsite, e.strerror))
                    continue
                html = url.read()
                
                if deepdebug:
                    print(html)
                    
                if save_html:
                    download_html_file_path = "%s\\%s\\%s\\%s\\%s\\" % (DOWNLOAD_DIR, software, latestver, lang, arch)
                    download_html_file_name = "%s\\%s\\%s\\%s\\%s\\download.html" % (DOWNLOAD_DIR, software, latestver, lang, arch)
                    if not os.path.exists(download_html_file_path): os.makedirs(download_html_file_path)
                    download_html_file = open(download_html_file_name, 'w')
                    download_html_file.write(html)
                    download_html_file.close
				
                dllinks = re.compile(dlregex).findall(html)
                if len(dllinks) < 1:
                    warning("could not find find download link on site \n    " + dlsite + "\n with re \n    " +    dlregex + "\n Skipping " + software)
                    somethingwentwrong.append("%s" % (software))
                    continue
                dllink = dllinks[0]
        
            if debug:
                print ("[DEBUG] grep'd dllink:", dllink)
        
            if dllink.startswith("//"):
                parsed_uri = urlparse(dlsite)
                dllink = "{uri.scheme}:".format(uri=parsed_uri) + dllink
            elif dllink.startswith("/"):
                parsed_uri = urlparse(dlsite)
                dllink = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri) + dllink
            elif not (dllink.startswith("http") or dllink.startswith("ftp")):
                dllink = (dlsite.rsplit("/", 1)[0]) + "/" + dllink
        
            if debug:
                print ("[DEBUG] dllink_processed:", dllink)
        
        if debug:
                print("[DEBUG] islater(%s,%s) = %s" % (latestver,currver,islater(latestver, currver)))
        
        if download_anyway:
            if not onlycheck:
                downloadfile(software, latestver, lang, arch, dllink)
            row[7] = latestver
        elif islater(latestver, currver):
            result.append("%s %s" % (software, latestver))
            if onlycheck:
                print("    skipping download because software is onlycheck")
                #don't download but create folder!
                software_dir = "%s\\%s\\%s\\%s\\%s\\files\\" % (DOWNLOAD_DIR, software, latestver, lang, arch)
                if not (os.path.isdir(software_dir)):
                    os.makedirs(software_dir)
                row[7] = latestver
            elif no_download:
                print("    skipping download because --no-download option was given")
            else:
                print(" latest version is newer than current -> downloading!")
                downloadfile(software, latestver, lang, arch, dllink)
                row[7] = latestver
    
    # save csv file (with new version)
    with open(inputfile, 'wb') as csvfile:
        softwarewriter = csv.writer(csvfile, delimiter=",", quotechar="\'")
        for row in softwares:
            softwarewriter.writerow(row)
    csvfile.close()
    
    print("\nNew software versions:")
    if len(result) > 0:
        print(result)
    else:
        print("No new versions found.")
    
    if len(somethingwentwrong) > 0:
        print("\nSomething went wrong:")
        print(somethingwentwrong)

if __name__ == "__main__":
    main(sys.argv[1:])
    #Development Debugging
    #createCommandFiles("Citavi","5.0.0.11","de","x86","C:\\Users\\ri42rod2\\Downloads\\Citavi\\5.0.0.11\\de\\x86\\files\\Citavi5Setup.msi")
