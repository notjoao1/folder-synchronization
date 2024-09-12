import os
import time
import logging
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
    self._logger.info(f"Starting synchronization between source folder '{self.source_path}' and replica folder '{self.replica_path} every {self.interval} seconds.")
    while True:
      init = time.time() 
      self.sync_folders()
      self._logger.info(f"Synchronized replica and source in {time.time() - init:.3f} seconds...")
      time.sleep(self.interval)

  def sync_folders(self) -> None:
    """
      Performs one-way synchronization between source folder and replica folder. 
    """
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
          copy_file(source_fpath, replica_fpath)
          continue

        if not equal_metadata(source_fpath, replica_fpath):
          self._logger.info(f"Detected metadata change in '{source_fpath}', copying metadata to '{replica_fpath}'")
          copy_metadata(source_fpath, replica_fpath)
          # try to compare cached hash with the current hash, and if there's no cached hash
          # just calculate both replica and source hash and compare them to know if contents changed 
          if source_fpath in self._source_file_index:
            self._logger.debug(f"Hash cache hit for key '{source_fpath}'")
            source_hash = hash_file(source_fpath)
            if self._source_file_index[source_fpath] != source_hash:
              self._logger.info(f"File contents changed inside '{source_fpath}', copying it over to '{replica_fpath}'...")
              copy_file(source_fpath, replica_fpath)
              self._source_file_index[source_fpath] = source_hash
            continue

          self._logger.debug(f"Hash cache miss for '{source_fpath}'")
          source_hash = hash_file(source_fpath)
          replica_hash = hash_file(replica_fpath)
          self._source_file_index[source_fpath] = source_hash
          if source_hash != replica_hash:
            self._logger.info(f"File contents changed inside '{source_fpath}', copying it over to '{replica_fpath}'...")
            copy_file(source_fpath, replica_fpath)


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

  def _setup_logger(self, log_file_path: str = None) -> None:
    """
      Setup logging for both stdout and, optionally, an output file. 
    """
    self._logger = logging.getLogger(__name__)
    self._logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)

    if log_file_path:
      file_handler = logging.FileHandler(log_file_path)
      file_handler.setLevel(logging.INFO)
      file_handler.setFormatter(formatter)
      self._logger.addHandler(file_handler)

    self._logger.addHandler(stdout_handler)