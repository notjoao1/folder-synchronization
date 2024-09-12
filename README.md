# Folder Synchronization

This repository contains a [python](https://www.python.org/) script to periodically perform one-way synchronization between two folders `source` and `replica`, such that replica will be strictly equal to `source`.

## Installation

- This script requires **python** 3.9 or greater and **PIP**. Refer to [the official python website](https://www.python.org/downloads/) for instructions on how to install both on your machine.


### Windows

- Installing program requirements:

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

### Linux

- Installing program requirements (ensure you have `python3-venv` available in your machine, otherwise the first command might fail):

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Running

After installing the program requirements, you can run the script using the following command:

### Usage

- Executing the script:

```bash
python3 main.py -s SOURCE_FOLDER -r REPLICA_FOLDER -i INTERVAL -l LOG_FILE
```

- Getting help:

```bash
python3 main.py -h
```

### Arguments

- `-s/--source`: The source folder whose contents will be replicated in the `replica` folder.

- `-r/--replica`: The replica folder whose contents will be strictly equal to the contents of the `source` folder, periodically updating based on `interval`.

- `-i/--interval INTERVAL`: The interval (in seconds) for periodically synchronizing the replica folder with the source folder.

- `-l/--log-file LOG_FILE`: The path to the log file where logging will be recorded in.


## Running tests

After installing the program requirements, you can run tests, using pytest, in the following manner:

```bash
pytest
# if the above doesn't work, try:   python3 -m pytest
```

### Test Cases

- Given a valid source folder with files and folders inside of it, the replica folder should correctly reflect it.

- Given a valid source folder with files and folders inside of it, deleting files/folders off of the source folder should be reflected in the replica folder, with the same file being deleted off of it.

- Given a valid source folder with files and folders inside of it, changing a file's contents should trigger copying the folder over to the replica folder.

- Given a valid source folder with files and folders inside of it, when adding a new file to the source folder, the replica folder should have that file as well after synchronization.

- Given a valid source folder with files and folders inside of it, when changing a file's metadata in the source folder, the replica folder's counterpart file should have its metadata updated to equal.

- Given a file in the source folder that cannot be read by the user executing the program, when trying to hash that file, the permission error should be caught and the program should continue execution.

- Given a file in the source folder that cannot be read by the user executing the program, when trying to copy that file to the replica folder, the permission error should be caught and the program should continue execution.

- Given a non-existent source folder, the program should exit with a non-zero exit code, logging the error correctly.

- Given the provided replica folder path is in a location the user executing the program cannot access (due to permissions), the program should exit with a non-zero exit code, logging the error correctly.


All tests passed on both Linux and Windows.