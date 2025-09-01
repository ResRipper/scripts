#!/bin/python3
# Extract files into their own folder
# Prerequisites: 7zip


import sys
from argparse import ArgumentParser
from multiprocessing import Pool
from os import chdir
from os import walk
from subprocess import DEVNULL
from subprocess import run


def __extract(file: str) -> None:
    """Extract compressed file.

    Args:
        file (str): File name with suffix
    """
    print(f'Processing: {file}')
    run(['7z', 'x', file, f'-o{file.rsplit(".", 1)[0]}'], stdout=DEVNULL)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('folder', help='Folder that contain compressed files')
    args = parser.parse_args()

    chdir(args.folder)
    files: list[str] = next(walk('.'))[2]
    if files == []:
        sys.exit('No subfolders found.')

    job_list = []

    # Filter out files that are not compressed file
    for file in files:
        if file.rsplit('.', 1)[1] in ('7z', 'zip', 'tar', 'rar'):
            job_list.append(file)

    print(job_list)
    if job_list == []:
        sys.exit('No compressed files found.')
    else:
        with Pool() as pool:
            pool.map(__extract, job_list)
