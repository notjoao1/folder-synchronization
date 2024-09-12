import pytest
import os
import shutil
import time
from src.folder_synchronizer import FolderSynchronizer
from src.file_utils import equal_metadata 
from utils import get_random_temp_folder_path, equal_folders 
from unittest.mock import patch 


@pytest.fixture
def source_folder():
  """
    Fixture that creates a temporary folder and deletes it after test execution.
  """
  folder_path = get_random_temp_folder_path()
  os.makedirs(folder_path)
  
  yield folder_path
  
  if os.path.exists(folder_path):
    shutil.rmtree(folder_path)

@pytest.fixture
def replica_folder():
  """
    Fixture that creates a temporary folder and deletes it after test execution.
  """
  folder_path = get_random_temp_folder_path()
  os.makedirs(folder_path)
  
  yield folder_path
  
  if os.path.exists(folder_path):
    shutil.rmtree(folder_path)

@pytest.fixture
def folder_sync() -> FolderSynchronizer:
  """Folder synchronizer fixture with mock source/replica folders"""
  return FolderSynchronizer('/dev/null', '/dev/null', 10)

def test_permission_error_on_source_should_crash(folder_sync: FolderSynchronizer):
  """
    Test that the program exits when we don't have permission to access the source folder.
  """
  with patch.object(os.path, 'exists', return_value=True):
    with patch.object(os, 'listdir', side_effect=PermissionError()):
      with pytest.raises(SystemExit) as sys_exit:
        folder_sync._ensure_source_exists_and_has_permission()

      assert sys_exit.type is SystemExit
      assert sys_exit.value.code == 1

def test_source_doesnt_exist_should_crash(folder_sync: FolderSynchronizer):
  """
    Test that the program exits when we the source folder doesn't exist.
  """
  with patch.object(os.path, 'exists', return_value=False):
    with pytest.raises(SystemExit) as sys_exit:
      folder_sync._ensure_source_exists_and_has_permission()
    
    assert sys_exit.type is SystemExit
    assert sys_exit.value.code == 1
  
def test_permission_error_on_create_replica_should_crash(folder_sync: FolderSynchronizer):
  """
    Test that the program exits when we cannot create the non-existent replica folder due
    to permission errors.
  """
  with patch('builtins.open', side_effect=PermissionError()):
    with pytest.raises(SystemExit) as sys_exit:
      folder_sync._ensure_replica_exists_and_has_permissions()

    assert sys_exit.type is SystemExit
    assert sys_exit.value.code == 1

def test_permission_error_on_replica_should_crash(folder_sync: FolderSynchronizer):
  """
    Test that the program exits when we cannot access the replica folder due
    to permission errors.
  """
  # patch makedirs since /some/replica doesn't yet exist and we don't wanna create it
  with patch.object(os, 'makedirs', return_value=None):
    with patch('builtins.open', side_effect=PermissionError()):
      with pytest.raises(SystemExit) as sys_exit:
        folder_sync._ensure_replica_exists_and_has_permissions()

      assert sys_exit.type is SystemExit
      assert sys_exit.value.code == 1


def test_given_valid_source_and_replica_should_be_synchronized(source_folder, replica_folder):
  """
    Tests that, given a valid source folder with a certain directory structure inside of it,
    its contents should be replicated to a replica folder
  """
  folder_sync = FolderSynchronizer(source_folder, replica_folder, 10, '/dev/null')

  # source_folder 
  # ├── folder1
  #     ├── folder2
  #         └── file2 
  #     └── file1 
  # └── file0
  os.makedirs(os.path.join(source_folder, 'folder1'))
  os.makedirs(os.path.join(source_folder, 'folder1', 'folder2'))
  with open(os.path.join(source_folder, 'file0'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'file1'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'folder2', 'file2'), 'w'):
    pass

  # sync with replica
  folder_sync.sync_folders()

  # assert every path in replica exists in source
  assert equal_folders(source_folder, replica_folder)
  
def test_given_source_changed_replica_should_be_synchronized(source_folder, replica_folder):
  """
    Tests that, given a valid source folder with a directory tree synchronized with the replica folder,
    removing a folder with a file inside of it and synchronizing again, the changes should be reflected
    in the replica folder
  """
  folder_sync = FolderSynchronizer(source_folder, replica_folder, 10, '/dev/null')

  # source_folder 
  # ├── folder1
  #     ├── folder2
  #         └── file2 
  #     └── file1 
  # └── file0
  os.makedirs(os.path.join(source_folder, 'folder1'))
  os.makedirs(os.path.join(source_folder, 'folder1', 'folder2'))
  with open(os.path.join(source_folder, 'file0'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'file1'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'folder2', 'file2'), 'w'):
    pass

  # sync with replica
  folder_sync.sync_folders()

  # remove a whole folder and sync
  shutil.rmtree(os.path.join(source_folder, 'folder1', 'folder2'))

  # at this point, things should NOT be synchronized
  assert not equal_folders(source_folder, replica_folder)

  folder_sync.sync_folders()

  assert equal_folders(source_folder, replica_folder)
  

def test_given_source_folder_file_changed_replica_should_be_synchronized(source_folder, replica_folder):
  """
    Tests that, given a valid source folder with a directory tree synchronized with the replica folder,
    changing a file's contents should be reflected in the replica folder.
  """
  folder_sync = FolderSynchronizer(source_folder, replica_folder, 10, 'test.log')

  # source_folder 
  # ├── folder1
  #     ├── folder2
  #         └── file2 
  #     └── file1 
  # └── file0
  os.makedirs(os.path.join(source_folder, 'folder1'))
  os.makedirs(os.path.join(source_folder, 'folder1', 'folder2'))
  with open(os.path.join(source_folder, 'file0'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'file1'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'folder2', 'file2'), 'w'):
    pass

  # sync with replica
  folder_sync.sync_folders()

  # open a file and append something to change its hash
  with open(os.path.join(source_folder, 'folder1', 'file1'), 'a') as f:
    f.write('0\n')
    f.flush()

  # at this point, things should NOT be synchronized
  assert not equal_folders(source_folder, replica_folder)

  folder_sync.sync_folders()

  assert equal_folders(source_folder, replica_folder)

def test_given_source_folder_added_new_file_replica_should_be_synchronized(source_folder, replica_folder):
  """
    Tests that, given a valid source folder with a directory tree synchronized with the replica folder,
    adding a new file to source during program execution should be reflected with the same file in
    replica. 
  """
  folder_sync = FolderSynchronizer(source_folder, replica_folder, 10, 'test.log')

  # source_folder 
  # ├── folder1
  #     ├── folder2
  #         └── file2 
  #     └── file1 
  # └── file0
  os.makedirs(os.path.join(source_folder, 'folder1'))
  os.makedirs(os.path.join(source_folder, 'folder1', 'folder2'))
  with open(os.path.join(source_folder, 'file0'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'file1'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'folder2', 'file2'), 'w'):
    pass

  # sync with replica
  folder_sync.sync_folders()

  # create new file and folder with a file in source that doesn't yet exist in replica
  with open(os.path.join(source_folder, 'cool_file'), 'w'):
    pass

  os.makedirs(os.path.join(source_folder, 'folder3'))
  with open(os.path.join(source_folder, 'folder3', 'file3'), 'w'):
    pass

  # at this point, things should NOT be synchronized
  assert not equal_folders(source_folder, replica_folder)

  folder_sync.sync_folders()

  assert equal_folders(source_folder, replica_folder)


def test_given_source_folder_changed_file_metadata_replica_should_be_synchronized(source_folder, replica_folder):
  """
    Tests that, given a valid source folder with a directory tree synchronized with the replica folder,
    changing a particular file's metadata, in this case, last modified timestamp, should
    trigger a copy of that file's metadata into the replica_folder
  """
  folder_sync = FolderSynchronizer(source_folder, replica_folder, 10, 'test.log')

  # source_folder 
  # ├── folder1
  #     ├── folder2
  #         └── file2 
  #     └── file1 
  # └── file0
  os.makedirs(os.path.join(source_folder, 'folder1'))
  os.makedirs(os.path.join(source_folder, 'folder1', 'folder2'))
  with open(os.path.join(source_folder, 'file0'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'file1'), 'w'):
    pass
  with open(os.path.join(source_folder, 'folder1', 'folder2', 'file2'), 'w'):
    pass

  # sync with replica
  folder_sync.sync_folders()

  # change file's ctime and mtime
  os.utime(os.path.join(source_folder, 'file0'), (time.time(), time.time()))

  folder_sync.sync_folders()

  assert equal_metadata(os.path.join(source_folder, 'file0'), os.path.join(replica_folder, 'file0'))
  assert equal_folders(source_folder, replica_folder)


def test_copy_file_no_permission_doesnt_exit_or_throw(folder_sync: FolderSynchronizer):
  """
    Test that the program does not exit when trying to copy a file it can't read
    and the error is properly handled
  """
  with patch.object(shutil, 'copy2', side_effect=PermissionError()):
    with patch.object(os, 'exit') as mock_exit:
      try:
        folder_sync._try_copy_file('f1', 'f2')
      except Exception as e:
        pytest.fail(f"_try_copy_file raised an unexpected exception: {e}")

    # Assert that os.exit was not called
    mock_exit.assert_not_called()

def test_hash_file_no_permission_doesnt_exit_or_throw(folder_sync: FolderSynchronizer):
  """
    Test that the program does not exit when trying to hash a file it can't read
    and the error is properly handled
  """
  with patch('builtins.open', side_effect=PermissionError()):
    with patch.object(os, 'exit') as mock_exit:
      try:
        folder_sync._try_hash_file('f1')
      except Exception as e:
        pytest.fail(f"_try_hash_file raised an unexpected exception: {e}")

    # Assert that os.exit was not called
    mock_exit.assert_not_called()

