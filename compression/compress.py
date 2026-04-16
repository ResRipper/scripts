#!/bin/python3
# Compress files in folders to a compressed file named after their folder's name.
# Prerequisites: 7zip


import subprocess
import sys
from argparse import ArgumentParser
from functools import partial
from multiprocessing import Pool
from os import chdir
from os import walk
from shutil import rmtree


def __compress(folder: str, archive_type: str = 'zip'):
    """Compress files into a single zip file.

    Args:
        folder (str): Folder that contain files
        archive_type (str): Archive type, zip by default
    """
    print(f'Compressing: {folder}')
    chdir(folder)
    try:
        # Highest compression level
        # Stop if can't open some files
        # Do not change modified time
        subprocess.run(
            f"7z a -mx=9 -sse -ssp -r ../$'{folder.replace("'", "\\'")}'.{archive_type} .",
            shell=True,
            capture_output=True,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as call_error:
        print(f'Fail to compress: {folder}\nError message: {call_error.stderr}')
        return
    chdir('../')
    rmtree(folder)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t', '--archive_type', default='zip', help='Archive type, zip by default')
    parser.add_argument('folder', help='Folder to be processed')
    args = parser.parse_args()

    chdir(args.folder)
    folders: list[str] = next(walk('.'))[1]
    if folders == []:
        sys.exit('No subfolders found.')

    with Pool() as pool:
        pool.map(partial(__compress, archive_type=args.archive_type), folders)
