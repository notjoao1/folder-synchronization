import hashlib
import shutil
import os
from typing import Union

def hash_file(filepath: str) -> str:
  """
    Generates the MD5 hash of a file.
  """
  sum = hashlib.md5()
  with open(filepath, 'rb') as file:
    while chunk := file.read(65536):
      sum.update(chunk)

  return sum.hexdigest()

def copy_file(source_fpath: str, replica_fpath: str) -> None:
  """
    Copies a file and its metadata from the source path to the replica path,
    assuming the directory tree under the replica path exists. 
  """
  shutil.copy2(source_fpath, replica_fpath)

def copy_metadata(source_fpath: str, replica_fpath: str) -> None:
  """
    Copies the metadata of a file from the source path to the replica path,
    assuming the directory tree under the replica path exists. 
  """
  shutil.copystat(source_fpath, replica_fpath)

def remove_folder(path: str) -> None:
  """
    Removes folder and nested tree under it. 
  """
  shutil.rmtree(path, ignore_errors=True)

def get_file_metadata(filepath: str) -> Union[dict, None]:
  """
    Returns the following metadata associated with the given file at 'filepath', if it exists:
    - 'ctime' - change timestamp
    - 'mtime' - last modified timestamp
    - 'mode'  - permission bits 
    - 'uid'   - user id of the file owner
    - 'gid'   - group id of the file owner
    - 'size'  - size of file in bytes
    If file doesn't exist, returns None.
  """
  if not os.path.exists(filepath):
    return None

  metadata = os.stat(filepath)
  return {
    "ctime" : int(metadata.st_ctime),
    "mtime" : int(metadata.st_mtime),
    "mode"  : metadata.st_mode,
    "uid"   : metadata.st_uid,
    "gid"   : metadata.st_gid,
    "size"  : metadata.st_size,
  }

def equal_metadata(f1_path: str, f2_path: str) -> bool:
  """
    Compares the metadata of two files
  """
  return get_file_metadata(f1_path) == get_file_metadata(f2_path)
