#!/bin/python3
# Convert images in folders to webp format and only keeping the samller files
# Prerequisites: imagemagick, libwebp

# Make sure to check for warnings and errors in the output!

import os
import sys
from argparse import ArgumentParser
from multiprocessing import Pool
from os import chdir
from os import listdir
from os import walk
from os.path import getsize
from subprocess import check_output
from subprocess import run


def __conv_image(file: str):
    # Webp image size limit: 16384 x 16384 pixels
    image_size = check_output(['identify', file]).decode().removeprefix(file).strip().split(' ')[1].split('x')
    for i in image_size:
        if int(i) > 16384:
            print(f'Error: skipping {file}, size exceeds limit: {image_size[0]}x{image_size[1]}')
            return

    # Convert
    run(['mogrify', '-format', 'webp', '-quality', '100', file])

    # Remove larger file
    try:
        if getsize(file) > getsize(file.rsplit('.', 1)[0] + '.webp'):
            os.remove(file)
        else:
            os.remove(file.rsplit('.', 1)[0] + '.webp')
    except FileNotFoundError:
        pass


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
        print('No image found or all images are webp format.')
        return False
    elif not processed:
        print(f'File count: {len(target_items)}')

        chdir(folder)

        with Pool() as pool:
            pool.map(__conv_image, target_items)
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
    else:
        folders.sort()

    for folder in folders:
        convert(folder)

    print('Done.')
