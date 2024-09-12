import pytest
import os
import shutil
from src.folder_synchronizer import FolderSynchronizer
from utils import get_random_temp_folder_path, assert_equal_folders
from unittest.mock import patch 

@pytest.fixture
def temp_folder():
  """
    Fixture that creates a temporary folder and deletes it after test execution.
  """
  folder_path = get_random_temp_folder_path()
  os.makedirs(folder_path)
  
  yield folder_path
  
  if os.path.exists(folder_path):
    shutil.rmtree(folder_path)

@pytest.fixture
def source_folder(temp_folder):
  return temp_folder

@pytest.fixture
def replica_folder(temp_folder):
  return temp_folder

@pytest.fixture
def folder_sync() -> FolderSynchronizer:
  """Folder synchronizer fixture with mock source/replica folders"""
  return FolderSynchronizer('/some/source', '/some/replica', 10)

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
  # patch makedirs since /some/replica doesn't yet exist and we don't wanna create it
  with patch.object(os, 'makedirs', side_effect=PermissionError()):
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
  assert_equal_folders(source_folder, replica_folder)