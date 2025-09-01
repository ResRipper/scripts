#!/bin/python3
# Extract files into their own folder
# Prerequisites: 7zip


import sys
from argparse import ArgumentParser
from os import chdir
from os import walk
from subprocess import run

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('folder', help='Folder that contain compressed files')
    args = parser.parse_args()

    chdir(args.folder)
    files: list[str] = next(walk('.'))[2]
    if files == []:
        sys.exit('No subfolders found.')

    for file in files:
        match file.rsplit('.', 1)[1]:
            case '7z' | 'zip' | 'tar' | 'rar':
                run(['7z', 'x', file, f'-o{file.rsplit(".", 1)[0]}'])
                break
            case _:
                print(f'Unknown file type: {file}')
