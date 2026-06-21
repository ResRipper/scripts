#!/bin/python3
# Convert images in folders to webp format and only keeping the samller files
# Prerequisites:
#   - webp: libwebp
#   - jxl: libjxl, imagemagick (webp), libwebp (webp)

# !! Test before use !!
# !! Make sure to check for warnings and errors in the output !!

import glob
import os
import sys
from argparse import ArgumentParser
from functools import partial
from multiprocessing import Pool
from os import chdir
from os import listdir
from os import walk
from os.path import getsize
from secrets import token_hex
from shutil import rmtree
from subprocess import check_output
from subprocess import run


def __conv_image(format: str, file: str, parallel: int):
    """Convert image format.

    Args:
        format (str): Output image format
        file (str): Source image file path
        parallel (int): Number of worker threads for cjxl
    """
    file_name = file.rsplit('.', 1)[0]
    try:
        match format:
            case 'webp':
                # Webp image size limit: 16384 x 16384 pixels
                image_size = (
                    check_output(['identify', file]).decode().removeprefix(file).strip().split(' ')[1].split('x')
                )
                for i in image_size:
                    if int(i) > 16384:
                        print(f'Error: skipping {file}, size exceeds limit: {image_size[0]}x{image_size[1]}')
                        return
                # Convert
                if file.rsplit('.', 1)[-1] == 'gif':
                    run(['gif2webp', '-quiet', '-mt', '-min_size', file, '-o', f'{file_name}.webp'])
                else:
                    run(['img2webp', '-quiet', '-lossless', '-min_size', file, '-o', f'{file_name}.webp'])

            case 'jxl':
                # Lossless, default worker threads
                command = ['cjxl', '--quiet', '-d', '0', '-e', '8', f'--num_threads={parallel}']
                match file.rsplit('.', 1)[-1]:
                    # cjxl doesn't support webp -> jxl natively
                    case 'webp':
                        if 'animated' in check_output(['file', file]).decode():
                            # webp -> *.png -> gif -> jxl
                            temp_folder = f'{file_name}_{token_hex(3)}'
                            os.mkdir(temp_folder)
                            run(['anim_dump', '-folder', temp_folder, file])
                            run(
                                [
                                    'magick',
                                    '-quiet',
                                    '-delay',
                                    '10',
                                    '-loop',
                                    '0',
                                    *glob.glob(f'{temp_folder}/*.png'),
                                    f'{file_name}.gif',
                                ]
                            )
                            rmtree(temp_folder)
                            run([*command, f'{file_name}.gif', f'{file_name}.jxl'])
                            os.remove(f'{file_name}.gif')
                        else:
                            # webp -> png -> jxl
                            tmp_file = f'{file_name}_tmp_{token_hex(3)}.png'
                            run(['dwebp', '-quiet', file, '-o', tmp_file])
                            run([*command, tmp_file, f'{file_name}.jxl'])
                            os.remove(tmp_file)
                    case 'jpg' | 'jpeg':
                        run([*command, '--lossless_jpeg=1', file, f'{file_name}.jxl'])
                    case _:
                        run([*command, file, f'{file_name}.jxl'])

            case _:
                print(f'Unknown format for file: {file}')
                return
    except Exception:
        print(f'Convert failed: {file}')
        return

    # Remove larger file
    try:
        if getsize(file) > getsize(file_name + f'.{format}'):
            os.remove(file)
        else:
            os.remove(file.rsplit('.', 1)[0] + f'.{format}')
    except FileNotFoundError:
        pass


def convert(folder: str, format: str, parallel: int) -> None:
    """Convert process starter.

    Args:
        folder (str): Folder that contain images
        format (str): Output image format
        parallel (int): Number of worker threads for cjxl
    """
    print('Current folder: ' + folder)
    items = listdir(folder)

    target_items = []

    for item in items:
        match item.rsplit('.', 1)[-1]:
            case 'jpg' | 'jpeg' | 'png' | 'gif':
                target_items.append(item)
            case 'webp':
                if format != 'webp':
                    target_items.append(item)
            case 'jxl':
                if format != 'jxl':
                    target_items.append(item)
            case _:
                continue

    if len(target_items) == 0:
        print('No convertable image found.')
        return

    print(f'File count: {len(target_items)}')

    chdir(folder)

    for item in target_items:
        __conv_image(format, item, parallel)
        chdir('../')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        '-p',
        '--parallel',
        type=int,
        default=os.process_cpu_count(),
        help='Number of worker threads for cjxl (default: Avaliable CPU core count)',
    )
    parser.add_argument(
        '-f', '--format', type=str, default='jxl', help='Output format, options: jxl, webp (default: jxl)'
    )
    parser.add_argument('folder', help='Folder to be processed')
    args = parser.parse_args()

    if args.parallel <= 0:
        raise ValueError('Invalid thread count.')

    chdir(args.folder)
    folders: list[str] = next(walk('.'))[1]
    if folders == []:
        sys.exit('No subfolders found.')
    else:
        folders.sort()

    for folder in folders:
        convert(folder, format=args.format, parallel=args.parallel)

    print('Done.')
