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

def assert_equal_folders(source_folder_path, replica_folder_path):
  """
    Walks replica folder and, for every file, ensures the same exists in the source
    folder and the hash of the source counterpart is the same. 
  """
  for dirpath, _, fnames in os.walk(replica_folder_path):
    replica_rel_path = os.path.relpath(dirpath, replica_folder_path)
    equivalent_source_path = os.path.join(source_folder_path, replica_rel_path)
    for fname in fnames:
      source_fpath = os.path.join(equivalent_source_path, fname)
      replica_fpath = os.path.join(dirpath, fname)
      assert os.path.exists(source_fpath)
      assert hash_file(source_fpath) == hash_file(replica_fpath)

