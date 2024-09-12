"""
  Useful functions to use in tests
"""
import uuid
import os
import tempfile
from src.file_utils import hash_file

def get_random_temp_folder_path():
  """
    Returns a random (unocuppied) folder name in the temp directory
    of your OS.
  """
  base_path = tempfile.gettempdir()
  while True:
    folder_name = str(uuid.uuid4())
    folder_path = os.path.join(base_path, folder_name)
    if not os.path.exists(folder_path):
      return folder_path

def equal_folders(source_folder_path, replica_folder_path) -> bool:
  """
    Walks both folders and, for every file, ensures the same exists in the counterpart
    and the hash is the same. If that's the case, returns true, otherwise, returns false
  """
  for dirpath, _, fnames in os.walk(source_folder_path):
    source_rel_path = os.path.relpath(dirpath, source_folder_path)
    equivalent_replica_path = os.path.join(replica_folder_path, source_rel_path)
    for fname in fnames:
      replica_fpath = os.path.join(equivalent_replica_path, fname)
      source_fpath = os.path.join(dirpath, fname)
      if not os.path.exists(replica_fpath) or hash_file(source_fpath) != hash_file(replica_fpath):
        return False

  for dirpath, _, fnames in os.walk(replica_folder_path):
    replica_rel_path = os.path.relpath(dirpath, replica_folder_path)
    equivalent_source_path = os.path.join(source_folder_path, replica_rel_path)
    for fname in fnames:
      source_fpath = os.path.join(equivalent_source_path, fname)
      replica_fpath = os.path.join(dirpath, fname)
      if not os.path.exists(source_fpath) or hash_file(source_fpath) != hash_file(replica_fpath):
        return False

  return True