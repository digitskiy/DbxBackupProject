# DBX Backup Project

**DBX Backup Project** is open source software, which is a script in the programming language Python for backing up data to Dropbox.    
This project was built with modularity, extensibility and simplicity in mind.

## Table of Contents

-   [Prerequisites](#prerequisites)
-   [Installation](#installation)
-   [Usage](#usage)
-   [Contributing](#contributing)
-   [Authors](#authors)
-   [License](#license)

## Prerequisites

- [Python](https://www.python.org/downloads) (tested on CPython 3.8)
- [Dropbox Python SDK](https://www.dropbox.com/developers/documentation/python)

## Installation

1. git clone <https://github.com/digitskiy/DbxBackupProject.git>
2. Place the dbx_backup_project.py script in the directory containing the files and folders for backing up to Dropbox;
3. Run the script, this will create the  ignored_list.yaml file;
4. Open file ignored_list.yaml and add file names to the "Optional" item and folders that you do not want to archive and backup (this item is optional);
5. Check the created zip archive in the subfolder with the date, which is in the Backup folder on Dropbox.

> **At the moment, only available - Testing with the generated access token.  
[OAuth 2.0](http://oauth.net/2/) authorization for Dropbox will be added in project later.**    
To test the Dropbox API with your Dropbox account before implementing OAuth,
you can generate an access token from your newly created app under «[My apps](https://www.dropbox.com/developers/apps)», 
by pressing the button that says "Generate" in the OAuth 2 section of your app settings page.

## Usage

To work with the script, you need to place it in the directory containing the files and folders intended for backup to Dropbox.   
When you run the script, a file ignored_list.yaml is automatically created in the same directory.   
The ignored_list.yaml file is intended to exclude files and folders when archiving and further uploading a .zip archive to Dropbox.   

Backup structure on Dropbox:
- The current date serves as the name of a subdirectory in the main Backup directory
- The current time serves as the name of the zip archive in a subdirectory

## Contributing

This project is in active development. I still have a lot
interesting ideas that can be implemented. Therefore, I will be grateful to you for
assistance in the development and improvement of this project.

Pull requests appreciated! However, at the beginning you should read [CONTRIBUTING.md](https://github.com/IniSlice/DbxBackupProject/blob/master/CONTRIBUTING.md), 
to learn more about our code of conduct and the process for sending us [Pull requests](https://github.com/IniSlice/DbxBackupProject/pulls).    
If you find a bug or have a request for improvement, please report a problem [Issue](https://github.com/IniSlice/DbxBackupProject/issues).

## Authors

[**Sergey Chernetskiy**](https://github.com/digitskiy) - developer of this project.    
See also the list of [contributors](https://github.com/IniSlice/DbxBackupProject/graphs/contributors), who participated in this project.

## License

This project is licensed under the MIT License.   
See file [LICENSE.md](https://github.com/IniSlice/DbxBackupProject/blob/master/LICENSE) for details.
