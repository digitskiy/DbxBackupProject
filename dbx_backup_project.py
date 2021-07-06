import inspect
import os
import sys
import copy
import zipfile
import tempfile
import time
import yaml
from yaml.error import YAMLError
import dropbox
from dropbox.exceptions import ApiError
from dropbox.files import GetMetadataError

dbx = dropbox.Dropbox('<YOUR_ACCESS_TOKEN>')
#Checks if the access token needs to be updated and updates if possible
dbx.check_and_refresh_access_token()

def get_script_dir(follow_symlinks=True):
    """ Get the path of the script directory """
    if getattr(sys, 'frozen', False): 
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

#The current date is the name of a subdirectory in the main directory
today = time.strftime('%d.%m.%Y')
#The current time serves as the name of the zip archive
now = time.strftime('%H_%M_%S')

dir_name = "/Backup/"+today

#List of ignored files
ignored_files = {
    "default": [
        "desktop.ini",
        "thumbs.db",
        ".ds_store",
        ".icon",
        ".dropbox",
        ".dropbox.attr",
        ".py",
        "ignored_list.yaml",
        ".ipynb"],
    "optional": [None]
        }

def check_ignored_files(ydict, dir_path=get_script_dir()):
    """
    Function that checks the list of ignored files.
    Then you can exclude such files when uploading them to dropbox.
    """
    #Making a full copy of the dictionary
    ydict = copy.deepcopy(ydict)
    filename = '{path}{sep}ignored_list.yaml'.format(path=dir_path, sep=os.sep)
    try:
        with open(filename, 'r+', encoding='utf-8') as rdata:
            yaml_rdata = yaml.safe_load(rdata)
            if isinstance(yaml_rdata, dict):
                default = yaml_rdata.get("default", None)
                optional = yaml_rdata.get("optional", None)
                count = 0
                if isinstance(optional, list):
                    del ydict["optional"][:]
                    for i in optional:
                        if isinstance(i, str) and (i not in ydict["optional"]):
                            ydict["optional"].append(i)
                        elif i!=None:
                            count+=1
                if (not isinstance(default, list)) or (default!=ydict["default"]) or (yaml_rdata.keys()!=ydict.keys()) or (count!=0):
                    with open(filename, 'w') as wdata:
                        yaml.dump({"default":ydict["default"], "optional":ydict["optional"]}, wdata, default_flow_style=False)
                        print('File overwritten! step1')
            else:
                raise AssertionError()
    except (YAMLError, IOError, FileNotFoundError, AssertionError):
        with open(filename, 'w') as wdata:
            yaml.dump(ignored_files, wdata, default_flow_style=False)
        print('File overwritten! step2')
    except Exception as e:
        print("Unknown Error!", e)
    finally:
        return ydict

def get_list_ignored_file(ignored_dict, dir_path=get_script_dir()):
    """ Forming a list files and directories in the directory tree to be placed in the backup zip archive """
    lst = []
    #Path for files and folders to be placed in the backup zip archive
    from_backup_path='{script_dir}'.format(script_dir=dir_path)
    ignore_files_and_dirs = set(ignored_dict["default"]+ignored_dict["optional"])
    #Checking a file in the ignore list
    for root, dirs, files in os.walk(from_backup_path, topdown=True):
    #Excluding a directory from a directory tree
        dirs[:] = [d for d in dirs if (d not in ignore_files_and_dirs)]
        #Excluding files from directories
        files = [file for file in files if (file not in ignore_files_and_dirs) and (os.path.splitext(file)[1] not in ignore_files_and_dirs)]
        for file in files:
            lst.append(os.path.join(root, file))
    return lst

def check_dropbox_dir():
    """ 
    Checks for a backup folder in Dropbox.
    If there is no folder, then it is created.
    """
    try:
        dbx.files_get_metadata(dir_name, include_deleted=False)
    except ApiError:
        #Create a folder at the specified path
        dbx.files_create_folder_v2(dir_name, False)
        print("Created "+ dir_name + " on Dropbox")
    except Exception as e:
        print("Error {}! Could not create dir with name {}!".format(e, dir_name))
        return False
    return True

def dropbox_backup(dir_path):
    """ Uploading zip archive depending on its size on the dropbox """
    #Open the file in byte-by-byte read mode
    with open(dir_path, 'rb') as file:
        file_size = os.path.getsize(dir_path)
        CHUNK_SIZE = 100 * (1024**2) 
        try:
            #if the file size for backup is less than 100 MB, then use the standard method of uploading the file to the dropbox.
            if file_size <= CHUNK_SIZE:
                #load the file: the first argument is the byte value of the file;  
                #the second is the name that will be assigned to the file already on the dropbox;
                #the third is the file overwrite mode on the dropbox
                dbx.files_upload(file.read(), dir_name+'/'+now+'.zip', mode=dropbox.files.WriteMode.overwrite) 
            #else we split the file into chunks and download each chunk using upload seances
            else: 
                upload_session_start_result = dbx.files_upload_session_start(file.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset=file.tell())
                commit = dropbox.files.CommitInfo(path=dir_name+'/'+now+'.zip', mode=dropbox.files.WriteMode.overwrite)
                while file.tell() < file_size:
                    if ((file_size - file.tell()) <= CHUNK_SIZE):
                        print (dbx.files_upload_session_finish(file.read(CHUNK_SIZE), cursor, commit))
                    else:
                        dbx.files_upload_session_append(file.read(CHUNK_SIZE), cursor.session_id, cursor.offset)
                        cursor.offset = file.tell() 
        except (ApiError, TypeError, OSError):
            print('Error! Could not upload the files!') 

def main(fname, created_dropbox_dir = False):
    if (not created_dropbox_dir):
        return 'Error! Could not create dir on Dropbox.'
    #Creating a temporary directory 
    with tempfile.TemporaryDirectory() as tmpdirname:  
        print('Temporary directory created:', tmpdirname)
        #Path for storing the backup zip archive
        in_backup_path ='{0}{1}{2}.zip'.format(tmpdirname, os.sep, fname)
        ignore_files = get_list_ignored_file(check_ignored_files(ignored_files))
        #Create a zip file
        with zipfile.ZipFile(in_backup_path,'w') as newzip:
            for file in ignore_files:
                newzip.write(file)
            print("The {}.zip archive has been created and the files have been written to it!".format(fname))
        #Backup zip archive with files on Dropbox
        dropbox_backup(in_backup_path)
            
if __name__ == '__main__':
    check_dir = check_dropbox_dir()
    print(main(now, check_dir))


