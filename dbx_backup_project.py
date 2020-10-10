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

dbx = dropbox.Dropbox('')#YOUR_ACCESS_TOKEN
dbx.check_and_refresh_access_token()#Проверяет, нужно ли обновить токен доступа, и, если возможно, обновляет

#Получить путь дериктрии со скриптом
def get_script_dir(follow_symlinks=True):
    if getattr(sys, 'frozen', False): 
        path = os.path.abspath(sys.executable)
    else:
        path = inspect.getabsfile(get_script_dir)
    if follow_symlinks:
        path = os.path.realpath(path)
    return os.path.dirname(path)

#Текущая дата служит именем подкаталога в основном каталоге
today = time.strftime('%d.%m.%Y')
#Текущее время служит именем zip-архива
now = time.strftime('%H_%M_%S')

dir_name = "/Backup/"+today

#список «Игнорируемые файлы» 
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

#Функция, которая проверяет список «Игнорируемые файлы» 
#Затем вы можете исключить такие файлы при загрузки их на dropbox.
def check_ignored_files(ydict, dir_path=get_script_dir()):
    ydict = copy.deepcopy(ydict)#Создаём копию словаря 
    filename = '{path}{sep}ignored_list.yaml'.format(path=dir_path, sep=os.sep)
    try:
        with open(filename, 'r+', encoding='utf-8') as rdata:
            yaml_rdata = yaml.safe_load(rdata)
            if isinstance(yaml_rdata, dict):
                default = yaml_rdata.get("default", None)#получаяем значение словаря по заданному ключу
                optional = yaml_rdata.get("optional", None)#Если ключи не найдены, то возвращяем None
                count = 0
                if isinstance(optional, list):
                    del ydict["optional"][:]
                    for i in optional:
                        if isinstance(i, str) and (i not in ydict["optional"]):
                            ydict["optional"].append(i)
                        elif i!=None:
                            count+=1
                if (not isinstance(default, list)) or (default!=ydict["default"]) or (yaml_rdata.keys()!=ydict.keys()) or (count!=0):
                    #raise AssertionError()
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
    lst = []
    #Путь для файлов и папок которые нужно поместить в backup zip-архив 
    from_backup_path='{script_dir}'.format(script_dir=dir_path)

    #Проверка файла в игнор листе
    ignore_files_and_dirs = set(ignored_dict["default"]+ignored_dict["optional"])

    for root, dirs, files in os.walk(from_backup_path, topdown=True):
    #Проверка файла в игнор листе
        dirs[:] = [d for d in dirs if (d not in ignore_files_and_dirs)]#Исключение каталога из дерева каталогов 
        files = [file for file in files if (file not in ignore_files_and_dirs) and (os.path.splitext(file)[1] not in ignore_files_and_dirs)] #Исключение файлов из каталогов
        for file in files:
            lst.append(os.path.join(root, file))
    return lst


# если папка не существует в Dropbox то создать её
def check_dropbox_dir():
    try:
        dbx.files_get_metadata(dir_name, include_deleted=False)
    except ApiError:
        dbx.files_create_folder_v2(dir_name, False)#Создать папку по указанному пути
        print("Created "+ dir_name + " on Dropbox")
    except Exception as e:
        print("Error {}! Could not create dir with name {}!".format(e, dir_name))
        return False
    return True


def dropbox_backup(dir_path):
    with open(dir_path, 'rb') as file: # открываем файл в режиме чтение побайтово
        file_size = os.path.getsize(dir_path)
        CHUNK_SIZE = 100 * (1024**2) 
        try:
            if file_size <= CHUNK_SIZE:# если размер файла для бэкапа меньше 100 Мб то используем стандарный метод загрузки файла на дропбокс.
                # загружаем файл: первый аргумент (file.read()) - какой файл; второй - название, которое будет присвоено файлу уже на дропбоксе.
                dbx.files_upload(file.read(), dir_name+'/'+now+'.zip', mode=dropbox.files.WriteMode.overwrite) 
            else: #иначе разбиваем файл на куски CHUNK и загружаем каждый кусок используя сиансы загрузки
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
    #Создание временной папки 
    with tempfile.TemporaryDirectory() as tmpdirname:  
        print('Temporary directory created:', tmpdirname)
        #Путь для хранения backup архива zip 
        in_backup_path ='{0}{1}{2}.zip'.format(tmpdirname, os.sep, fname)
        ignore_files = get_list_ignored_file(check_ignored_files(ignored_files))
        #Создание zip файла 
        with zipfile.ZipFile(in_backup_path,'w') as newzip:
            for file in ignore_files:
                newzip.write(file)
            print("The {}.zip archive has been created and the files have been written to it!".format(fname))
        #backup zip ахрива с файлами на Dropbox
        dropbox_backup(in_backup_path)
            
if __name__ == '__main__':
    check_dir = check_dropbox_dir()
    print(main(now, check_dir))


