#!/bin/python3
# Compress files in folders to a zip file named after their folder's name.
# Prerequisites: zip


import sys
from argparse import ArgumentParser
from multiprocessing import Pool
from os import chdir
from os import walk
from subprocess import DEVNULL
from subprocess import run


def __compress(folder: str):
    """Compress files into a single zip file.

    Args:
        folder (str): Folder that contain files
    """
    print(f'Compressing: {folder}')
    chdir(folder)
    run(f"zip -9 -r ../'{folder}'.zip *", shell=True, stdout=DEVNULL)
    chdir('../')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('folder', help='Folder to be processed')
    args = parser.parse_args()

    chdir(args.folder)
    folders: list[str] = next(walk('.'))[1]
    if folders == []:
        sys.exit('No subfolders found.')

    with Pool() as pool:
        pool.map(__compress, folders)
