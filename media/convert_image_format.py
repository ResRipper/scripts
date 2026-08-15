#!/bin/python3
# Convert images in folders to webp format and only keeping the samller files
# Prerequisites:
#   imagemagick, libjxl, libwebp

# !! Test before use !!
# !! Make sure to check for warnings and errors in the output !!

import glob
import os
import subprocess
import sys
from argparse import ArgumentParser
from multiprocessing import Pool
from os import chdir
from os import listdir
from os import walk
from os.path import getsize
from secrets import token_hex
from shutil import rmtree
from subprocess import run


def __png(file: str, tmp: bool = False) -> str:
    """Convert image to png/apng.

    Args:
        file (str): Source image file path
        tmp (bool, optional): Wether the output file is temporary. Defaults to False.

    Returns:
        str: Output file name without extention
    """
    file_ext = file.rsplit('.', 1)[-1]

    file_name = file.rsplit('.', 1)[0]
    file_name_target = ''
    if tmp:
        file_name_target = f'{file_name}_{token_hex(3)}'
    else:
        file_name_target = file_name

    match file_ext:
        case 'jpg' | 'jpeg':
            run(['magick', '-format', 'png', '-quality', '100', file])
            run(['mv', f'{file_name}.png', f'{file_name_target}.png'])

        case 'webp':
            if 'animated' in subprocess.check_output(['file', file]).decode():
                # webp -> *.png -> apng
                os.mkdir(file_name_target)
                run(['anim_dump', '-folder', file_name_target, file])
                run(
                    [
                        'magick',
                        '-quiet',
                        '-delay',
                        '10',
                        '-loop',
                        '0',
                        '-quality',
                        '100',
                        *glob.glob(f'{file_name_target}/*.png'),
                        f'APNG:{file_name_target}.apng',
                    ]
                )
                rmtree(file_name_target)
            else:
                run(['dwebp', '-quiet', file, '-o', f'{file_name_target}.png'])

        case 'jxl':
            if 'Animation' in subprocess.check_output(['jxlinfo', file]).decode():
                run(['djxl', '--quiet', file, f'{file_name_target}.apng'])
            else:
                run(['djxl', '--quiet', file, f'{file_name_target}.png'])

        case 'gif':
            run(
                [
                    'ffmpeg',
                    '-hide_banner',
                    '-loglevel',
                    'error',
                    '-lossless',
                    '1',
                    '-i',
                    file,
                    f'{file_name_target}.apng',
                ]
            )

        case _:
            print(f'Unknow source image format for file: {file}')

    return file_name_target


def __webp_size_check(file: str):
    # Webp image size limit: 16384 x 16384 pixels
    image_size = (
        subprocess.check_output(['identify', file]).decode().removeprefix(file).strip().split(' ')[1].split('x')
    )
    for i in image_size:
        if int(i) > 16384:
            raise AttributeError(f'Error: skipping {file}, size exceeds limit: {image_size[0]}x{image_size[1]}')


def __webp(file: str):
    """Convert image to webp.

    Args:
        file (str): Source image file path
    """
    file_name = file.rsplit('.', 1)[0]
    file_ext = file.rsplit('.', 1)[-1]

    # Convert
    match file_ext:
        case 'jxl':
            # jxl -> png/apng -> webp
            tmp_file = __png(file, True)
            if 'Animation' in subprocess.check_output(['jxlinfo', file]).decode():
                run(['magick', '-quiet', '-quality', '100', f'APNG:{tmp_file}.apng', f'{file_name}.webp'])
                os.remove(f'{tmp_file}.apng')
            else:
                __webp_size_check(file)
                run(['img2webp', '-lossless', '-min_size', f'{tmp_file}.png', '-o', f'{file_name}.webp'])
                os.remove(f'{tmp_file}.png')
        case 'gif':
            run(['gif2webp', '-mt', '-min_size', file, '-o', f'{file_name}.webp'])
        case _:
            __webp_size_check(file)
            run(['img2webp', '-lossless', '-min_size', file, '-o', f'{file_name}.webp'])


def __jxl(file: str, parallel: int):
    """Convert image to JPEGXL.

    Args:
        file (str): Source image file path
        parallel (int): Number of worker threads for cjxl
    """
    file_name = file.rsplit('.', 1)[0]
    file_ext = file.rsplit('.', 1)[-1]

    # Lossless, default worker threads
    command = ['cjxl', '--quiet', '-d', '0', '-e', '8', f'--num_threads={parallel}']
    match file_ext:
        # cjxl doesn't support webp -> jxl natively
        case 'webp':
            tmp_file = __png(file, True)
            if 'animated' in subprocess.check_output(['file', file]).decode():
                # webp -> apng -> jxl
                run([*command, f'{tmp_file}.apng', f'{file_name}.jxl'])
                os.remove(f'{tmp_file}.apng')
            else:
                # webp -> png -> jxl
                run([*command, f'{tmp_file}.png', f'{file_name}.jxl'])
                os.remove(f'{tmp_file}.png')
        case 'jpg' | 'jpeg':
            run([*command, '--lossless_jpeg=1', file, f'{file_name}.jxl'])
        case _:
            run([*command, file, f'{file_name}.jxl'])


def __conv_image(format: str, file: str, parallel: int, keep: str):
    """Convert image format.

    Args:
        format (str): Output image format
        file (str): Source image file path
        parallel (int): Number of worker threads for cjxl
        keep (str): Select which file to keep
    """
    try:
        match format:
            case 'webp':
                __webp(file)
            case 'jxl':
                __jxl(file, parallel)
            case 'png':
                __png(file)
            case _:
                print(f'Unknown target format for file: {file}')
                return
    except Exception:
        print(f'Convert failed: {file}')
        return

    # Remove file
    try:
        match keep:
            case 'smaller':
                if getsize(file) > getsize(file.rsplit('.', 1)[0] + f'.{format}'):
                    os.remove(file)
                else:
                    os.remove(file.rsplit('.', 1)[0] + f'.{format}')

            case 'out':
                os.remove(file)

            case _:
                raise ValueError(f'Unknown option: {keep}')
    except FileNotFoundError:
        pass


def convert(folder: str, format: str, parallel: int, keep: str) -> None:
    """Convert process starter.

    Args:
        folder (str): Folder that contain images
        format (str): Output image format
        parallel (int): Number of worker threads for cjxl
        keep (str): Select which file to keep
    """
    print('Current folder: ' + folder)

    target_items = []

    for item in listdir(folder):
        match item.rsplit('.', 1)[-1]:
            case 'jpg' | 'jpeg' | 'gif':
                target_items.append(item)
            case 'webp':
                if format != 'webp':
                    target_items.append(item)
            case 'jxl':
                if format != 'jxl':
                    target_items.append(item)
            case 'png':
                if format != 'png':
                    target_items.append(item)
            case _:
                continue

    if len(target_items) == 0:
        print('No convertable image found.')
        return

    print(f'File count: {len(target_items)}')

    chdir(folder)

    if format == 'webp':
        # Parallel
        with Pool() as p:
            p.starmap(__conv_image, [(format, item, parallel, keep) for item in target_items])
    else:
        for item in target_items:
            __conv_image(format, item, parallel, keep)


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
        '-f', '--format', type=str, default='jxl', help='Output format, options: jxl, png, webp (default: jxl)'
    )
    parser.add_argument(
        '-k',
        '--keep',
        type=str,
        default='smaller',
        help='Select which file to keep, options: out, smaller (default: smaller)',
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
        convert(folder, format=args.format, parallel=args.parallel, keep=args.keep)
        chdir('../')

    print('Done.')
