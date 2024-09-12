import os
import time
import logging
from typing import Union
from .file_utils import hash_file, copy_file, remove_folder, copy_metadata, equal_metadata


class FolderSynchronizer:
  def __init__(self, source_path: str, replica_path: str, interval: int, log_file_path: str = None):
    self.source_path = os.path.normpath(source_path)
    self.replica_path = os.path.normpath(replica_path)
    self.interval = interval
    # for caching source folder files hashes
    self._source_file_index = dict()
    self._setup_logger(log_file_path)

  def periodic_sync(self) -> None:
    """
      Periodically synchronizes source and replica folder in a periodic manner,
      according to the given interval. 
    """
    self._logger.info(f"Starting synchronization between source folder '{self.source_path}' and replica folder '{self.replica_path}' every {self.interval} seconds.")
    while True:
      init = time.time() 
      self.sync_folders()
      self._logger.info(f"Synchronization between replica and source done in {time.time() - init:.3f} seconds...")
      time.sleep(self.interval)

  def sync_folders(self) -> None:
    """
      Performs one-way synchronization between source folder and replica folder. 
    """
    self._ensure_folders_exist()
    self._sync_source_to_replica()
    self._sync_replica_to_source()

  def _sync_source_to_replica(self) -> None:
    """
      Walks source directory and copies files from source to replica if they don't exist, or their
      hash has been modified, or their metadata changed.
    """
    for dirpath, _, fnames in os.walk(self.source_path):
      # relative path from source to the current "dirpath"
      src_rel_path = os.path.relpath(dirpath, self.source_path)
      replica_folder_path = os.path.join(self.replica_path, src_rel_path)

      if not os.path.exists(replica_folder_path):
        self._logger.info(f"Folder '{replica_folder_path}' doesn't exist in replica, creating it...")
        os.makedirs(replica_folder_path, exist_ok=True)

      for fname in fnames:
        source_fpath = os.path.join(dirpath, fname)
        replica_fpath = os.path.join(replica_folder_path, fname)

        if not os.path.exists(replica_fpath):
          self._logger.info(f"File '{source_fpath}' doesn't exist in replica, copying it over to '{replica_fpath}'...")
          self._try_copy_file(source_fpath, replica_fpath)
          continue

        if not equal_metadata(source_fpath, replica_fpath):
          self._logger.info(f"Detected metadata change in '{source_fpath}', copying metadata to '{replica_fpath}'")
          copy_metadata(source_fpath, replica_fpath)
          # try to compare cached hash with the current hash, and if there's no cached hash
          # just calculate both replica and source hash and compare them to know if contents changed 
          if source_fpath in self._source_file_index:
            self._logger.debug(f"Hash cache hit for key '{source_fpath}'")
            source_hash = self._try_hash_file(source_fpath)
            if source_hash is None:
              # skip files we cannot read
              continue
            if self._source_file_index[source_fpath] != source_hash:
              self._logger.info(f"File contents changed inside '{source_fpath}', copying it over to '{replica_fpath}'...")
              self._try_copy_file(source_fpath, replica_fpath)
              self._source_file_index[source_fpath] = source_hash
            continue

          self._logger.debug(f"Hash cache miss for '{source_fpath}'")
          source_hash = self._try_hash_file(source_fpath)
          replica_hash = self._try_hash_file(replica_fpath)
          self._source_file_index[source_fpath] = source_hash
          if source_hash != replica_hash:
            self._logger.info(f"File contents changed inside '{source_fpath}', copying it over to '{replica_fpath}'...")
            self._try_copy_file(source_fpath, replica_fpath)


  def _sync_replica_to_source(self) -> None:
    """
      Walks replica directory and deletes folders and files that no longer exist in source.
    """
    for dirpath, _, fnames in os.walk(self.replica_path):
      replica_rel_path = os.path.relpath(dirpath, self.replica_path)
      src_folder_path = os.path.join(self.source_path, replica_rel_path)

      if not os.path.exists(src_folder_path):
        remove_folder(dirpath)
        self._logger.info(f"Folder '{replica_rel_path}' doesn't exist in source, removing it...")
        continue

      for fname in fnames:
        replica_fpath = os.path.join(dirpath, fname)
        source_fpath = os.path.join(src_folder_path, fname)
        if not os.path.exists(source_fpath):
          self._logger.info(f"File '{replica_fpath}' in replica no longer exists in source, removing it...")
          os.remove(replica_fpath)
  
  def _try_copy_file(self, source_fpath: str, replica_fpath: str) -> None:
    """
      Wraps copy operations around a try except block for dealing with permission errors on particular files,
      and logs failed operations.
    """
    try:
      copy_file(source_fpath, replica_fpath)
    except PermissionError as e:
      self._logger.error(f"Permission error while copying file '{source_fpath} to replica: {e}. Ignoring it.")

  def _try_hash_file(self, filepath: str) -> Union[str, None]:
    """
      Wraps the operation of hashing a file around a try except block in the case we cannot read the file,
      logging failed operations.  
    """
    file_hash = None
    try:
      file_hash = hash_file(filepath)
    except PermissionError as e:
      self._logger.error(f"Permission error while hashing file '{filepath}: {e}.")
    return file_hash

  def _ensure_folders_exist(self) -> None:
    """
      Checks if source folder exists and we have permission to read from it, otherwise exit.
      Checks if replica folder exists and creates it if we have permission to do so, otherwise exit.
    """
    self._ensure_source_exists_and_has_permission()
    self._ensure_replica_exists_and_has_permissions()
  
  def _ensure_source_exists_and_has_permission(self) -> None:
    """
      Checks whether source exists and we have read/execute permissions on it, exits otherwise.
    """
    if not os.path.exists(self.source_path):
      self._logger.critical(f"Source folder '{self.source_path}' doesn't exist, exiting.")
      exit(1)

    # check if we have read/execute permissions on source folder by listing files inside of it
    try:
      os.listdir(self.source_path)
    except PermissionError:
      self._logger.critical(f"Cannot access source folder '{self.source_path}', exiting.")
      exit(1)
  
  def _ensure_replica_exists_and_has_permissions(self) -> None:
    """
      Checks whether replica exists, and create it if not.
      If we cannot create it due to permission errors, exit the program.
    """
    if not os.path.exists(self.replica_path):
      try:
        self._logger.info(f"Replica folder '{self.replica_path}' doesn't exist... creating it.")
        os.makedirs(self.replica_path, exist_ok=True)
      except PermissionError as e:
        self._logger.critical(f"Permission error on creating replica folder: {e}... exiting.")
        exit(1)

    # check if we have write permissions on replica directory by creating an empty file (and cleaning up afterwards)
    try:
        test_file = os.path.join(self.replica_path, '.test_write_permission')
        with open(test_file, 'w') as _:
            pass
        os.remove(test_file)
    except PermissionError:
        self._logger.critical(f"No write permissions for replica folder '{self.replica_path}'... exiting.")
        exit(1)

  def _setup_logger(self, log_file_path: str = None) -> None:
    """
      Setup logging for both stderr and, optionally, an output file. 
      Exits program if missing permissions to create log file at given path.
    """
    self._logger = logging.getLogger(__name__)
    self._logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)
    self._logger.addHandler(stdout_handler)


    if log_file_path:
      try:
        file_handler = logging.FileHandler(log_file_path)
      except PermissionError as e:
        self._logger.critical(f"Permission error on creating log file: {e}... exiting.")
        exit(1)

      file_handler.setLevel(logging.INFO)
      file_handler.setFormatter(formatter)
      self._logger.addHandler(file_handler)