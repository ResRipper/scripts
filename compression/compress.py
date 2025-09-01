#!/bin/python3
# Compress files in folders to a zip file named after their folder's name.
# Prerequisites: zip


import sys
from argparse import ArgumentParser
from os import chdir
from os import walk
from subprocess import run

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('folder', help='Folder to be processed')
    args = parser.parse_args()

    chdir(args.folder)
    folders: list[str] = next(walk('.'))[1]
    if folders == []:
        sys.exit('No subfolders found.')

    for folder in folders:
        chdir(folder)
        run(['zip', '-9', '-r', f'../{folder}.zip', '*'])
        chdir('../')
