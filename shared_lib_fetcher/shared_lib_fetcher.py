#!/bin/python3
#
# Find and copy all dynamic library used by lib / executable
#

from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output


def linked_lib(binary: Path, excluded_lib: list[str] | None = None) -> list[Path]:
    """Get list of path to the dynamic library dependencies of a binary file.

    Args:
        binary: Path of executable or library file which the dependency list will be extracted from.
        excluded_lib: List of library name that will be excluded from output.

    Returns:
        List of path to the library dependencies.
    """
    if not binary.is_file():
        raise ValueError(f'Invalid file: {binary.absolute()}')

    # Read and verify output from ldd
    ldd_output = check_output(['ldd', binary]).decode()
    if 'not a dynamic executable' in ldd_output:
        raise ValueError('Not a dynamic executable.')
    if 'not found' in ldd_output:
        raise ValueError('Some dependencies are missing.')

    linked = [i.strip().rsplit(' (', 1)[0] for i in ldd_output.splitlines()]

    dep_list = []
    if excluded_lib == None:
        excluded_lib = []
    for link in linked:
        # Ignore virtual library linux-vdso.so
        #
        # ld-linux-x86-64.so.2 should always be included, but it is not always
        # an explicit dependency, so it might no have the => symbol
        if '=>' in link or link.endswith('/ld-linux-x86-64.so.2'):
            link_path = Path(link.rsplit(' => ', 1)[-1])
            if link_path.name in excluded_lib:
                continue
            dep_list.append(link_path)

    return dep_list


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('binary', help='Path to the executable or library.', type=Path)
    arg_parser.add_argument('copy_to', help='Path to where dynamic libraries will be copied to.', type=Path)
    arg_parser.add_argument(
        '-e',
        '--exclude',
        default='',
        type=str,
        help='Exclude matched library name. Each name should be separated by a comma (,).',
    )

    args = arg_parser.parse_args()

    excluded_lib: list[str] = args.exclude.split(',')

    # Check target path
    target_folder: Path = args.copy_to
    if not target_folder.is_dir():
        raise ValueError('Invalid target path.')

    dep_list = linked_lib(args.binary, excluded_lib)
    for lib in dep_list:
        lib.copy_into(target_folder, preserve_metadata=True)
