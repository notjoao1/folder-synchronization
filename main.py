"""
  Tests:
  - test with regular path names
  - test with weird path names "../../../../../../../passwd" type thing
  - test deleting a file, and seeing it being deleted in replica
  - test deleting a folder, and seeing it being deleted in replica
  - test creating a file in source root + inside nested folders inside source 
  - test updating a file
  - test updating a file's metadata and seeing it being updated on the replica as well (mtime, ctime, permissions)

  Error handling! Check for exceptions where it makes sense to check for them
  CHECK #TODO's!
"""

import argparse
from src.folder_synchronizer import FolderSynchronizer

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="One-way synchronization between two folders.")
  parser.add_argument('-s', '--source', type=str, required=True, help="Source folder that will be replicated in the 'replica' folder.")
  parser.add_argument('-r', '--replica', type=str, required=True, help="Replica folder that will be synchronized with the 'source' folder.")
  parser.add_argument('-i', '--interval', type=int, required=True, help="Interval (in seconds) for periodically synchronizing the 'replica' folder with the 'source' folder.")
  parser.add_argument('-l', '--log-file', type=str, required=True, help="Log file path.")

  args = parser.parse_args() 

  source_path = args.source
  replica_path = args.replica
  interval = args.interval
  log_file_path = args.log_file

  synchronizer = FolderSynchronizer(source_path, replica_path, interval, log_file_path)
  synchronizer.periodic_sync()

