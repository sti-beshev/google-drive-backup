Google Drive Backup
===================

A python script to sync your google drive contents.

## Features
* You can Download your entire google drive or any given folder
* Downloads a file only if it has been modified since last download
* Logs all actions (optional)
* Uses OAuth2 authentication and can remember authentication
* Exports and downloads native Google Documents, Spreadsheets, and Presentations, as Microsoft Office, Open Office or PDF documents
* You can create a custom list of folders to check and download if needed.

## Requirements
* Google API Python library. To install run
`pip install --upgrade google-api-python-client` or
`easy_install --upgrade google-api-python-client`
* pytz
* tzlocal

## Setup
* Edit `client_secrets_sample.json` and add your Google API client id and client secret (If you don't have one, [get it here](https://code.google.com/apis/console/)).
* Save it as `client_secrets.json`.
* Now, if you run `python drive.py`, a browser window/tab will open for you to authenticate the script.
* Once authentication is done, the script will start downloading your *My Drive*. Refer the next section for more options.

## Options
Following command line options are available.

**--destination** - Path to the folder where the files have to be downloaded to. If not specified, a folder named `downloaded` is created in the current directory.

**--debug** - If present (accepts no value), every step will be logged to the log file.

**--logfile** - Path to the file to which the logs should be written to. By default, writes to `drive.log` in the current directory. The file will be overwritten every time the script is run.

**--drive_id** ID of the folder which you want to download. By default, entire "My Drive" is downloaded.

**--export** Defines the export format for native Google Documents, Spreadsheets, and Presentations: Microsoft Office (MSO), OpenOffice (OO), or PDF.  By default, export to OpenOffice format (.odt for Gdocs; .ods for Gspreadsheets; .pptx for presentations).

**--from_folders_list** Check and download if needed only folders in folders.json.

**--list_folder_names**  Give a list of all the folder names in folders.json.

**--add_folder** Adds folder to folders.json. Have to use it two times with the name of the folder and then with drive id of the folder. Usage :  `--add_folder` 'name of the folder' `--add_folder` 'folder id'. 

##Custom folder list
To add folder to your custom list use :

 `--add_folder` 'name of the folder' `--add_folder` 'folder id' 
 
 All folder names and drive ids will be stored in `folders.json`.
 
 For now if you want to edit or delete folder info in `folders.json`, you have to manually edit the file.
