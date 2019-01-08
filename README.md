# update-checker.py
update-checker.py is a little program written in python to read from a list of software and notify of new versions and / or download the newest version of it (if possible).
It was intended to run on Python on Windows and find Windows software, but could probably be used for anything that has some kind of version.

**Develoment halted since 2013**

## History
Development began in 2012 in python, and ended 2013 when I began developing a similiar script (Win-AutoPKG) in PowerShell at the Leibniz-Rechenzentrum (which is, as of yet, not open source).
In other words: This project is pretty much dead, but feel free to try, read and learn from my early python mistakes.

## Installation
Simply git clone the repository, no installation needed

## Usage
Simply run `./update-checker.py`

## What it does
The script runs through the lines in the `software.csv` file and scans the given websites for version numbers with the given regexes. If a new version number is found, it attempts to download the executable given by the second regex.

## software.csv
Each line contains of the following columns:
 * 'software': the name of the software to find updates for.
 * 'lang': the language of the software. Multiple entries (=lines) may exist for different languages.
 * 'arch': the CPU architecture of the software, i.e. x86 or x64. Multiple entries (=lines) may exist for different architectures.
 * 'versite': the URL of the website where the new version number can be found.
 * 'versionregex': the regex with which the newest version can be found.
 * 'dlsite': the URL of the website on which the link to the newest software release can be found.
 * 'dlregex': the regex with which the newest version download string can be found.
 * 'current_version': the current (=offline) version of the software.
 * 'onlycheck': if this is true, no download is attempted, the script only tells the user that a new version is available.

The `software.csv` file is edited by the script with each run: every current_version string is updated to the last online version.

## Development
Feel free to use the script for whatever you like, and change and make it better, if possible. The script should be suffuciently commented for every beginner-level python programmer to understand.
