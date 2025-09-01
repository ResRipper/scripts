#!/bin/python3
# Convert images in folders to webp format and only keeping the samller files
# Prerequisites: imagemagick, libwebp

import os
import sys
from argparse import ArgumentParser
from multiprocessing import Pool
from os import chdir
from os import listdir
from os import walk
from os.path import getsize
from subprocess import run


def __conv_image(file: str):
    run(['mogrify', '-format', 'webp', '-quality', '100', file])


def image_clean(items: list[str]):
    """Remove larger image file.

    Args:
        items (list[str]): Image list (webp file not included)
    """
    print('Start removing larger files...')

    for item in items:
        try:
            if getsize(item) > getsize(item.rsplit('.', 1)[0] + '.webp'):
                os.remove(item)
            else:
                os.remove(item.rsplit('.', 1)[0] + '.webp')
        except FileNotFoundError:
            print(f'Duplicate file name: {item}')


def convert(folder: str) -> bool:
    """Convert images to webp format and remove larger files.

    Args:
        folder (str): Folder that contain images

    Returns:
        bool: True if folder is processed
    """
    print('Current folder: ' + folder)
    items = listdir(folder)

    processed = False
    target_items = []

    for item in items:
        if item.endswith('.webp'):
            processed = True
        elif item.endswith(('.jpg', '.jpeg', '.png')):
            target_items.append(item)

    if len(target_items) == 0:
        print('No images found.')
        return False
    elif not processed:
        print(f'File count: {len(target_items)}')

        chdir(folder)

        with Pool() as pool:
            pool.map(__conv_image, target_items)

        chdir('../')

    chdir(folder)
    image_clean(target_items)
    chdir('../')

    return not processed


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('folder', help='Folder to be processed')
    args = parser.parse_args()

    chdir(args.folder)
    folders: list[str] = next(walk('.'))[1]
    if folders == []:
        sys.exit('No subfolders found.')

    for folder in folders:
        convert(folder)

    print('Done.')
